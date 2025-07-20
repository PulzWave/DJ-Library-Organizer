"""Audio processing and analysis functionality."""

import io
import os
import random
import numpy as np
import librosa
import pygame
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, ID3NoHeaderError

from ..config import CUSTOM_ID3_VALUE, RATING_TXXX_DESC
from ..utils.settings_manager import SettingsManager
from ..utils.logger import get_logger

logger = get_logger()

# Initialize settings manager
settings_manager = SettingsManager()
settings_manager.load_settings()


class AudioProcessor:
    """Handles audio file processing, analysis, and playback."""
    
    def __init__(self):
        """Initialize the audio processor."""
        pygame.mixer.init()
        
    def analyze_audio_file(self, filepath):
        """
        Analyze an audio file and extract waveform data and metadata.
        
        Args:
            filepath (str): Path to the audio file
            
        Returns:
            dict: Dictionary containing analysis results
        """
        try:
            with open(filepath, 'rb') as f:
                audio_data_bytes = f.read()
            
            # Load audio for analysis
            y, sr = librosa.load(io.BytesIO(audio_data_bytes), sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Generate waveform visualization data
            waveform_lines = self._generate_waveform_lines(y, sr)
            
            # Extract metadata
            metadata = self._extract_metadata(io.BytesIO(audio_data_bytes))
            
            return {
                'filepath': filepath,
                'audio_data': audio_data_bytes,
                'duration': duration,
                'waveform_lines': waveform_lines,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Worker failed to analyze {os.path.basename(filepath)}: {e}")
            raise
    
    def _generate_waveform_lines(self, y, sr, canvas_width=1160, canvas_height=400):
        """
        Generate waveform visualization data from audio.
        
        Args:
            y: Audio time series
            sr: Sample rate
            canvas_width: Width of the canvas
            canvas_height: Height of the canvas
            
        Returns:
            list: List of waveform line data
        """
        N_FFT, HOP_LENGTH = 2048, 512
        stft = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
        stft_db = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
        freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
        
        time_points = np.linspace(0, stft_db.shape[1] - 1, num=canvas_width, dtype=int)
        
        # Frequency band masks
        bass_mask = (freqs >= 20) & (freqs < 500)
        mid_mask = (freqs >= 500) & (freqs < 2000)
        high_mask = (freqs >= 2000) & (freqs <= 20000)
        
        waveform_lines = []
        center_y = canvas_height / 2
        
        def scale_energy(energy):
            return max(0, (energy + 80) / 80) * (canvas_height / 2.2)
        
        for i, t in enumerate(time_points):
            if t >= stft_db.shape[1]:
                continue
                
            frame = stft_db[:, t]
            
            # Calculate energy for each frequency band
            bass_h = scale_energy(np.mean(frame[bass_mask]) if np.any(bass_mask) else -80.0)
            mid_h = scale_energy(np.mean(frame[mid_mask]) if np.any(mid_mask) else -80.0)
            high_h = scale_energy(np.mean(frame[high_mask]) if np.any(high_mask) else -80.0)
            
            # Create line data for each frequency band
            waveform_lines.append({
                'coords': (i, center_y - bass_h, i, center_y + bass_h),
                'options': {'fill': '#0096FF', 'width': 1}
            })
            waveform_lines.append({
                'coords': (i, center_y - mid_h, i, center_y + mid_h),
                'options': {'fill': '#4CBB17', 'width': 1}
            })
            waveform_lines.append({
                'coords': (i, center_y - high_h, i, center_y + high_h),
                'options': {'fill': 'white', 'width': 1}
            })
            
        return waveform_lines
    
    def _extract_metadata(self, audio_bytes):
        """
        Extract metadata from audio file bytes.
        
        Args:
            audio_bytes: BytesIO object containing audio data
            
        Returns:
            dict: Extracted metadata
        """
        metadata = {}
        
        try:
            audio_tags = MP3(audio_bytes, ID3=ID3)
            
            # Get POPM email from settings
            popm_email = settings_manager.get("POPM_EMAIL", "changeme@pulzwave.com")
            
            # Extract rating from POPM or TXXX:RATING
            rating_val = None
            if f'POPM:{popm_email}' in audio_tags:
                rating_val = int(audio_tags[f'POPM:{popm_email}'].rating * 5 / 255)
            elif f'TXXX:{RATING_TXXX_DESC}' in audio_tags:
                try:
                    rating_val = int(str(audio_tags[f'TXXX:{RATING_TXXX_DESC}']))
                except Exception:
                    pass
            
            if rating_val is not None:
                metadata['rating'] = rating_val
            
            # Extract other metadata
            if 'TCON' in audio_tags:
                metadata['genre'] = audio_tags['TCON'].text[0]
            
            if 'TBPM' in audio_tags:
                metadata['bpm'] = audio_tags['TBPM'].text[0]
            
            if 'COMM::eng' in audio_tags:
                metadata['comment'] = audio_tags['COMM::eng'].text[0]
            elif 'COMM' in audio_tags:
                metadata['comment'] = audio_tags['COMM'].text[0]
            
            if 'TPE1' in audio_tags:
                metadata['artist'] = str(audio_tags['TPE1'])
            
            if 'TIT2' in audio_tags:
                metadata['title'] = str(audio_tags['TIT2'])
            
            # Extract bitrate
            if hasattr(audio_tags.info, 'bitrate'):
                metadata['bitrate'] = int(audio_tags.info.bitrate // 1000)
                
        except (ID3NoHeaderError, KeyError):
            pass
            
        return metadata
    
    def play_audio(self, audio_data, start_pos_seconds=None, duration=None):
        """
        Play audio from bytes data.
        
        Args:
            audio_data: Audio data bytes
            start_pos_seconds: Starting position in seconds
            duration: Total duration of the audio
            
        Returns:
            float: The starting position used for playback
        """
        if not audio_data:
            logger.error("Audio data not loaded.")
            return 0
            
        playback_start_time = start_pos_seconds
        if playback_start_time is None and duration:
            playback_start_time = duration * 0.20  # Default to 20% into the track
        elif playback_start_time is None:
            playback_start_time = 0
            
        pygame.mixer.music.load(io.BytesIO(audio_data))
        pygame.mixer.music.play(start=playback_start_time)
        
        return playback_start_time
    
    def stop_audio(self):
        """Stop audio playback and cleanup."""
        pygame.mixer.music.stop()
        if pygame.mixer.get_init():
            pygame.mixer.music.unload()
    
    def pause_audio(self):
        """Pause audio playback."""
        pygame.mixer.music.pause()
    
    def unpause_audio(self):
        """Resume audio playback."""
        pygame.mixer.music.unpause()
    
    def is_playing(self):
        """Check if audio is currently playing."""
        return pygame.mixer.music.get_busy()
    
    def get_playback_position(self):
        """Get current playback position in milliseconds."""
        return pygame.mixer.music.get_pos()
    
    def cleanup(self):
        """Cleanup pygame mixer resources."""
        pygame.mixer.quit()


class AudioFileManager:
    """Handles audio file discovery and filtering."""
    
    @staticmethod
    def find_mp3_files(directory, year_filter=None):
        """
        Find MP3 files in a directory, optionally filtered by year.
        
        Args:
            directory (str): Directory to search
            year_filter (str): Year to filter by (optional)
            
        Returns:
            tuple: (all_mp3s, filtered_mp3s)
        """
        all_mp3s = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.mp3'):
                    all_mp3s.append(os.path.join(root, file))
        
        if not year_filter:
            return all_mp3s, all_mp3s
        
        filtered_mp3s = []
        for filepath in all_mp3s:
            if AudioFileManager._matches_year(filepath, year_filter):
                filtered_mp3s.append(filepath)
        
        return all_mp3s, filtered_mp3s
    
    @staticmethod
    def _matches_year(filepath, year_filter):
        """
        Check if an MP3 file matches the year filter.
        
        Args:
            filepath (str): Path to the MP3 file
            year_filter (str): Year to match
            
        Returns:
            bool: True if file matches year filter
        """
        try:
            audio = MP3(filepath, ID3=ID3)
            # Try TDRC (ID3v2.4), then TYER (ID3v2.3)
            year_val = None
            if 'TDRC' in audio:
                year_val = str(audio['TDRC'])
            elif 'TYER' in audio:
                year_val = str(audio['TYER'])
            else:
                return False
            
            return year_val.startswith(year_filter)
        except Exception:
            return False
    
    @staticmethod
    def is_file_processed(filepath):
        """
        Check if a file has already been processed.
        
        Args:
            filepath (str): Path to the MP3 file
            
        Returns:
            bool: True if file has been processed
        """
        try:
            # Get custom ID3 tag from settings
            custom_id3_tag = settings_manager.get("CUSTOM_ID3_TAG", "PULZWAVE_APPROVED")
            
            audio = MP3(filepath, ID3=ID3)
            tag_key = f"TXXX:{custom_id3_tag}"
            return (tag_key in audio.tags and 
                    audio.tags[tag_key].text[0] == CUSTOM_ID3_VALUE)
        except Exception:
            return False
    
    @staticmethod
    def shuffle_files(files):
        """
        Shuffle a list of files in place.
        
        Args:
            files (list): List of file paths to shuffle
        """
        random.shuffle(files)
