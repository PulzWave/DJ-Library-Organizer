"""External system integrations for Engine DJ and API."""

import os
import requests
from send2trash import send2trash

from ..config import API_HEADERS
from ..audio.metadata import MetadataManager
from ..utils.logger import get_logger
from ..utils.settings_manager import SettingsManager
from ..external.engine_dj_db import delete_track

logger = get_logger()


class ExternalDeletionManager:
    """Handles deletion from external systems and file system."""
    
    def __init__(self):
        """Initialize the deletion manager."""
        self.settings_manager = SettingsManager()
        self.settings_manager.load_settings()
    
    def delete_file_completely(self, filepath):
        """
        Delete file from all external systems and move to trash.
        
        Args:
            filepath (str): Path to the file to delete
            
        Returns:
            bool: True if successful
        """
        logger.info(f"Deletion process started for: {filepath}")
        
        # Delete from external systems
        self._delete_from_engine_dj(filepath)
        self._delete_from_api(filepath)
        
        # Move to recycle bin
        success = self._move_to_trash(filepath)
        
        logger.info("Deletion process finished")
        return success
    
    def _delete_from_engine_dj(self, filepath):
        """
        Delete track from Engine DJ database.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            bool: True if successfully deleted or if Engine DJ DB path is not configured
        """
        logger.info("Starting Engine DJ deletion process")
        
        # Get Engine DJ DB path from settings
        engine_db_path = self.settings_manager.get("ENGINE_DB_PATH", "")
        if not engine_db_path:
            logger.warning("Engine DJ Database path is not configured in settings. Skipping Engine DJ deletion.")
            return True
            
        deleted = delete_track(filepath)
        if deleted:
            logger.info(f"Track deleted from Engine DJ DB: {filepath}")
            return True
        else:
            logger.warning(f"Track not found or could not be deleted from Engine DJ DB: {filepath}")
            return False
    
    def _delete_from_api(self, filepath):
        """
        Give heads-up of a deletion to an API endpoint
        
        Args:
            filepath (str): Path to the file
        """
        logger.info("Starting API deletion process")
        
        # Check if API is enabled
        if not self.settings_manager.get("API_ENABLED", False):
            logger.info("API functionality is disabled in settings. Skipping API deletion.")
            return False
            
        # Get API URL from settings
        api_url = self.settings_manager.get("API_URL", "")
        if not api_url:
            logger.warning("API URL is not configured in settings. Skipping API deletion.")
            return False
        
        # Get artist and title from metadata
        artist, title = MetadataManager.get_artist_title(filepath)
        
        if not artist or not title:
            logger.info("MP3 is missing Artist (TPE1) or Title (TIT2) tag. Skipping API deletion.")
            return False
        
        logger.info(f"Attempting to delete from API: Artist='{artist}', Title='{title}'")
        
        payload = {"artistString": str(artist), "titleString": str(title)}
        
        try:
            response = requests.delete(
                api_url,
                headers=API_HEADERS,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                message = response.json().get('message', 'N/A')
                logger.info(f"Deleted from API. API Message: '{message}'")
                return True
            elif response.status_code == 404:
                logger.warning("Track not found on API (HTTP 404).")
                return True  # Consider this a successful operation
            else:
                logger.error(f"API returned an error. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return False
            logger.error(f"A network error occurred while calling the API: {e}")
    
    def _move_to_trash(self, filepath):
        """
        Move file to system trash/recycle bin.
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            bool: True if successful
        """
        try:
            normalized_path = os.path.normpath(filepath)
            send2trash(normalized_path)
            logger.info(f"Moved file to Recycle Bin: {os.path.basename(normalized_path)}")
            return True
        except Exception as e:
            logger.error(f"Failed to move file to Recycle Bin: {e}")
            return False
