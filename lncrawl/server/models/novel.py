from typing import Optional

from pydantic import BaseModel, Field

from ...dao import Chapter, Novel


class ReadChapterResponse(BaseModel):
    novel: Novel = Field(description="Novel details")
    chapter: Chapter = Field(description="Chapter details")
    content: Optional[str] = Field(description="Chapter content")
    next_id: Optional[str] = Field(description="Next chapter id")
    previous_id: Optional[str] = Field(description="Previous chapter id")
