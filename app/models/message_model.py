from datetime import datetime
from typing import Optional, Dict, Any
import re

class MessageModel:
    def __init__(self, 
                 user_id: str, 
                 message_type: str, 
                 content: str, 
                 timestamp: Optional[datetime] = None,
                 raw_data: Optional[Dict[Any, Any]] = None):
        self.user_id = user_id
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.raw_data = raw_data or {}
        self.tags = self._extract_tags()
        self.processed_content = self._process_content()
    
    def _extract_tags(self) -> list:
        tag_pattern = r'#(\w+)'
        tags = re.findall(tag_pattern, self.content)
        return list(set(tags))
    
    def _process_content(self) -> str:
        content = self.content.strip()
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Basic content cleaning
        content = content.replace('\n', ' ').replace('\r', '')
        
        return content
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'message_type': self.message_type,
            'content': self.content,
            'processed_content': self.processed_content,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'raw_data': self.raw_data
        }
    
    def to_sheets_row(self) -> list:
        return [
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            self.message_type,
            self.processed_content,
            self.user_id,
            ', '.join(self.tags) if self.tags else '',
            'processed'
        ]
    
    @staticmethod
    def get_sheets_headers() -> list:
        return [
            'timestamp',
            'message_type', 
            'content',
            'user_id',
            'tags',
            'status'
        ]
    
    def is_valid(self) -> bool:
        return (
            bool(self.user_id) and 
            bool(self.message_type) and 
            bool(self.content.strip())
        )
    
    def get_summary(self) -> str:
        content_preview = self.processed_content[:50]
        if len(self.processed_content) > 50:
            content_preview += "..."
        
        return f"{self.message_type}: {content_preview}"