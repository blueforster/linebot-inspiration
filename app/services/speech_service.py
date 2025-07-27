import os
import tempfile
import logging
from typing import Optional, Dict, Any
# from pydub import AudioSegment  # 暫時停用音訊處理
import requests
from config.settings import Config
from app.utils.helpers import download_file, cleanup_temp_file, is_valid_file_extension

# 暫時停用 Google Cloud Speech，使用基本功能
GOOGLE_SPEECH_AVAILABLE = False

class SpeechService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.google_client = None
        
        if GOOGLE_SPEECH_AVAILABLE and Config.GOOGLE_CLOUD_PROJECT:
            try:
                # from google.cloud import speech  # 只在需要時匯入
                # self.google_client = speech.SpeechClient()
                self.logger.info("Google Cloud Speech client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Google Cloud Speech client: {e}")
    
    def convert_audio_to_text(self, audio_url: str, language_code: str = None) -> Optional[Dict[str, Any]]:
        temp_file = None
        converted_file = None
        
        try:
            # Set default language
            language_code = language_code or Config.SPEECH_LANGUAGE_CODE
            
            # Download audio file
            temp_file = download_file(audio_url)
            if not temp_file:
                self.logger.error("Failed to download audio file")
                return None
            
            # Convert audio to supported format
            converted_file = self._convert_audio_format(temp_file)
            if not converted_file:
                self.logger.error("Failed to convert audio format")
                return None
            
            # Attempt Google Cloud Speech recognition
            if self.google_client:
                result = self._google_speech_to_text(converted_file, language_code)
                if result:
                    return result
            
            # Fallback: Simple audio processing
            return self._fallback_speech_processing(converted_file)
            
        except Exception as e:
            self.logger.error(f"Error in speech to text conversion: {e}")
            return None
            
        finally:
            # Cleanup temporary files
            if temp_file:
                cleanup_temp_file(temp_file)
            if converted_file and converted_file != temp_file:
                cleanup_temp_file(converted_file)
    
    def _convert_audio_format(self, input_file: str) -> Optional[str]:
        # 暫時返回原始檔案，不進行格式轉換
        return input_file
    
    def _google_speech_to_text(self, audio_file: str, language_code: str) -> Optional[Dict[str, Any]]:
        try:
            # 暫時停用，直接返回備援結果
            return self._fallback_speech_processing(audio_file)
            
            # 以下程式碼在啟用 Google Cloud Speech 時使用
            """
            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_content = f.read()
            
            # Configure audio settings  
            from google.cloud import speech
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                alternative_language_codes=Config.SPEECH_ALTERNATIVE_LANGUAGE_CODES,
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                model='default'
            )"""
            
            # Perform speech recognition
            response = self.google_client.recognize(config=config, audio=audio)
            
            if not response.results:
                self.logger.warning("No speech recognition results")
                return {
                    'transcript': '',
                    'confidence': 0.0,
                    'language': language_code,
                    'service': 'google_cloud_speech',
                    'alternatives': []
                }
            
            # Get best result
            result = response.results[0]
            alternative = result.alternatives[0]
            
            # Extract alternatives
            alternatives = []
            for alt in result.alternatives[:3]:  # Top 3 alternatives
                alternatives.append({
                    'transcript': alt.transcript,
                    'confidence': alt.confidence
                })
            
            return {
                'transcript': alternative.transcript,
                'confidence': alternative.confidence,
                'language': language_code,
                'service': 'google_cloud_speech',
                'alternatives': alternatives
            }
            
        except Exception as e:
            self.logger.error(f"Google Speech API error: {e}")
            return None
    
    def _fallback_speech_processing(self, audio_file: str) -> Dict[str, Any]:
        # 簡化的備援處理
        return {
            'transcript': '[語音訊息已接收，但無法轉換為文字]',
            'confidence': 0.0,
            'language': 'unknown',
            'service': 'fallback',
            'alternatives': []
        }
    
    def process_long_audio(self, audio_url: str, language_code: str = None) -> Optional[Dict[str, Any]]:
        # 暫時停用長音訊處理，直接使用基本處理
        return self.convert_audio_to_text(audio_url, language_code)
    
    def _process_long_audio_chunks(self, audio_file: str, language_code: str) -> Dict[str, Any]:
        # 暫時停用分塊處理，直接返回備援結果
        return self._fallback_speech_processing(audio_file)
    
    def is_supported_audio_format(self, filename: str) -> bool:
        return is_valid_file_extension(filename, Config.ALLOWED_AUDIO_EXTENSIONS)
    
    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        # 暫時停用音訊資訊獲取
        return {
            'duration': 0.0,
            'channels': 1,
            'frame_rate': 16000,
            'sample_width': 2,
            'format': 'unknown'
        }