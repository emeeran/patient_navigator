"""Database maintenance service — reset, backup, restore, repair, integrity check."""

import asyncio
import logging
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.database import Base, engine
from app.services.auth_service import write_audit_log

logger = logging.getLogger(__name__)


class DbMaintenanceService:
    """Admin database maintenance operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def reset_database(self, user_id: uuid.UUID) -> dict:
        """Drop all tables and recreate them. Returns count of recreated tables."""
        # Drop and recreate in a fresh connection
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            table_count_after = len(Base.metadata.tables)

        # Write audit log in a separate session since the caller's session
        # may be broken after its underlying tables were dropped and recreated.
        from app.core.database import async_session_factory

        async with async_session_factory() as audit_db:
            await write_audit_log(
                audit_db,
                action="database.reset",
                user_id=user_id,
                entity_type="database",
                description=f"Database reset: dropped and recreated {table_count_after} tables",
            )
            await audit_db.commit()

        return {
            "reset_tables": table_count_after,
            "message": f"Database reset complete. {table_count_after} tables recreated.",
        }

    async def backup_database(self) -> bytes:
        """Run pg_dump and return the SQL dump as bytes."""
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL_SYNC)
        env = {"PGPASSWORD": parsed.password or ""}

        cmd = [
            "pg_dump",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "navigator",
            "-d", (parsed.path or "/patient_nav").lstrip("/"),
            "--no-password",
            "--format=plain",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**_get_env(), **env},
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace").strip()
            logger.error("pg_dump failed: %s", error_msg)
            raise RuntimeError(f"Backup failed: {error_msg}")

        return stdout

    async def restore_database(self, user_id: uuid.UUID, file_bytes: bytes) -> dict:
        """Restore database from a SQL dump file using psql."""
        from urllib.parse import urlparse

        parsed = urlparse(settings.DATABASE_URL_SYNC)
        env = {"PGPASSWORD": parsed.password or ""}

        # Write dump to temp file (psql needs a file path or stdin)
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            cmd = [
                "psql",
                "-h", parsed.hostname or "localhost",
                "-p", str(parsed.port or 5432),
                "-U", parsed.username or "navigator",
                "-d", (parsed.path or "/patient_nav").lstrip("/"),
                "-f", tmp_path,
                "--no-password",
                "-q",
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**_get_env(), **env},
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace").strip()
                logger.error("psql restore failed: %s", error_msg)
                raise RuntimeError(f"Restore failed: {error_msg}")

            await write_audit_log(
                self.db,
                action="database.restore",
                user_id=user_id,
                entity_type="database",
                description="Database restored from backup file",
            )
            await self.db.flush()

            return {"message": "Database restored successfully."}
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    async def repair_database(self, user_id: uuid.UUID) -> dict:
        """Run REINDEX and VACUUM on all tables. Returns per-operation results."""
        results = []

        # REINDEX and VACUUM cannot run inside a transaction.
        # Use an autocommit-level engine for these operations.
        autocommit_engine = create_async_engine(
            settings.DATABASE_URL,
            isolation_level="AUTOCOMMIT",
            pool_size=1,
            max_overflow=0,
        )

        try:
            async with autocommit_engine.connect() as conn:
                # Reindex each table individually (avoids superuser requirement)
                for table_name in Base.metadata.tables:
                    try:
                        await conn.execute(text(f"REINDEX TABLE {table_name}"))
                        results.append({"operation": "REINDEX", "table": table_name, "status": "ok"})
                    except Exception as e:
                        results.append({"operation": "REINDEX", "table": table_name, "status": f"error: {e}"})

                # Vacuum analyze each table
                for table_name in Base.metadata.tables:
                    try:
                        await conn.execute(text(f"VACUUM ANALYZE {table_name}"))
                        results.append({"operation": "VACUUM ANALYZE", "table": table_name, "status": "ok"})
                    except Exception as e:
                        results.append({
                            "operation": "VACUUM ANALYZE",
                            "table": table_name,
                            "status": f"error: {e}",
                        })
        finally:
            await autocommit_engine.dispose()

        await write_audit_log(
            self.db,
            action="database.repair",
            user_id=user_id,
            entity_type="database",
            description=f"Database repair: {sum(1 for r in results if r['status'] == 'ok')}/{len(results)} operations succeeded",
        )
        await self.db.flush()

        ok_count = sum(1 for r in results if r["status"] == "ok")
        return {
            "results": results,
            "message": f"Repair complete: {ok_count}/{len(results)} operations succeeded.",
        }

    async def integrity_check(self) -> dict:
        """Check table integrity using pg_stat and row counts."""
        tables_info = []

        async with engine.begin() as conn:
            # Get all user tables
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
            table_names = [row[0] for row in result.fetchall()]

            for name in table_names:
                # Get row count estimate (fast)
                count_result = await conn.execute(text(
                    "SELECT reltuples::bigint AS estimate FROM pg_class WHERE relname = :name"
                ), {"name": name})
                row = count_result.fetchone()
                row_count = row[0] if row else 0

                # Check for dead tuples (indicator of needed vacuum)
                stat_result = await conn.execute(text(
                    "SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = :name"
                ), {"name": name})
                stat_row = stat_result.fetchone()
                dead_tuples = stat_row[0] if stat_row else 0

                status = "healthy"
                issues = []
                if dead_tuples and dead_tuples > 10000:
                    status = "needs_vacuum"
                    issues.append(f"{dead_tuples} dead tuples")

                tables_info.append({
                    "name": name,
                    "row_count": row_count,
                    "dead_tuples": dead_tuples or 0,
                    "status": status,
                    "issues": issues,
                })

        has_issues = any(t["status"] != "healthy" for t in tables_info)
        overall = "issues_found" if has_issues else "healthy"

        return {
            "tables": tables_info,
            "overall": overall,
        }


def _get_env() -> dict:
    """Get a clean environment dict for subprocess calls."""
    import os
    return dict(os.environ)
