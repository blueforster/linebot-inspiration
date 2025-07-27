import os
import tempfile
import hashlib
from typing import Optional, Union
from datetime import datetime, timedelta
import requests
from config.settings import Config

def is_valid_file_extension(filename: str, allowed_extensions: set) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def download_file(url: str, max_size: int = None) -> Optional[str]:
    try:
        max_size = max_size or Config.MAX_CONTENT_LENGTH
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check content length
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > max_size:
            return None
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        downloaded_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                downloaded_size += len(chunk)
                if downloaded_size > max_size:
                    temp_file.close()
                    os.unlink(temp_file.name)
                    return None
                temp_file.write(chunk)
        
        temp_file.close()
        return temp_file.name
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return None

def cleanup_temp_file(file_path: str) -> bool:
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            return True
        return False
    except Exception:
        return False

def generate_file_hash(file_path: str) -> Optional[str]:
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return None

def sanitize_text(text: str) -> str:
    if not text:
        return ""
    
    # Remove control characters
    cleaned = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
    
    # Limit length
    max_length = 10000
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "... (truncated)"
    
    return cleaned.strip()

def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    return dt.strftime(format_str)

def parse_datetime(dt_str: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    try:
        return datetime.strptime(dt_str, format_str)
    except ValueError:
        return None

def time_ago(dt: datetime) -> str:
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} days ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutes ago"
    else:
        return "Just now"

def chunk_text(text: str, chunk_size: int = 2000) -> list:
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            # Try to break at a sentence or word boundary
            last_period = text.rfind('.', start, end)
            last_space = text.rfind(' ', start, end)
            
            if last_period > start + chunk_size // 2:
                end = last_period + 1
            elif last_space > start + chunk_size // 2:
                end = last_space
        
        chunks.append(text[start:end].strip())
        start = end
    
    return chunks

def validate_user_id(user_id: str) -> bool:
    return bool(user_id and len(user_id.strip()) > 0)

def extract_keywords(text: str, min_length: int = 3) -> list:
    import re
    
    # Simple keyword extraction
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [word for word in words if len(word) >= min_length]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:10]  # Return top 10 keywords