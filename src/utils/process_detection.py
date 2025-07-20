"""Process detection utilities for Engine DJ safety checks."""

import psutil
import tkinter as tk
from tkinter import messagebox
from ..utils.logger import get_logger

logger = get_logger()

def is_engine_dj_running():
    """
    Check if Engine DJ is currently running.
    
    Returns:
        bool: True if Engine DJ process is found, False otherwise
    """
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] and 'Engine DJ.exe' in proc.info['name']:
                logger.warning(f"Engine DJ process detected: PID {proc.info['pid']}")
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking for Engine DJ process: {e}")
        # Return False to not block operation on error, but log it
        return False

def show_engine_dj_warning_dialog(parent=None, operation="start"):
    """
    Show a warning dialog when Engine DJ is detected.
    
    Args:
        parent: Parent window for the dialog
        operation: Description of the operation being attempted
        
    Returns:
        str: 'retry' if user wants to try again, 'exit' if user wants to exit
    """
    title = "Engine DJ Detected"
    message = (
        f"Engine DJ is currently running!\n\n"
        f"To prevent database corruption, please close Engine DJ "
        f"before {operation}ing the DJ Library Organizer.\n\n"
        f"What would you like to do?"
    )
    
    # Create custom dialog with Try Again and Exit buttons
    result = messagebox.askretrycancel(
        title=title,
        message=message,
        parent=parent
    )
    
    return 'retry' if result else 'exit'

def check_engine_dj_with_dialog(parent=None, operation="start"):
    """
    Check for Engine DJ and show dialog if found.
    
    Args:
        parent: Parent window for the dialog
        operation: Description of the operation being attempted
        
    Returns:
        bool: True if it's safe to proceed, False if user chose to exit
    """
    while is_engine_dj_running():
        choice = show_engine_dj_warning_dialog(parent, operation)
        if choice == 'exit':
            logger.info(f"User cancelled {operation} due to Engine DJ running.")
            return False
        # If 'retry', the loop continues to check again
    
    return True
