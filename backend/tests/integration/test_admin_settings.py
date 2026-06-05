"""Integration tests for admin endpoints: settings, scraping, bulk import, audit log.

@spec API-060..065 (settings), API-070..075 (scrape/import), API-097 (audit)
"""

import io
import uuid

import pytest

# ── Settings CRUD ─────────────────────────────────────────


class TestSettingsEndpoints:
    """GET /admin/settings, PUT /admin/settings, GET /admin/settings/health."""

    @pytest.mark.spec("API-060")
    async def test_get_settings_as_admin(self, async_client, auth_headers_admin):
        resp = await async_client.get("/admin/settings", headers=auth_headers_admin)
        assert resp.status_code == 200
        body = resp.json()
        assert "settings" in body
        assert "groups" in body
        assert len(body["settings"]) > 0
        # Check a known setting is present
        keys = [s["key"] for s in body["settings"]]
        assert "APP_NAME" in keys
        assert "JWT_SECRET_KEY" in keys

    @pytest.mark.spec("API-060")
    async def test_settings_sensitive_values_masked(self, async_client, auth_headers_admin):
        resp = await async_client.get("/admin/settings", headers=auth_headers_admin)
        body = resp.json()
        sensitive = [s for s in body["settings"] if s["sensitive"]]
        assert len(sensitive) > 0, "No sensitive settings found"
        for s in sensitive:
            assert s["display_value"] == "••••••••••"

    @pytest.mark.spec("API-061")
    async def test_update_setting_as_admin(self, async_client, auth_headers_admin):
        resp = await async_client.put(
            "/admin/settings",
            headers=auth_headers_admin,
            json={"updates": {"OLLAMA_TIMEOUT": "120"}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "OLLAMA_TIMEOUT" in body["updated"]

    @pytest.mark.spec("API-061")
    async def test_update_non_editable_setting_rejected(self, async_client, auth_headers_admin):
        with pytest.raises(Exception):
            # Service raises ValueError for non-editable settings
            await async_client.put(
                "/admin/settings",
                headers=auth_headers_admin,
                json={"updates": {"APP_NAME": "Hacked"}},
            )

    @pytest.mark.spec("API-062")
    async def test_health_check(self, async_client, auth_headers_admin):
        resp = await async_client.get("/admin/settings/health", headers=auth_headers_admin)
        assert resp.status_code == 200
        body = resp.json()
        assert "postgres" in body
        assert "redis" in body
        assert "ollama" in body

    async def test_settings_forbidden_for_navigator(self, async_client, auth_headers_navigator):
        resp = await async_client.get("/admin/settings", headers=auth_headers_navigator)
        assert resp.status_code == 403

    async def test_settings_forbidden_unauthenticated(self, async_client):
        resp = await async_client.get("/admin/settings")
        assert resp.status_code == 401


# ── Data Import Endpoints ────────────────────────────────


class TestHospitalImport:
    """POST /admin/import/hospitals, POST /admin/import/hospitals/csv."""

    @pytest.mark.spec("API-070")
    async def test_bulk_import_hospitals_json(self, async_client, auth_headers_admin):
        hospitals = [
            {
                "name": f"Test Import Hospital {uuid.uuid4().hex[:8]}",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "address": "123 Test St",
                "phone": "9876543210",
            }
        ]
        resp = await async_client.post(
            "/admin/import/hospitals",
            headers=auth_headers_admin,
            json={"hospitals": hospitals},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["imported"] >= 1
        assert body["errors"] == []

    @pytest.mark.spec("API-070")
    async def test_bulk_import_duplicate_skipped(self, async_client, auth_headers_admin):
        name = f"Dupe Hospital {uuid.uuid4().hex[:8]}"
        hospital = {"name": name, "city": "Chennai"}
        # Import once
        await async_client.post(
            "/admin/import/hospitals",
            headers=auth_headers_admin,
            json={"hospitals": [hospital]},
        )
        # Import again — should skip duplicate
        resp = await async_client.post(
            "/admin/import/hospitals",
            headers=auth_headers_admin,
            json={"hospitals": [hospital]},
        )
        assert resp.status_code == 200
        assert resp.json()["skipped"] >= 1

    @pytest.mark.spec("API-071")
    async def test_import_hospitals_csv(self, async_client, auth_headers_admin):
        csv_data = (
            "name,city,state,phone\n"
            f"CSV Hospital {uuid.uuid4().hex[:8]},Madurai,Tamil Nadu,9876543210\n"
        ).encode()
        resp = await async_client.post(
            "/admin/import/hospitals/csv",
            headers=auth_headers_admin,
            files={"file": ("hospitals.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["imported"] >= 1

    async def test_import_hospitals_empty_csv(self, async_client, auth_headers_admin):
        csv_data = b"name,city\n"
        resp = await async_client.post(
            "/admin/import/hospitals/csv",
            headers=auth_headers_admin,
            files={"file": ("empty.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["imported"] == 0

    async def test_import_hospitals_missing_data(self, async_client, auth_headers_admin):
        resp = await async_client.post(
            "/admin/import/hospitals",
            headers=auth_headers_admin,
            json={"hospitals": []},
        )
        assert resp.status_code == 400

    async def test_import_forbidden_for_navigator(self, async_client, auth_headers_navigator):
        resp = await async_client.post(
            "/admin/import/hospitals",
            headers=auth_headers_navigator,
            json={"hospitals": [{"name": "X", "city": "Y"}]},
        )
        assert resp.status_code == 403


class TestNgoImport:
    """POST /admin/import/ngos/csv."""

    @pytest.mark.spec("API-072")
    async def test_import_ngos_csv(self, async_client, auth_headers_admin):
        csv_data = (
            "name,description,provider,max_amount\n"
            f"Test NGO {uuid.uuid4().hex[:8]},Helps patients,Trust,50000\n"
        ).encode()
        resp = await async_client.post(
            "/admin/import/ngos/csv",
            headers=auth_headers_admin,
            files={"file": ("ngos.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["imported"] >= 1

    async def test_import_ngos_empty_csv(self, async_client, auth_headers_admin):
        csv_data = b"name\n"
        resp = await async_client.post(
            "/admin/import/ngos/csv",
            headers=auth_headers_admin,
            files={"file": ("empty.csv", io.BytesIO(csv_data), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["imported"] == 0


# ── Scraper Endpoint ─────────────────────────────────────


class TestScrapeEndpoint:
    """POST /admin/scrape/hospitals — validates URL, returns preview."""

    async def test_scrape_missing_url(self, async_client, auth_headers_admin):
        resp = await async_client.post(
            "/admin/scrape/hospitals",
            headers=auth_headers_admin,
            json={"url": ""},
        )
        assert resp.status_code == 400

    async def test_scrape_invalid_domain(self, async_client, auth_headers_admin):
        resp = await async_client.post(
            "/admin/scrape/hospitals",
            headers=auth_headers_admin,
            json={"url": "https://example.com/hospitals"},
        )
        assert resp.status_code == 400
        assert "nic.in" in resp.json()["detail"]

    async def test_scrape_forbidden_for_clinician(self, async_client, auth_headers_clinician):
        resp = await async_client.post(
            "/admin/scrape/hospitals",
            headers=auth_headers_clinician,
            json={"url": "https://test.nic.in/"},
        )
        assert resp.status_code == 403


# ── Audit Log ────────────────────────────────────────────


class TestAuditLog:
    """GET /admin/audit-log — pagination, filtering, RBAC."""

    @pytest.mark.spec("API-097")
    async def test_list_audit_log(self, async_client, auth_headers_admin):
        resp = await async_client.get("/admin/audit-log", headers=auth_headers_admin)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body

    async def test_audit_log_pagination(self, async_client, auth_headers_admin):
        resp = await async_client.get(
            "/admin/audit-log?page=1&limit=5", headers=auth_headers_admin
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 5
        assert len(body["items"]) <= 5

    async def test_audit_log_action_filter(self, async_client, auth_headers_admin):
        resp = await async_client.get(
            "/admin/audit-log?action_filter=login", headers=auth_headers_admin
        )
        assert resp.status_code == 200

    async def test_audit_log_forbidden_for_patient(self, async_client, auth_headers_patient):
        resp = await async_client.get("/admin/audit-log", headers=auth_headers_patient)
        assert resp.status_code == 403
