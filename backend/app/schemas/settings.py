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


class ServiceHealthResponse(BaseModel):
    postgres: str
    redis: str
    ollama: str
    ollama_models: list[str] | None = None
