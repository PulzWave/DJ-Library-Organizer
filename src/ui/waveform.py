"""Waveform visualization component."""

import tkinter as tk


class WaveformCanvas:
    """Handles waveform visualization and playback cursor."""
    
    def __init__(self, parent, width=1160, height=400):
        """
        Initialize the waveform canvas.
        
        Args:
            parent: Parent widget
            width: Canvas width
            height: Canvas height
        """
        self.canvas = tk.Canvas(
            parent,
            bg='black',
            highlightthickness=0,
            width=width,
            height=height,
            takefocus=True  # Allow canvas to receive keyboard focus
        )
        self.playback_cursor_id = None
        self.audio_duration = 0
        self.click_callback = None
        
        self.canvas.bind('<Button-1>', self._on_click)
    
    def pack(self, **kwargs):
        """Pack the canvas widget."""
        self.canvas.pack(**kwargs)
    
    def set_click_callback(self, callback):
        """
        Set callback for canvas clicks.
        
        Args:
            callback: Function to call with (x_position_ratio) when clicked
        """
        self.click_callback = callback
    
    def _on_click(self, event):
        """Handle canvas click events."""
        if self.click_callback and self.audio_duration > 0:
            x_ratio = event.x / self.canvas.winfo_width()
            seek_time = self.audio_duration * x_ratio
            self.click_callback(seek_time)
    
    def draw_waveform(self, waveform_lines):
        """
        Draw waveform visualization.
        
        Args:
            waveform_lines: List of line data dictionaries
        """
        self.clear()
        for line_data in waveform_lines:
            self.canvas.create_line(*line_data['coords'], **line_data['options'])
    
    def update_playback_cursor(self, progress_ratio):
        """
        Update the playback cursor position.
        
        Args:
            progress_ratio: Progress as ratio (0.0 to 1.0)
        """
        if self.playback_cursor_id:
            self.canvas.delete(self.playback_cursor_id)
        
        if 0 <= progress_ratio <= 1:
            cursor_x = int(self.canvas.winfo_width() * progress_ratio)
            self.playback_cursor_id = self.canvas.create_line(
                cursor_x, 0,
                cursor_x, self.canvas.winfo_height(),
                fill='red',
                width=2
            )
    
    def clear_cursor(self):
        """Clear the playback cursor."""
        if self.playback_cursor_id:
            self.canvas.delete(self.playback_cursor_id)
            self.playback_cursor_id = None
    
    def clear(self):
        """Clear the entire canvas."""
        self.canvas.delete("all")
        self.playback_cursor_id = None
    
    def focus_set(self):
        """Set focus to the canvas."""
        self.canvas.focus_set()
    
    def set_audio_duration(self, duration):
        """
        Set the audio duration for cursor calculations.
        
        Args:
            duration: Audio duration in seconds
        """
        self.audio_duration = duration
