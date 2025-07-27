import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, AudioMessage, ImageMessage,
    TextSendMessage, QuickReply, QuickReplyButton, MessageAction,
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent,
    ButtonComponent, URIAction
)
from config.settings import Config
from app.models.message_model import MessageModel
from app.services.sheets_service import SheetsService
from app.services.speech_service import SpeechService
from app.utils.helpers import sanitize_text, time_ago

class LineService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize LINE Bot API
        self.line_bot_api = LineBotApi(Config.LINE_CHANNEL_ACCESS_TOKEN)
        self.handler = WebhookHandler(Config.LINE_CHANNEL_SECRET)
        
        # Initialize services
        self.sheets_service = SheetsService()
        self.speech_service = SpeechService()
        
        # Setup event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_text_message(event):
            self._handle_text_message(event)
        
        @self.handler.add(MessageEvent, message=AudioMessage)
        def handle_audio_message(event):
            self._handle_audio_message(event)
        
        @self.handler.add(MessageEvent, message=ImageMessage)
        def handle_image_message(event):
            self._handle_image_message(event)
    
    def _handle_text_message(self, event):
        try:
            user_id = event.source.user_id
            text_content = event.message.text.strip()
            
            self.logger.info(f"Received text message from {user_id}: {text_content[:50]}...")
            
            # Check for commands
            if text_content.startswith('/'):
                self._handle_command(event, text_content)
                return
            
            # Create message model
            message = MessageModel(
                user_id=user_id,
                message_type='text',
                content=text_content,
                raw_data={'event_type': 'text_message'}
            )
            
            # Save to Google Sheets
            success = self.sheets_service.add_message(message)
            
            # Send confirmation
            if success:
                reply_text = "✅ 靈感已記錄！"
                if message.tags:
                    reply_text += f"\n🏷️ 標籤: {', '.join(message.tags)}"
                
                # Add quick reply buttons
                quick_reply = self._create_quick_reply_buttons()
                
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text, quick_reply=quick_reply)
                )
            else:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ 記錄失敗，請稍後再試")
                )
                
        except Exception as e:
            self.logger.error(f"Error handling text message: {e}")
            try:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ 處理訊息時發生錯誤")
                )
            except Exception:
                pass
    
    def _handle_audio_message(self, event):
        try:
            user_id = event.source.user_id
            message_id = event.message.id
            
            self.logger.info(f"Received audio message from {user_id}")
            
            # Get audio content URL
            message_content = self.line_bot_api.get_message_content(message_id)
            audio_url = message_content.url if hasattr(message_content, 'url') else None
            
            if not audio_url:
                # For LINE Bot, we need to download the content differently
                audio_url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
            
            # Send processing message
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="🎵 正在處理語音訊息...")
            )
            
            # Convert speech to text
            speech_result = self.speech_service.convert_audio_to_text(audio_url)
            
            if speech_result and speech_result.get('transcript'):
                transcript = speech_result['transcript']
                confidence = speech_result.get('confidence', 0)
                
                # Create message model
                message = MessageModel(
                    user_id=user_id,
                    message_type='audio',
                    content=transcript,
                    raw_data={
                        'event_type': 'audio_message',
                        'speech_confidence': confidence,
                        'speech_service': speech_result.get('service', 'unknown')
                    }
                )
                
                # Save to Google Sheets
                success = self.sheets_service.add_message(message)
                
                if success:
                    reply_text = f"🎵 語音已轉換並記錄！\n\n📝 內容: {transcript}"
                    if confidence > 0:
                        reply_text += f"\n🎯 準確度: {confidence:.2%}"
                    if message.tags:
                        reply_text += f"\n🏷️ 標籤: {', '.join(message.tags)}"
                    
                    # Add quick reply buttons
                    quick_reply = self._create_quick_reply_buttons()
                    
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=reply_text, quick_reply=quick_reply)
                    )
                else:
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text="❌ 語音轉換成功但記錄失敗")
                    )
            else:
                self.line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text="❌ 語音轉換失敗，請重新發送或改用文字")
                )
                
        except Exception as e:
            self.logger.error(f"Error handling audio message: {e}")
            try:
                self.line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text="❌ 處理語音訊息時發生錯誤")
                )
            except Exception:
                pass
    
    def _handle_image_message(self, event):
        try:
            user_id = event.source.user_id
            
            self.logger.info(f"Received image message from {user_id}")
            
            # Create message model for image
            message = MessageModel(
                user_id=user_id,
                message_type='image',
                content='[圖片訊息]',
                raw_data={'event_type': 'image_message'}
            )
            
            # Save to Google Sheets
            success = self.sheets_service.add_message(message)
            
            if success:
                reply_text = "🖼️ 圖片已記錄！"
                quick_reply = self._create_quick_reply_buttons()
                
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text, quick_reply=quick_reply)
                )
            else:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ 圖片記錄失敗")
                )
                
        except Exception as e:
            self.logger.error(f"Error handling image message: {e}")
            try:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ 處理圖片時發生錯誤")
                )
            except Exception:
                pass
    
    def _handle_command(self, event, command_text):
        user_id = event.source.user_id
        command = command_text.lower().strip()
        
        try:
            if command == '/today' or command == '/今日':
                self._send_today_summary(event, user_id)
            elif command == '/stats' or command == '/統計':
                self._send_user_statistics(event, user_id)
            elif command == '/tags' or command == '/標籤':
                self._send_tags_summary(event, user_id)
            elif command.startswith('/search ') or command.startswith('/搜尋 '):
                query = command_text[8:].strip() if command.startswith('/search ') else command_text[4:].strip()
                self._send_search_results(event, user_id, query)
            elif command == '/help' or command == '/幫助':
                self._send_help_message(event)
            else:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❓ 未知指令，輸入 /help 查看可用指令")
                )
                
        except Exception as e:
            self.logger.error(f"Error handling command {command}: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 指令執行失敗")
            )
    
    def _send_today_summary(self, event, user_id):
        try:
            recent_messages = self.sheets_service.get_recent_messages(user_id, days=1)
            
            if not recent_messages:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="📅 今日還沒有記錄任何靈感")
                )
                return
            
            summary_text = f"📅 今日靈感記錄 ({len(recent_messages)} 筆)\n\n"
            
            for i, msg in enumerate(recent_messages[:5], 1):
                content = msg.get('content', '')[:50]
                if len(msg.get('content', '')) > 50:
                    content += "..."
                
                msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                time_str = msg_time.strftime('%H:%M')
                
                summary_text += f"{i}. [{time_str}] {content}\n"
            
            if len(recent_messages) > 5:
                summary_text += f"\n... 還有 {len(recent_messages) - 5} 筆記錄"
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=summary_text)
            )
            
        except Exception as e:
            self.logger.error(f"Error sending today summary: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 無法取得今日記錄")
            )
    
    def _send_user_statistics(self, event, user_id):
        try:
            stats = self.sheets_service.get_user_statistics(user_id)
            
            if not stats or stats.get('total_messages', 0) == 0:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="📊 還沒有任何記錄")
                )
                return
            
            stats_text = f"📊 您的靈感統計\n\n"
            stats_text += f"📝 總記錄數: {stats['total_messages']}\n"
            stats_text += f"🏷️ 標籤數量: {stats['tags_count']}\n"
            
            if stats['message_types']:
                stats_text += f"\n📊 訊息類型:\n"
                for msg_type, count in stats['message_types'].items():
                    stats_text += f"  • {msg_type}: {count}\n"
            
            if stats['first_message']:
                stats_text += f"\n📅 首次記錄: {stats['first_message']}"
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=stats_text)
            )
            
        except Exception as e:
            self.logger.error(f"Error sending user statistics: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 無法取得統計資料")
            )
    
    def _send_tags_summary(self, event, user_id):
        try:
            tags_stats = self.sheets_service.get_tags_statistics(user_id)
            
            if not tags_stats:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="🏷️ 還沒有任何標籤")
                )
                return
            
            tags_text = f"🏷️ 您的標籤統計 (共 {len(tags_stats)} 個)\n\n"
            
            for i, (tag, count) in enumerate(list(tags_stats.items())[:10], 1):
                tags_text += f"{i}. #{tag}: {count} 次\n"
            
            if len(tags_stats) > 10:
                tags_text += f"\n... 還有 {len(tags_stats) - 10} 個標籤"
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=tags_text)
            )
            
        except Exception as e:
            self.logger.error(f"Error sending tags summary: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 無法取得標籤資料")
            )
    
    def _send_search_results(self, event, user_id, query):
        try:
            if not query:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="🔍 請提供搜尋關鍵字")
                )
                return
            
            results = self.sheets_service.search_messages(query, user_id)
            
            if not results:
                self.line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"🔍 沒有找到包含 '{query}' 的記錄")
                )
                return
            
            search_text = f"🔍 搜尋結果: '{query}' (共 {len(results)} 筆)\n\n"
            
            for i, result in enumerate(results[:5], 1):
                content = result.get('content', '')[:50]
                if len(result.get('content', '')) > 50:
                    content += "..."
                
                msg_time = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00'))
                time_str = msg_time.strftime('%m/%d %H:%M')
                
                search_text += f"{i}. [{time_str}] {content}\n"
            
            if len(results) > 5:
                search_text += f"\n... 還有 {len(results) - 5} 筆相符記錄"
            
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=search_text)
            )
            
        except Exception as e:
            self.logger.error(f"Error sending search results: {e}")
            self.line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="❌ 搜尋失敗")
            )
    
    def _send_help_message(self, event):
        help_text = """
🤖 靈感筆記機器人使用說明

📝 基本功能:
• 傳送文字 → 自動記錄靈感
• 傳送語音 → 轉文字後記錄
• 傳送圖片 → 記錄圖片訊息
• 使用 #標籤 來分類您的靈感

🔧 指令功能:
• /today 或 /今日 → 查看今日記錄
• /stats 或 /統計 → 查看統計資料  
• /tags 或 /標籤 → 查看標籤統計
• /search 關鍵字 → 搜尋記錄
• /help 或 /幫助 → 顯示此說明

💡 小技巧:
在訊息中加入 #工作 #想法 等標籤來分類您的靈感！
        """.strip()
        
        self.line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=help_text)
        )
    
    def _create_quick_reply_buttons(self):
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="📅 今日記錄", text="/今日")),
            QuickReplyButton(action=MessageAction(label="📊 統計", text="/統計")),
            QuickReplyButton(action=MessageAction(label="🏷️ 標籤", text="/標籤")),
            QuickReplyButton(action=MessageAction(label="❓ 幫助", text="/幫助"))
        ])
    
    def handle_webhook(self, body: str, signature: str):
        try:
            self.handler.handle(body, signature)
            return True
        except InvalidSignatureError:
            self.logger.error("Invalid signature")
            return False
        except Exception as e:
            self.logger.error(f"Webhook handling error: {e}")
            return False