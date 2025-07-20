"""Metadata management for MP3 files."""

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TXXX, POPM, TCON, ID3NoHeaderError

from ..config import CUSTOM_ID3_VALUE, RATING_TXXX_DESC
from ..utils.settings_manager import SettingsManager
from ..utils.logger import get_logger

logger = get_logger()


class MetadataManager:
    """Handles reading and writing MP3 metadata."""
    
    @staticmethod
    def save_metadata(filepath, rating=None, genre=None):
        """
        Save metadata to an MP3 file and update Engine DJ DB rating.
        
        Args:
            filepath (str): Path to the MP3 file
            rating (int): Rating value (1-5)
            genre (str): Genre string
            
        Returns:
            bool: True if successful, False otherwise
        """
        from ..external.engine_dj_db import update_track_rating
        
        # Get settings
        settings_manager = SettingsManager()
        settings_manager.load_settings()
        custom_id3_tag = settings_manager.get("CUSTOM_ID3_TAG", "PULZWAVE_APPROVED")
        popm_email = settings_manager.get("POPM_EMAIL", "changeme@pulzwave.com")
        
        try:
            logger.debug(f"Starting save_metadata for file: {filepath}, rating: {rating}, genre: {genre}")
            # Load or create ID3 tags
            try:
                audio = ID3(filepath)
                logger.debug("Loaded existing ID3 tags.")
            except ID3NoHeaderError:
                audio = ID3()
                logger.debug("No ID3 header found. Created new ID3 tags.")
            # Add processing marker
            audio.add(TXXX(encoding=3, desc=custom_id3_tag, text=[CUSTOM_ID3_VALUE]))
            logger.debug(f"Added processing marker: {custom_id3_tag} = {CUSTOM_ID3_VALUE}")
            # Handle rating (write to file first)
            if rating is not None and rating > 0:
                audio.delall('POPM')
                audio.delall(f'TXXX:{RATING_TXXX_DESC}')
                popm_rating = int(rating * 255 / 5)
                logger.debug(f"Setting POPM rating: {popm_rating} for email: {popm_email}")
                audio.add(POPM(email=popm_email, rating=popm_rating, count=0))
                audio.add(TXXX(encoding=3, desc=RATING_TXXX_DESC, text=str(rating)))
                logger.debug(f"Set TXXX rating: {RATING_TXXX_DESC} = {rating}")
            # Handle genre
            if genre:
                audio.delall('TCON')
                audio.add(TCON(encoding=3, text=genre))
                logger.debug(f"Set genre: {genre}")
            # Save the file
            logger.debug("Saving ID3 tags to file.")
            audio.save(filepath)
            logger.info("Metadata saved successfully to file.")
            # Now update Engine DJ DB rating
            if rating is not None and rating > 0:
                logger.debug("Attempting to update Engine DJ DB rating...")
                db_success = update_track_rating(filepath, rating)
                if db_success:
                    logger.info(f"Engine DJ DB rating updated for {filepath}.")
                else:
                    logger.warning(f"Engine DJ DB rating update failed or not applicable for {filepath}.")
            return True
        except Exception as e:
            logger.error(f"Could not save metadata: {e}")
            return False
    
    @staticmethod
    def get_artist_title(filepath):
        """
        Extract artist and title from MP3 file.
        
        Args:
            filepath (str): Path to the MP3 file
            
        Returns:
            tuple: (artist, title) or (None, None) if not found
        """
        try:
            audio = MP3(filepath, ID3=ID3)
            artist = audio.get('TPE1', [None])[0]
            title = audio.get('TIT2', [None])[0]
            return artist, title
        except Exception:
            return None, None
