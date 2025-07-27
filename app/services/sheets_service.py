import gspread
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import pandas as pd
from config.settings import Config
from app.models.message_model import MessageModel
from app.utils.helpers import sanitize_text
import json
import os

class SheetsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.sheet = None
        self.worksheet = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            credentials = None
            
            # 優先使用環境變數中的 JSON 憑證（更安全）
            if Config.GOOGLE_SERVICE_ACCOUNT_JSON:
                try:
                    cred_dict = json.loads(Config.GOOGLE_SERVICE_ACCOUNT_JSON)
                    credentials = Credentials.from_service_account_info(
                        cred_dict,
                        scopes=[
                            'https://www.googleapis.com/auth/spreadsheets',
                            'https://www.googleapis.com/auth/drive'
                        ]
                    )
                    self.logger.info("Google credentials loaded from environment variable")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON: {e}")
            
            # 備選：使用檔案路徑
            elif os.path.exists(Config.GOOGLE_SERVICE_ACCOUNT_KEY_PATH):
                credentials = Credentials.from_service_account_file(
                    Config.GOOGLE_SERVICE_ACCOUNT_KEY_PATH,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                self.logger.info("Google credentials loaded from file")
            
            if credentials:
                self.client = gspread.authorize(credentials)
                self.logger.info("Google Sheets client initialized successfully")
                
                # Open the spreadsheet
                self._open_spreadsheet()
            else:
                self.logger.error("No valid Google credentials found")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Sheets client: {e}")
    
    def _open_spreadsheet(self):
        try:
            self.sheet = self.client.open_by_key(Config.GOOGLE_SHEET_ID)
            
            # Get or create main worksheet
            try:
                self.worksheet = self.sheet.worksheet("Inspiration_Notes")
            except gspread.WorksheetNotFound:
                self.worksheet = self.sheet.add_worksheet(
                    title="Inspiration_Notes", 
                    rows=1000, 
                    cols=10
                )
                self._setup_headers()
            
            self.logger.info("Spreadsheet opened successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to open spreadsheet: {e}")
    
    def _setup_headers(self):
        try:
            headers = MessageModel.get_sheets_headers()
            self.worksheet.insert_row(headers, 1)
            
            # Format headers
            self.worksheet.format("A1:F1", {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "textFormat": {"bold": True}
            })
            
            self.logger.info("Headers set up successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup headers: {e}")
    
    def add_message(self, message: MessageModel) -> bool:
        try:
            if not self.worksheet:
                self.logger.error("Worksheet not initialized")
                return False
            
            if not message.is_valid():
                self.logger.error("Invalid message data")
                return False
            
            # Sanitize content
            sanitized_content = sanitize_text(message.content)
            message.content = sanitized_content
            message.processed_content = sanitize_text(message.processed_content)
            
            # Prepare row data
            row_data = message.to_sheets_row()
            
            # Insert row
            self.worksheet.insert_row(row_data, 2)  # Insert at row 2 (after headers)
            
            self.logger.info(f"Message added to sheet: {message.get_summary()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add message to sheet: {e}")
            return False
    
    def add_messages_batch(self, messages: List[MessageModel]) -> int:
        try:
            if not messages:
                return 0
            
            valid_messages = [msg for msg in messages if msg.is_valid()]
            if not valid_messages:
                return 0
            
            # Prepare batch data
            rows_data = []
            for message in valid_messages:
                sanitized_content = sanitize_text(message.content)
                message.content = sanitized_content
                message.processed_content = sanitize_text(message.processed_content)
                rows_data.append(message.to_sheets_row())
            
            # Insert batch
            if rows_data:
                self.worksheet.insert_rows(rows_data, 2)
                self.logger.info(f"Added {len(rows_data)} messages to sheet")
                return len(rows_data)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to add messages batch: {e}")
            return 0
    
    def get_recent_messages(self, user_id: Optional[str] = None, days: int = 7) -> List[Dict]:
        try:
            if not self.worksheet:
                return []
            
            # Get all data
            all_data = self.worksheet.get_all_records()
            
            if not all_data:
                return []
            
            # Convert to DataFrame for easier filtering
            df = pd.DataFrame(all_data)
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[df['timestamp'] >= cutoff_date]
            
            # Filter by user if specified
            if user_id:
                df = df[df['user_id'] == user_id]
            
            # Sort by timestamp (newest first)
            df = df.sort_values('timestamp', ascending=False)
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Failed to get recent messages: {e}")
            return []
    
    def search_messages(self, query: str, user_id: Optional[str] = None) -> List[Dict]:
        try:
            if not self.worksheet or not query.strip():
                return []
            
            all_data = self.worksheet.get_all_records()
            if not all_data:
                return []
            
            df = pd.DataFrame(all_data)
            
            # Filter by user if specified
            if user_id:
                df = df[df['user_id'] == user_id]
            
            # Search in content (case-insensitive)
            query_lower = query.lower()
            mask = df['content'].str.lower().str.contains(query_lower, na=False)
            
            # Also search in tags
            tag_mask = df['tags'].str.lower().str.contains(query_lower, na=False)
            
            # Combine masks
            combined_mask = mask | tag_mask
            result_df = df[combined_mask]
            
            # Sort by timestamp (newest first)
            result_df = result_df.sort_values('timestamp', ascending=False)
            
            return result_df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Failed to search messages: {e}")
            return []
    
    def get_tags_statistics(self, user_id: Optional[str] = None) -> Dict[str, int]:
        try:
            if not self.worksheet:
                return {}
            
            all_data = self.worksheet.get_all_records()
            if not all_data:
                return {}
            
            df = pd.DataFrame(all_data)
            
            # Filter by user if specified
            if user_id:
                df = df[df['user_id'] == user_id]
            
            # Count tags
            tag_counts = {}
            for tags_str in df['tags'].dropna():
                if tags_str.strip():
                    tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                    for tag in tags:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            
            # Sort by count
            sorted_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))
            
            return sorted_tags
            
        except Exception as e:
            self.logger.error(f"Failed to get tags statistics: {e}")
            return {}
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        try:
            if not self.worksheet:
                return {}
            
            all_data = self.worksheet.get_all_records()
            if not all_data:
                return {}
            
            df = pd.DataFrame(all_data)
            user_data = df[df['user_id'] == user_id]
            
            if user_data.empty:
                return {
                    'total_messages': 0,
                    'message_types': {},
                    'tags_count': 0,
                    'first_message': None,
                    'last_message': None
                }
            
            # Convert timestamp to datetime
            user_data['timestamp'] = pd.to_datetime(user_data['timestamp'])
            
            # Calculate statistics
            stats = {
                'total_messages': len(user_data),
                'message_types': user_data['message_type'].value_counts().to_dict(),
                'tags_count': len(self.get_tags_statistics(user_id)),
                'first_message': user_data['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'last_message': user_data['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get user statistics: {e}")
            return {}
    
    def backup_data(self, backup_path: str) -> bool:
        try:
            if not self.worksheet:
                return False
            
            all_data = self.worksheet.get_all_records()
            
            # Save as JSON
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"Data backed up to {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to backup data: {e}")
            return False
    
    def is_healthy(self) -> bool:
        try:
            return (
                self.client is not None and 
                self.sheet is not None and 
                self.worksheet is not None
            )
        except Exception:
            return False