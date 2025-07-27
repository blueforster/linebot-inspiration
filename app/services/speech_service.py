import os
import tempfile
import logging
from typing import Optional, Dict, Any
from pydub import AudioSegment
import requests
from config.settings import Config
from app.utils.helpers import download_file, cleanup_temp_file, is_valid_file_extension

try:
    from google.cloud import speech
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    logging.warning("Google Cloud Speech not available. Install google-cloud-speech for advanced speech recognition.")

class SpeechService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.google_client = None
        
        if GOOGLE_SPEECH_AVAILABLE and Config.GOOGLE_CLOUD_PROJECT:
            try:
                self.google_client = speech.SpeechClient()
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
        try:
            # Load audio file
            audio = AudioSegment.from_file(input_file)
            
            # Convert to WAV format with specific settings for speech recognition
            audio = audio.set_frame_rate(16000)  # 16kHz sample rate
            audio = audio.set_channels(1)       # Mono
            audio = audio.set_sample_width(2)   # 16-bit
            
            # Create temporary WAV file
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_wav.close()
            
            # Export to WAV
            audio.export(temp_wav.name, format="wav")
            
            self.logger.debug(f"Audio converted to WAV: {temp_wav.name}")
            return temp_wav.name
            
        except Exception as e:
            self.logger.error(f"Failed to convert audio format: {e}")
            return None
    
    def _google_speech_to_text(self, audio_file: str, language_code: str) -> Optional[Dict[str, Any]]:
        try:
            # Read audio file
            with open(audio_file, 'rb') as f:
                audio_content = f.read()
            
            # Configure audio settings
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
                alternative_language_codes=Config.SPEECH_ALTERNATIVE_LANGUAGE_CODES,
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                model='default'
            )
            
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
        try:
            # Get audio duration and basic info
            audio = AudioSegment.from_file(audio_file)
            duration = len(audio) / 1000.0  # Duration in seconds
            
            # Simple fallback - return metadata
            return {
                'transcript': '[語音訊息已接收，但無法轉換為文字]',
                'confidence': 0.0,
                'language': 'unknown',
                'service': 'fallback',
                'duration': duration,
                'alternatives': []
            }
            
        except Exception as e:
            self.logger.error(f"Fallback processing error: {e}")
            return {
                'transcript': '[語音訊息處理失敗]',
                'confidence': 0.0,
                'language': 'unknown',
                'service': 'error',
                'alternatives': []
            }
    
    def process_long_audio(self, audio_url: str, language_code: str = None) -> Optional[Dict[str, Any]]:
        temp_file = None
        
        try:
            # Download and check audio duration
            temp_file = download_file(audio_url)
            if not temp_file:
                return None
            
            audio = AudioSegment.from_file(temp_file)
            duration = len(audio) / 1000.0  # Duration in seconds
            
            # If audio is longer than 60 seconds, split it
            if duration > 60:
                return self._process_long_audio_chunks(temp_file, language_code)
            else:
                return self.convert_audio_to_text(audio_url, language_code)
                
        except Exception as e:
            self.logger.error(f"Error processing long audio: {e}")
            return None
            
        finally:
            if temp_file:
                cleanup_temp_file(temp_file)
    
    def _process_long_audio_chunks(self, audio_file: str, language_code: str) -> Dict[str, Any]:
        try:
            audio = AudioSegment.from_file(audio_file)
            chunk_length = 30 * 1000  # 30 seconds chunks
            
            transcripts = []
            total_confidence = 0
            chunk_count = 0
            
            # Process audio in chunks
            for i in range(0, len(audio), chunk_length):
                chunk = audio[i:i + chunk_length]
                
                # Save chunk to temporary file
                chunk_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                chunk_file.close()
                
                try:
                    chunk.export(chunk_file.name, format="wav")
                    
                    # Process chunk
                    if self.google_client:
                        result = self._google_speech_to_text(chunk_file.name, language_code)
                        if result and result['transcript']:
                            transcripts.append(result['transcript'])
                            total_confidence += result['confidence']
                            chunk_count += 1
                    
                finally:
                    cleanup_temp_file(chunk_file.name)
            
            # Combine results
            combined_transcript = ' '.join(transcripts)
            average_confidence = total_confidence / chunk_count if chunk_count > 0 else 0
            
            return {
                'transcript': combined_transcript,
                'confidence': average_confidence,
                'language': language_code or Config.SPEECH_LANGUAGE_CODE,
                'service': 'google_cloud_speech_chunked',
                'chunk_count': chunk_count,
                'alternatives': []
            }
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunks: {e}")
            return self._fallback_speech_processing(audio_file)
    
    def is_supported_audio_format(self, filename: str) -> bool:
        return is_valid_file_extension(filename, Config.ALLOWED_AUDIO_EXTENSIONS)
    
    def get_audio_info(self, audio_file: str) -> Dict[str, Any]:
        try:
            audio = AudioSegment.from_file(audio_file)
            
            return {
                'duration': len(audio) / 1000.0,
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'format': 'detected'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audio info: {e}")
            return {}