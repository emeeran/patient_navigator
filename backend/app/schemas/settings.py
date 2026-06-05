"""Pydantic schemas for system settings endpoints."""

from pydantic import BaseModel


class SettingItem(BaseModel):
    key: str
    value: str
    display_value: str
    type: str  # "str", "int", "bool"
    group_name: str
    editable: bool
    sensitive: bool
    source: str  # "database" or "default"


class SettingsResponse(BaseModel):
    settings: list[SettingItem]
    groups: dict[str, str]  # group key -> display name


class SettingsUpdateRequest(BaseModel):
    updates: dict[str, str]


class SettingsUpdateResponse(BaseModel):
    updated: list[str]
    message: str = "Settings updated successfully"


class DatabaseResetResponse(BaseModel):
    reset_tables: int
    message: str


class DatabaseRepairResult(BaseModel):
    operation: str
    table: str
    status: str


class DatabaseRepairResponse(BaseModel):
    results: list[DatabaseRepairResult]
    message: str


class DatabaseIntegrityTable(BaseModel):
    name: str
    row_count: int
    dead_tuples: int
    status: str
    issues: list[str]


class DatabaseIntegrityResponse(BaseModel):
    tables: list[DatabaseIntegrityTable]
    overall: str


class DatabaseRestoreResponse(BaseModel):
    message: str


class ServiceHealthResponse(BaseModel):
    postgres: str
    redis: str
    ollama: str
    ollama_models: list[str] | None = None
