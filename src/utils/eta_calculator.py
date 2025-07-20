"""ETA (Estimated Time of Arrival) calculation utilities."""

import time
from collections import deque
from .logger import get_logger

logger = get_logger()


class ETACalculator:
    """Calculates and tracks estimated time remaining for processing."""
    
    def __init__(self, max_samples=10):
        """
        Initialize ETA calculator.
        
        Args:
            max_samples (int): Maximum number of processing time samples to keep
        """
        self.processing_times = deque(maxlen=max_samples)
        self.current_track_start_time = None
    
    def start_tracking(self):
        """Start tracking time for the current operation."""
        self.current_track_start_time = time.time()
    
    def log_completion(self):
        """Log completion of current operation and calculate duration."""
        if self.current_track_start_time:
            duration = time.time() - self.current_track_start_time
            self.processing_times.append(duration)
            logger.info(f"Track processed in {duration:.2f}s. Pace based on last {len(self.processing_times)} tracks.")
        self.current_track_start_time = None
    
    def get_eta_string(self, remaining_count):
        """
        Get formatted ETA string.
        
        Args:
            remaining_count (int): Number of items remaining to process
            
        Returns:
            str: Formatted ETA string or empty if not enough data
        """
        if not self.processing_times or len(self.processing_times) < 3:
            return ""
        
        if remaining_count == 0:
            return ""
        
        avg_time = sum(self.processing_times) / len(self.processing_times)
        total_seconds = avg_time * remaining_count
        
        # Don't show ETA for less than a minute
        if total_seconds < 60:
            return ""
        
        minutes, _ = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        return f"ETA: {int(hours):02}:{int(minutes):02}"
    
    def reset(self):
        """Reset all tracking data."""
        self.processing_times.clear()
        self.current_track_start_time = None
