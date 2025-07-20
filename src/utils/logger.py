"""Logging utility for the DJ Library Organizer application."""

import logging
import os
from datetime import datetime
from typing import Optional


class DJLibraryLogger:
    """Custom logger for DJ Library Organizer with date-based log files."""
    
    _instance: Optional['DJLibraryLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls) -> 'DJLibraryLogger':
        """Ensure singleton pattern for logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger if not already done."""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Set up the logger with date-based log files."""
        # Create logs directory if it doesn't exist
        app_data_dir = os.path.join(os.environ.get('APPDATA', '.'), 'PulzWaveDJLibraryOrganizer')

        os.makedirs(app_data_dir, exist_ok=True)
        log_dir = os.path.join(app_data_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate log filename with current date
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f'{today}.log')
        
        # Create logger
        self._logger = logging.getLogger('dj_library_organizer')
        self._logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler for ERROR and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
    
    @property
    def logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self._logger
    
    def debug(self, message: str) -> None:
        """Log debug message."""
        self._logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log info message."""
        self._logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning message."""
        self._logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log error message."""
        self._logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log critical message."""
        self._logger.critical(message)


# Create global logger instance
logger = DJLibraryLogger()


def get_logger() -> DJLibraryLogger:
    """Get the global logger instance."""
    return logger
