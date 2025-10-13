from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class Article(BaseModel):
    """Core article model for news feed system."""
    url: str
    urlHash: Optional[str] = None  # Auto-generated if not provided
    title: str
    summary: str
    source: str
    image: Optional[str] = None
    publishedAt: datetime
    # Simplified entities - just store as dict for flexibility
    entities: Dict[str, List[str]] = Field(default_factory=dict)  # {"tickers": [], "keywords": []}
    # Simplified quality - just store as dict for flexibility  
    quality: Dict[str, Any] = Field(default_factory=dict)  # {"llmScore": float, "reason": str}
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    
    @model_validator(mode='after')
    def generate_url_hash(self):
        """Auto-generate urlHash if not provided."""
        if not self.urlHash:
            from ..utils.hashing import url_hash
            self.urlHash = url_hash(self.url)
        return self
    
    def to_mongo_dict(self) -> dict:
        """Convert to MongoDB-ready dictionary."""
        data = self.model_dump()
        # Ensure datetime objects are properly serialized
        for field in ['publishedAt', 'createdAt', 'updatedAt']:
            if data.get(field) and hasattr(data[field], 'isoformat'):
                data[field] = data[field]
        return data
