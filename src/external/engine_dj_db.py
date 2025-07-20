"""Engine DJ database utilities: path conversion, rating update, and deletion."""

import os
import sqlite3
from ..config import DEFAULT_ENGINE_DB_PATH, DEFAULT_DJ_POOL_FOLDER_NAME
from ..utils.logger import get_logger
from ..utils.process_detection import check_engine_dj_with_dialog
from ..utils.settings_manager import SettingsManager

logger = get_logger()

settings_manager = SettingsManager()  # Singleton instance
settings_manager.load_settings()

def construct_db_path(full_path):
    """
    Convert an absolute file system path to the EngineDJ relative path format.
    e.g., 'D:\DJ_Pool\Trance\song.mp3' -> '../DJ_Pool/Trance/song.mp3'
    """
    # Get DJ pool folder from settings
    dj_pool_folder = settings_manager.get("DJ_POOL_FOLDER_NAME", DEFAULT_DJ_POOL_FOLDER_NAME)
    if not dj_pool_folder:
        logger.error("DJ Pool folder not configured in settings")
        return None
        
    norm_full_path = os.path.normpath(full_path)
    norm_pool_path = os.path.normpath(dj_pool_folder)
    if not norm_full_path.startswith(norm_pool_path):
        logger.debug(f"DJ Pool folder '{dj_pool_folder}' not found in path: {full_path}")
        return None
    rel_path = os.path.relpath(norm_full_path, norm_pool_path)
    rel_path = rel_path.replace(os.path.sep, '/')
    pool_dir_name = os.path.basename(norm_pool_path)
    return f"../{pool_dir_name}/{rel_path}"

def update_track_rating(filepath, rating):
    """
    Update the rating for a track in the Engine DJ database.
    Args:
        filepath (str): Absolute path to the file
        rating (int): Rating value (1-5)
    Returns:
        bool: True if updated, False otherwise
    """
    # Check for Engine DJ process before database operation
    if not check_engine_dj_with_dialog(None, "update the database"):
        logger.warning("Engine DJ database update cancelled due to Engine DJ running.")
        return False
    
    db_path = construct_db_path(filepath)
    if not db_path:
        logger.debug(f"File not in DJ Pool folder: {filepath}")
        return False
        
    # Get Engine DJ DB path from settings
    engine_db_path = settings_manager.get("ENGINE_DB_PATH", DEFAULT_ENGINE_DB_PATH)
    if not engine_db_path:
        logger.error("Engine DJ database path not configured in settings")
        return False
        
    if not os.path.exists(engine_db_path):
        logger.error(f"Engine DJ database not found at '{engine_db_path}'")
        return False
    try:
        conn = sqlite3.connect(engine_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Track WHERE path = ?", (db_path,))
        row = cursor.fetchone()
        if not row:
            logger.debug(f"Track not found in Engine DJ DB for path: {db_path}")
            return False
        track_id = row[0]
        db_rating = int(rating) * 20
        logger.debug(f"Updating Engine DJ DB rating for track_id={track_id}, rating={db_rating}")
        cursor.execute("UPDATE Track SET rating = ? WHERE id = ?", (db_rating, track_id))
        conn.commit()
        logger.info(f"Updated Engine DJ DB rating for {filepath} to {rating} stars.")
        return True
    except Exception as e:
        logger.error(f"Failed to update Engine DJ DB rating: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

def delete_track(filepath):
    """
    Delete a track from the Engine DJ database by file path.
    Args:
        filepath (str): Absolute path to the file
    Returns:
        bool: True if deleted, False otherwise
    """
    # Check for Engine DJ process before database operation
    if not check_engine_dj_with_dialog(None, "delete from the database"):
        logger.warning("Engine DJ database deletion cancelled due to Engine DJ running.")
        return False
    
    db_path = construct_db_path(filepath)
    if not db_path:
        logger.debug(f"File not in DJ Pool folder: {filepath}")
        return False
        
    # Get Engine DJ DB path from settings
    engine_db_path = settings_manager.get("ENGINE_DB_PATH", DEFAULT_ENGINE_DB_PATH)
    if not engine_db_path:
        logger.error("Engine DJ database path not configured in settings")
        return False
        
    if not os.path.exists(engine_db_path):
        logger.error(f"Engine DJ database not found at '{engine_db_path}'")
        return False
    try:
        conn = sqlite3.connect(engine_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Track WHERE path = ?", (db_path,))
        deleted = cursor.rowcount
        conn.commit()
        if deleted:
            logger.info(f"Deleted {deleted} record(s) from Engine DJ DB for {filepath}")
            return True
        else:
            logger.warning(f"No record deleted for {filepath} (not found in DB)")
            return False
    except Exception as e:
        logger.error(f"Failed to delete from Engine DJ DB: {e}")
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass
