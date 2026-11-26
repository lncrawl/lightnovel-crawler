import json
import re
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator

from ...dao import LanguageCode, OutputFormat


class FetchNovelsRequest(BaseModel):
    urls: List[HttpUrl] = Field(
        description="List of novel URLs or text with newline-, comma-, or JSON-separated URLs"
    )
    full: bool = Field(default=False, description="To fetch all contents")

    @field_validator("urls", mode="before", json_schema_input_type=Union[List[HttpUrl], str])
    @classmethod
    def parse_urls(cls, value: Any) -> Any:
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
            value = value[0]
        if not isinstance(value, str):
            return value

        text = value.strip()
        if not text:
            return []
        if text.startswith(("[", "{")):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as error:
                raise ValueError("Enter valid JSON URLs") from error
            if isinstance(parsed, dict):
                parsed = parsed.get("urls")
            if not isinstance(parsed, list):
                raise ValueError("JSON input must be a URL array or an object with a urls array")
            return parsed

        urls = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            urls.extend(re.split(r",\s*(?=https?://)", line, flags=re.IGNORECASE))
        return [url.strip() for url in urls if url.strip()]


class FetchVolumesRequest(BaseModel):
    volumes: List[str] = Field(description="List of volume ids to fetch")


class FetchChaptersRequest(BaseModel):
    chapters: List[str] = Field(description="List of chapter ids to fetch")


class FetchImagesRequest(BaseModel):
    images: List[str] = Field(description="List of image ids to fetch")


class MakeArtifactsRequest(BaseModel):
    novel_id: str = Field(description="The novel id")
    formats: List[OutputFormat] = Field(description="List of formats")
    language: Optional[LanguageCode] = Field(default=None, description="Target language code")
    volume: Optional[int] = Field(
        default=None,
        description="Volume serial number to build a single-volume artifact; "
        "omit to build the whole novel",
    )


class TranslateNovelsRequest(BaseModel):
    novel_ids: List[str] = Field(description="List of novel ids to translate")
    language: LanguageCode = Field(description="Target language code")
    full: bool = Field(default=False, description="Also translate all volumes and chapters")


class TranslateVolumesRequest(BaseModel):
    volumes: List[str] = Field(description="List of volume ids to translate")
    language: LanguageCode = Field(description="Target language code")


class TranslateChaptersRequest(BaseModel):
    chapters: List[str] = Field(description="List of chapter ids to translate")
    language: LanguageCode = Field(description="Target language code")


class FetchMissingChaptersRequest(BaseModel):
    novel_id: str = Field(description="The novel id")


class FetchLatestRequest(BaseModel):
    novel_id: str = Field(description="The novel id")


class SearchSourceRequest(BaseModel):
    query: str = Field(description="Search query", min_length=2, max_length=50)
    domain: Optional[str] = Field(default=None, description="Search in a specific source only")
