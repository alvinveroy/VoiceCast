from pydantic import BaseModel, Field
from typing import Optional

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice: Optional[str] = None
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0)
    device_name: Optional[str] = None
