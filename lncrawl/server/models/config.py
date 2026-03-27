from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ConfigProperty(BaseModel):
    key: str = Field(
        description="Property name on the section object",
    )
    display_name: str = Field(
        description="Short label from the property docstring",
    )
    description: str = Field(
        description="Longer help text from the property docstring",
    )
    value_kind: str = Field(
        description="Logical type: string, integer, boolean, path, or any",
    )
    value: Optional[Any] = Field(
        default=None,
        description="Current value when included in the response",
    )
    sensitive: bool = Field(
        default=False,
        description="Whether the property is sensitive and masked in the response",
    )


class ConfigSection(BaseModel):
    key: str = Field(description="Config section key")
    display_name: str = Field(description="Short label from the section docstring")
    description: str = Field(description="Longer help text from the section docstring")
    properties: List[ConfigProperty] = Field(description="List of config properties")


class ConfigUpdateRequest(BaseModel):
    section: str = Field(description="Config section id (e.g. server, database)")
    key: str = Field(description="Property name on the section object")
    value: Any = Field(description="New value to set")
