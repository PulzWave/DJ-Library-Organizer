"""Threading utilities for background processing."""

import threading
import queue
import time
from .logger import get_logger

logger = get_logger()


class WorkerManager:
    """Manages worker threads for background audio analysis."""
    
    def __init__(self, num_workers, worker_function, stop_event):
        """
        Initialize worker manager.
        
        Args:
            num_workers (int): Number of worker threads to create
            worker_function: Function to execute in worker threads
            stop_event (threading.Event): Event to signal workers to stop
        """
        self.num_workers = num_workers
        self.worker_function = worker_function
        self.stop_event = stop_event
        self.worker_threads = []
        
        self.file_path_queue = queue.Queue()
        self.analysis_queue = queue.Queue(maxsize=num_workers + 1)
    
    def start_workers(self, file_list):
        """
        Start worker threads with a list of files to process.
        
        Args:
            file_list (list): List of file paths to process
        """
        self.stop_workers()
        self._clear_queues()
        
        # Add files to processing queue
        for filepath in file_list:
            self.file_path_queue.put(filepath)
        
        # Start worker threads
        self.worker_threads = []
        for _ in range(self.num_workers):
            thread = threading.Thread(
                target=self._worker_wrapper,
                daemon=True
            )
            thread.start()
            self.worker_threads.append(thread)
    
    def stop_workers(self):
        """Stop all worker threads."""
        self.stop_event.set()
        self._clear_file_queue()
        
        # Wait for threads to finish
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        self.worker_threads = []
        self.stop_event.clear()
    
    def _worker_wrapper(self):
        """Wrapper for worker function that handles queue management."""
        while not self.stop_event.is_set():
            try:
                filepath = self.file_path_queue.get(timeout=0.5)
            except queue.Empty:
                break
            
            try:
                result = self.worker_function(filepath)
                self.analysis_queue.put(result)
            except Exception as e:
                logger.error(f"Worker error processing {filepath}: {e}")
            finally:
                self.file_path_queue.task_done()
    
    def _clear_queues(self):
        """Clear all queues."""
        self._clear_file_queue()
        while not self.analysis_queue.empty():
            try:
                self.analysis_queue.get_nowait()
            except queue.Empty:
                break
    
    def _clear_file_queue(self):
        """Clear the file path queue."""
        while not self.file_path_queue.empty():
            try:
                self.file_path_queue.get_nowait()
            except queue.Empty:
                break
    
    def get_result(self, timeout=1.0):
        """
        Get a result from the analysis queue.
        
        Args:
            timeout (float): Timeout in seconds
            
        Returns:
            Analysis result or None if timeout
        """
        try:
            return self.analysis_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def has_pending_files(self):
        """Check if there are files waiting to be processed."""
        return not self.file_path_queue.empty()
    
    def has_results(self):
        """Check if there are results available."""
        return not self.analysis_queue.empty()
    
    def workers_active(self):
        """Check if any worker threads are still active."""
        return any(t.is_alive() for t in self.worker_threads)
    
    def get_queue_sizes(self):
        """
        Get current queue sizes.
        
        Returns:
            tuple: (file_queue_size, analysis_queue_size)
        """
        return self.file_path_queue.qsize(), self.analysis_queue.qsize()
