"""Main application class for the DJ Library Organizer."""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from PIL import Image, ImageTk

from .config import (
    APP_TITLE, WINDOW_GEOMETRY, RATING_TXXX_DESC,
    DEFAULT_NUM_THREADS, DEFAULT_GENRE_LIST
)
from .audio.processor import AudioProcessor, AudioFileManager
from .audio.metadata import MetadataManager
from .external.deletion_manager import ExternalDeletionManager
from .utils.eta_calculator import ETACalculator
from .utils.threading_utils import WorkerManager
from .ui.styles import UIStyleManager, RadioButtonGroup
from .ui.waveform import WaveformCanvas
from .ui.shortcuts import KeyboardShortcutManager
from .ui.config_dialog import ConfigDialog
from .utils.logger import get_logger
from .utils.process_detection import check_engine_dj_with_dialog
from .utils.settings_manager import SettingsManager

logger = get_logger()


class AudioProcessorApp:
    """Main application class for the DJ Library Organizer."""
    
    def __init__(self, master, settings_manager=None):
        """
        Initialize the application.
        
        Args:
            master: Root tkinter window
            settings_manager: Optional SettingsManager instance
        """
        self.master = master
        self.master.title(APP_TITLE)
        self.master.geometry(WINDOW_GEOMETRY)
        self.master.configure(bg='#2e2e2e')
        
        # Set window icon
        self._set_window_icon()
        
        # Use provided settings manager or create a new one
        self.settings_manager = settings_manager or SettingsManager()
        if settings_manager is None:
            self.settings_manager.load_settings()
        
        # Initialize core components
        self._init_variables()
        self._init_components()
        
        # Create UI
        self.style_manager.apply_dark_theme()
        self._create_menu_bar()
        self.create_widgets()
        # Moved shortcut registration after widgets are created
        self.shortcut_manager.setup_default_shortcuts(self)
        # Ensure shortcuts work by setting initial focus
        self.master.after(200, self._ensure_shortcuts_active)
        
    def _create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = tk.Menu(self.master)
        self.master.config(menu=menu_bar)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder...", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.destroy)
        
        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configuration...", command=lambda: self.open_config_dialog())
    
    def _init_variables(self):
        """Initialize application variables."""
        self.mp3_files = []
        self.total_files_to_process = 0
        self.current_file_path = None
        self.current_audio_data = None
        self.audio_duration = 0
        self.is_paused = False
        self.after_id = None
        self.playback_start_time = 0
        
        # Tkinter control variables
        self.rating_var = tk.IntVar(value=3)
        self.genre_var = tk.StringVar()
        self.year_var = tk.StringVar(value="")
        self.bpm_var = tk.StringVar(value="BPM: --")
        self.comment_var = tk.StringVar(value="Comment: --")
        self.bitrate_var = tk.StringVar(value="Bitrate: --")
    
    def _init_components(self):
        """Initialize application components."""
        # Re-check settings in case the first run dialog was closed without saving
        if not self.settings_manager.load_settings():
            return
            
        self.audio_processor = AudioProcessor()
        self.deletion_manager = ExternalDeletionManager()
        self.eta_calculator = ETACalculator()
        self.style_manager = UIStyleManager(self.master)
        self.shortcut_manager = KeyboardShortcutManager(self.master)
        
        # Initialize worker manager
        self.stop_workers = threading.Event()
        self.worker_manager = WorkerManager(
            self.settings_manager.get("NUM_THREADS", DEFAULT_NUM_THREADS),
            self.audio_processor.analyze_audio_file,
            self.stop_workers
        )
    
    def open_config_dialog(self, first_run=False):
        """Open the configuration dialog."""
        dialog = ConfigDialog(
            self.master, 
            self.settings_manager, 
            on_save_callback=self.on_settings_saved, 
            first_run=first_run
        )
        # Make sure dialog is completely processed before continuing
        if first_run:
            self.master.update()
        
        self.master.wait_window(dialog)
        
    def on_settings_saved(self):
        """Callback when settings are saved."""
        # Only reload worker manager if already initialized
        if hasattr(self, 'stop_workers') and hasattr(self, 'worker_manager'):
            self.stop_workers.set()
            self.worker_manager.stop_workers()
            self.stop_workers = threading.Event()
            self.worker_manager = WorkerManager(
                self.settings_manager.get("NUM_THREADS", DEFAULT_NUM_THREADS),
                self.audio_processor.analyze_audio_file,
                self.stop_workers
            )
        # Only update genre dropdown if genre_combo exists
        if hasattr(self, 'genre_combo'):
            self._update_genre_dropdown()
        logger.info("Settings updated and applied")
    
    def create_widgets(self):
        """Create and layout all UI widgets."""
        self._create_top_frame()
        self._create_waveform()
        self._create_info_and_metadata_controls()
        self._create_bottom_frame()
        self._create_status_bar()
        
    def _update_genre_dropdown(self):
        """Update the genre dropdown with values from settings."""
        genre_list = self.settings_manager.get("GENRE_LIST", DEFAULT_GENRE_LIST)
        genre_list.sort()
        self.genre_combo['values'] = genre_list
    
    def _create_top_frame(self):
        """Create the top frame with directory selection and file info."""
        top_frame = ttk.Frame(self.master, padding=(0, 10))
        top_frame.pack(fill=tk.X)
        
        # Year filter
        year_frame = ttk.Frame(top_frame)
        year_frame.pack(side=tk.RIGHT, padx=10)
        ttk.Label(year_frame, text="Year filter:").pack(side=tk.LEFT)
        year_entry = ttk.Entry(year_frame, textvariable=self.year_var, width=8)
        year_entry.pack(side=tk.LEFT)
        
        # Directory selection button
        self.dir_button = ttk.Button(
            top_frame,
            text="Select MP3 Directory",
            command=self.select_directory
        )
        self.dir_button.pack(pady=5)
        
        # Current file label
        self.current_file_label = ttk.Label(
            top_frame,
            text="No file loaded.",
            style='Header.TLabel',
            wraplength=1100,
            anchor='center'
        )
        self.current_file_label.pack(pady=5, fill=tk.X, expand=True)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.master,
            mode='indeterminate',
            style='Blue.Horizontal.TProgressbar'
        )
    
    def _create_waveform(self):
        """Create the waveform visualization."""
        self.waveform_canvas = WaveformCanvas(self.master)
        self.waveform_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.waveform_canvas.set_click_callback(self.seek_on_click)
    
    def _create_info_and_metadata_controls(self):
        """Create information display and metadata controls."""
        controls_container = ttk.Frame(self.master, padding=10)
        controls_container.pack(fill=tk.X)
        
        # Info frame (BPM, Bitrate, Comment)
        info_frame = ttk.Frame(controls_container, padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        bpm_label = ttk.Label(info_frame, textvariable=self.bpm_var, style='Info.TLabel')
        bpm_label.pack(side=tk.LEFT, padx=20, expand=True, anchor='w')
        
        self.bitrate_label = ttk.Label(info_frame, textvariable=self.bitrate_var, style='Info.TLabel')
        self.bitrate_label.pack(side=tk.LEFT, padx=20, expand=True, anchor='w')
        
        comment_label = ttk.Label(
            info_frame,
            textvariable=self.comment_var,
            style='Info.TLabel',
            wraplength=800,
            justify=tk.LEFT
        )
        comment_label.pack(side=tk.LEFT, padx=20, expand=True, anchor='w')
        
        # Metadata frame (Rating and Genre)
        metadata_frame = ttk.Frame(controls_container)
        metadata_frame.pack(fill=tk.X)
        
        # Rating controls
        rating_frame = ttk.Frame(metadata_frame)
        rating_frame.pack(side=tk.LEFT, padx=20, expand=True)
        ttk.Label(rating_frame, text="Rating:").pack(side=tk.LEFT, padx=(0, 10))
        
        RadioButtonGroup(
            rating_frame,
            self.rating_var,
            values=list(range(1, 6)),
            clear_button=True
        )
        
        # Genre controls
        genre_frame = ttk.Frame(metadata_frame)
        genre_frame.pack(side=tk.RIGHT, padx=20, expand=True)
        ttk.Label(genre_frame, text="Genre:").pack(side=tk.LEFT, padx=(0, 10))

        # Get genres from settings
        genre_list = self.settings_manager.get("GENRE_LIST", DEFAULT_GENRE_LIST)
        genre_list.sort()
        
        self.genre_combo = ttk.Combobox(
            genre_frame,
            textvariable=self.genre_var,
            values=genre_list,
            width=25
        )
        self.genre_combo.pack(side=tk.LEFT)
        
        # Prevent combobox from stealing arrow key shortcuts
        self._configure_combobox_bindings()
    
    def _configure_combobox_bindings(self):
        """Configure combobox to not interfere with keyboard shortcuts."""
        # Unbind Up/Down from the specific combobox instance, not the class
        self.genre_combo.bind('<Up>', lambda e: 'break')
        self.genre_combo.bind('<Down>', lambda e: 'break')
        
        # Also prevent the combobox from consuming these keys when it has focus
        self.genre_combo.bind('<FocusIn>', self._on_combobox_focus_in)
        self.genre_combo.bind('<FocusOut>', self._on_combobox_focus_out)
    
    def _on_combobox_focus_in(self, event):
        """Handle combobox gaining focus."""
        # When combobox gains focus, we need to be more careful about key handling
        pass
    
    def _on_combobox_focus_out(self, event):
        """Handle combobox losing focus."""
        # When combobox loses focus, ensure global shortcuts work
        pass
    
    def _ensure_shortcuts_active(self):
        """Ensure keyboard shortcuts are properly active."""
        # Give focus to the waveform canvas to ensure shortcuts work
        self.waveform_canvas.focus_set()
        # Log debug info to check if shortcuts are registered
        logger.debug(f"Shortcuts registered: {list(self.shortcut_manager.callbacks.keys())}")
        logger.debug(f"Waveform canvas focus: {self.waveform_canvas.canvas.focus_get() == self.waveform_canvas.canvas}")
        
        # Test the button states for conditional shortcuts
        logger.debug(f"Keep button state: {self.keep_button['state']}")
        logger.debug(f"Delete button state: {self.delete_button['state']}")
    
    def _create_bottom_frame(self):
        """Create the bottom frame with action buttons."""
        bottom_frame = ttk.Frame(self.master, padding=(0, 20))
        bottom_frame.pack(fill=tk.X)
        
        button_container = ttk.Frame(bottom_frame)
        button_container.pack()
        
        # Add configuration button
        self.config_button = ttk.Button(
            button_container,
            text="⚙ Configure",
            command=lambda: self.open_config_dialog()
        )
        self.config_button.pack(side=tk.LEFT, padx=20, ipady=10, ipadx=20)
        
        self.keep_button = ttk.Button(
            button_container,
            text="▲ Keep & Save",
            command=self.keep_file,
            state='disabled'
        )
        self.keep_button.pack(side=tk.LEFT, padx=20, ipady=10, ipadx=30)
        
        self.delete_button = ttk.Button(
            button_container,
            text="▼ Delete",
            command=self.delete_file,
            state='disabled'
        )
        self.delete_button.pack(side=tk.LEFT, padx=20, ipady=10, ipadx=30)
    
    def _create_status_bar(self):
        """Create the status bar with logo."""
        # Create a frame for the status bar and logo
        status_frame = ttk.Frame(self.master)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # Status label on the left
        self.status_bar = ttk.Label(
            status_frame,
            text="Welcome! Select a directory to start.",
            style='Status.TLabel',
            anchor='w'
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Logo on the right
        self._create_logo_widget(status_frame)
    
    def _create_logo_widget(self, parent):
        """Create the Pulzwave logo widget in the bottom right."""
        try:
            # Get the path to the logo image
            logo_path = os.path.join(os.path.dirname(__file__), 'image', 'pulzwave_logo.png')
            
            if os.path.exists(logo_path):
                # Load and resize the image
                pil_image = Image.open(logo_path)
                
                # Calculate scaled size maintaining aspect ratio, max width 100px
                original_width, original_height = pil_image.size
                max_width = 100
                
                if original_width > max_width:
                    ratio = max_width / original_width
                    new_width = max_width
                    new_height = int(original_height * ratio)
                else:
                    new_width = original_width
                    new_height = original_height
                
                # Resize the image
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage for tkinter
                self.logo_image = ImageTk.PhotoImage(pil_image)
                
                # Create label with the logo
                logo_label = tk.Label(parent, image=self.logo_image, bg='#2e2e2e', bd=0)
                logo_label.pack(side=tk.RIGHT, padx=(10, 0))
                
                # Keep a reference to prevent garbage collection
                logo_label.image = self.logo_image
                
                logger.debug(f"Logo loaded successfully: {new_width}x{new_height}")
            else:
                logger.warning(f"Logo file not found: {logo_path}")
                
        except Exception as e:
            logger.error(f"Failed to load logo: {e}")
            # Create a simple text label as fallback
            fallback_label = ttk.Label(parent, text="PULZWAVE", style='Status.TLabel')
            fallback_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def _set_window_icon(self):
        """Set the window icon using pulzwave_icon.png, compatible with PyInstaller."""
        import sys
        try:
            # Detect if running in a PyInstaller bundle
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
                icon_path = os.path.join(base_path, 'src', 'image', 'pulzwave_icon.png')
            else:
                base_path = os.path.dirname(__file__)
                icon_path = os.path.join(base_path, 'image', 'pulzwave_icon.png')

            if os.path.exists(icon_path):
                from PIL import Image, ImageTk
                icon_image = Image.open(icon_path)
                icon_photo = ImageTk.PhotoImage(icon_image)
                self.master.iconphoto(True, icon_photo)
                self.icon_image = icon_photo  # Prevent garbage collection
                logger.debug(f"Window icon set successfully from: {icon_path}")
            else:
                logger.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}")
    
    # File and Directory Management Methods
    def select_directory(self):
        """Handle directory selection and file discovery."""
        directory = filedialog.askdirectory(title="Select Folder with MP3s")
        if not directory:
            return
        
        self.status_bar.config(text=f"Scanning {directory} for MP3s...")
        self.master.update()
        
        # Stop any existing workers
        self.worker_manager.stop_workers()
        
        # Find and filter MP3 files
        year_filter = self.year_var.get().strip() or None
        all_mp3s, filtered_mp3s = AudioFileManager.find_mp3_files(directory, year_filter)
        
        # Filter out already processed files
        self.mp3_files = [
            f for f in filtered_mp3s
            if not AudioFileManager.is_file_processed(f)
        ]
        
        self.status_bar.config(
            text=f"Found {len(self.mp3_files)} unprocessed MP3s out of {len(all_mp3s)} total."
        )
        
        if self.mp3_files:
            # Disable controls and show loading state
            self._disable_controls()
            self._show_waveform_loading_state()
            
            # Shuffle and prepare for processing
            AudioFileManager.shuffle_files(self.mp3_files)
            self.eta_calculator.reset()
            self.total_files_to_process = len(self.mp3_files)
            
            # Start background analysis
            self.worker_manager.start_workers(self.mp3_files)
            self.process_next_song()
        else:
            messagebox.showinfo("No Files Found", "No unprocessed MP3 files were found.")
    
    def process_next_song(self):
        """Process the next song in the queue."""
        self._cleanup_current_track()
        self._cancel_after_event()
        
        # Check for results or wait for analysis
        if not self.worker_manager.has_results():
            if self.worker_manager.has_pending_files() or self.worker_manager.workers_active():
                # Still processing - update status but keep waiting
                self.status_bar.config(text="Analyzing audio files...")
                self.master.after(200, self.process_next_song)
                return
            else:
                # All done
                self._show_completion_message()
                return
        
        # We have a result - clear any existing waveform but don't show progress bar yet
        self.waveform_canvas.clear()
        
        # Show loading state for song preparation
        self._show_loading_state()
        
        # Get analysis result
        analysis_result = self.worker_manager.get_result(timeout=1.0)
        if not analysis_result:
            self.master.after(100, self.process_next_song)
            return
        
        # Load the analyzed track
        self._load_analyzed_track(analysis_result)
    
    def _cleanup_current_track(self):
        """Clean up resources from current track."""
        self.audio_processor.stop_audio()
        self.current_audio_data = None
    
    def _cancel_after_event(self):
        """Cancel any pending after events."""
        if self.after_id:
            self.master.after_cancel(self.after_id)
            self.after_id = None
    
    def _show_loading_state(self):
        """Show loading progress bar."""
        self.status_bar.config(text="Loading next pre-analyzed song...")
        self.current_file_label.config(text="...")
        self.progress_bar.pack(fill=tk.X, padx=20, pady=5, before=self.waveform_canvas.canvas)
        self.progress_bar.start(10)
        self.master.update_idletasks()
    
    def _hide_loading_state(self):
        """Hide loading progress bar."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
    
    def _load_analyzed_track(self, analysis_result):
        """Load an analyzed track for playback and editing."""
        self._hide_loading_state()
        self._hide_waveform_loading_state()
        
        # Extract analysis data
        self.current_file_path = analysis_result['filepath']
        self.current_audio_data = analysis_result['audio_data']
        self.audio_duration = analysis_result['duration']
        
        # Start ETA tracking
        self.eta_calculator.start_tracking()
        
        # Update UI
        self._update_file_display(analysis_result)
        self._load_waveform(analysis_result['waveform_lines'])
        self._load_metadata_ui(analysis_result.get('metadata', {}))
        
        # Enable controls and start playback
        self._enable_controls()
        self._start_playback()
    
    def _update_file_display(self, analysis_result):
        """Update the current file display."""
        meta = analysis_result.get('metadata', {})
        artist = meta.get('artist')
        title = meta.get('title')
        
        if artist and title:
            display_text = f"{artist} - {title}"
        else:
            display_text = os.path.basename(self.current_file_path)
        
        self.current_file_label.config(text=display_text)
    
    def _load_waveform(self, waveform_lines):
        """Load waveform visualization."""
        self.waveform_canvas.draw_waveform(waveform_lines)
        self.waveform_canvas.set_audio_duration(self.audio_duration)
    
    def _load_metadata_ui(self, metadata):
        """Load metadata into UI controls."""
        # Set rating (default to 3 if not present)
        if 'rating' in metadata:
            self.rating_var.set(metadata['rating'])
        else:
            self.rating_var.set(3)
        
        # Set genre
        current_genre = metadata.get('genre', "")
        genre_list = self.settings_manager.get("GENRE_LIST", DEFAULT_GENRE_LIST)
        if current_genre and current_genre not in genre_list:
            self.genre_combo['values'] = genre_list + [current_genre]
        else:
            self.genre_combo['values'] = genre_list
        self.genre_var.set(current_genre)
        
        # Set info displays
        self.bpm_var.set(f"BPM: {metadata.get('bpm', '--')}")
        self.comment_var.set(f"Comment: {metadata.get('comment', '--')}")
        
        # Set bitrate with color coding
        bitrate_val = metadata.get('bitrate')
        if bitrate_val is not None:
            self.bitrate_var.set(f"Bitrate: {bitrate_val}")
            color = 'cyan' if str(bitrate_val) == '320' else 'red'
            self.bitrate_label.configure(foreground=color)
        else:
            self.bitrate_var.set("Bitrate: --")
            self.bitrate_label.configure(foreground='cyan')
    
    def _enable_controls(self):
        """Enable user controls."""
        self.keep_button.config(state='normal')
        self.delete_button.config(state='normal')
        # Ensure the waveform canvas has focus for keyboard shortcuts
        self.master.after(100, lambda: self.waveform_canvas.focus_set())
        logger.debug("Controls enabled - buttons should now respond to Up/Down keys")
    
    def _disable_controls(self):
        """Disable user controls during loading."""
        self.keep_button.config(state='disabled')
        self.delete_button.config(state='disabled')
    
    def _show_waveform_loading_state(self):
        """Show loading indicator in waveform area."""
        self.waveform_canvas.clear()
        self.current_file_label.config(text="Loading waveform...")
        self.status_bar.config(text="Preparing first song...")
    
    def _hide_waveform_loading_state(self):
        """Hide loading indicator in waveform area."""
        # This will be called when the actual track is loaded
        pass
    
    def _start_playback(self):
        """Start audio playback and cursor updates."""
        self.playback_start_time = self.audio_processor.play_audio(
            self.current_audio_data,
            duration=self.audio_duration
        )
        self.is_paused = False
        self.update_playback_cursor()
    
    def _show_completion_message(self):
        """Show completion message when all files are processed."""
        messagebox.showinfo("All Done!", "You have processed all the MP3s.")
        self.current_file_label.config(text="All files processed!")
        self._disable_controls()
        self.status_bar.config(text="Processing complete.")
    
    # Action Methods
    def keep_file(self):
        """Keep the current file and save metadata."""
        if not self.current_file_path:
            return
        
        self.eta_calculator.log_completion()
        self._cleanup_current_track()
        
        logger.info(f"Keeping and saving metadata for: {self.current_file_path}")
        
        # Save metadata
        success = MetadataManager.save_metadata(
            self.current_file_path,
            rating=self.rating_var.get() if self.rating_var.get() > 0 else None,
            genre=self.genre_var.get() if self.genre_var.get() else None
        )
        
        if not success:
            messagebox.showerror("Save Error", "Could not save tags for file.")
        
        self.process_next_song()
    
    def delete_file(self):
        """Delete the current file."""
        if not self.current_file_path:
            return
        
        self.eta_calculator.log_completion()
        self._cleanup_current_track()
        
        filepath_to_delete = self.current_file_path
        
        # Perform deletion
        success = self.deletion_manager.delete_file_completely(filepath_to_delete)
        
        if not success:
            messagebox.showerror(
                "File Deletion Error",
                f"Could not move file to Recycle Bin:\n{filepath_to_delete}"
            )
        
        self.process_next_song()
    
    # Playback Control Methods
    def toggle_pause(self):
        """Toggle pause/play state."""
        if not self.current_file_path or (not self.audio_processor.is_playing() and not self.is_paused):
            return
        if self.is_paused:
            self.audio_processor.unpause_audio()
            self.is_paused = False
        else:
            self.audio_processor.pause_audio()
            self.is_paused = True
    
    def seek_forward(self):
        """Seek forward by 12% of track duration."""
        self._seek_relative('forward')
    
    def seek_backward(self):
        """Seek backward by 12% of track duration."""
        self._seek_relative('backward')
    
    def _seek_relative(self, direction):
        """Seek playback relative to current position."""
        if not self.audio_duration or not self.audio_processor.is_playing():
            return
        
        skip_amount = self.audio_duration * 0.12
        current_time_ms = self.audio_processor.get_playback_position()
        current_elapsed_seconds = self.playback_start_time + (current_time_ms / 1000.0)
        
        if direction == 'forward':
            new_position = min(
                current_elapsed_seconds + skip_amount,
                self.audio_duration - 0.1
            )
        else:  # 'backward'
            new_position = max(0, current_elapsed_seconds - skip_amount)
        
        self.playback_start_time = self.audio_processor.play_audio(
            self.current_audio_data,
            start_pos_seconds=new_position
        )
        self._cancel_after_event()
        self.update_playback_cursor()
    
    def seek_on_click(self, seek_time):
        """Handle waveform click to seek to position."""
        if self.audio_duration > 0:
            self.playback_start_time = self.audio_processor.play_audio(
                self.current_audio_data,
                start_pos_seconds=seek_time
            )
            self._cancel_after_event()
            self.update_playback_cursor()
    
    def update_playback_cursor(self):
        """Update playback cursor and status information."""
        is_playing = self.audio_processor.is_playing() and not self.is_paused
        
        if (is_playing or self.is_paused) and self.audio_duration > 0:
            # Calculate current position
            current_time_ms = self.audio_processor.get_playback_position()
            total_elapsed_seconds = self.playback_start_time + (current_time_ms / 1000.0)
            progress_ratio = total_elapsed_seconds / self.audio_duration
            
            # Update cursor
            self.waveform_canvas.update_playback_cursor(progress_ratio)
            
            # Update status
            self._update_playback_status(total_elapsed_seconds, is_playing)
            
            # Schedule next update
            self.after_id = self.master.after(50, self.update_playback_cursor)
        else:
            # Playback finished or stopped
            self.waveform_canvas.clear_cursor()
            self.after_id = None
            self._update_finished_status()
    
    def _update_playback_status(self, current_time, is_playing):
        """Update status bar during playback."""
        # Format time display
        mins, secs = divmod(int(current_time), 60)
        total_mins, total_secs = divmod(int(self.audio_duration), 60)
        time_str = f"Time: {mins:02}:{secs:02} / {total_mins:02}:{total_secs:02}"
        
        # Get remaining count
        file_count, result_count = self.worker_manager.get_queue_sizes()
        remaining = file_count + result_count
        
        # Build status text
        status_parts = [time_str, f"Remaining: {remaining}"]
        
        # Add ETA if available
        eta_str = self.eta_calculator.get_eta_string(remaining)
        if eta_str:
            status_parts.append(eta_str)
        
        status_text = " | ".join(status_parts)
        
        if self.is_paused:
            status_text = f"Paused | {status_text}"
        
        self.status_bar.config(text=status_text)
    
    def _update_finished_status(self):
        """Update status when playback is finished."""
        file_count, result_count = self.worker_manager.get_queue_sizes()
        remaining_count = file_count + result_count
        
        if remaining_count == 0:
            self.status_bar.config(text="Processing complete.")
        else:
            self.status_bar.config(text=f"Song finished. Choose an action. ({remaining_count} remaining)")
    
    # Keyboard Shortcut Handlers
    def can_keep_file(self):
        """Check if keep file action is available."""
        state = str(self.keep_button['state'])
        result = state == 'normal'
        logger.debug(f"can_keep_file: button state='{state}', result={result}")
        return result
    
    def can_delete_file(self):
        """Check if delete file action is available."""
        state = str(self.delete_button['state'])
        result = state == 'normal'
        logger.debug(f"can_delete_file: button state='{state}', result={result}")
        return result
    
    def set_rating_from_key(self, event=None):
        """Set rating from number key press."""
        if event and event.char.isdigit() and 1 <= int(event.char) <= 5:
            self.rating_var.set(int(event.char))
        return "break"
    
    def debug_shortcuts(self):
        """Debug method to test shortcuts."""
        logger.debug("=== SHORTCUT DEBUG INFO ===")
        logger.debug(f"Focus widget: {self.master.focus_get()}")
        logger.debug(f"Keep button state: {repr(self.keep_button['state'])}")
        logger.debug(f"Delete button state: {repr(self.delete_button['state'])}")
        logger.debug(f"Keep button state == 'normal': {self.keep_button['state'] == 'normal'}")
        logger.debug(f"Delete button state == 'normal': {self.delete_button['state'] == 'normal'}")
        logger.debug(f"Keep button state == tk.NORMAL: {self.keep_button['state'] == tk.NORMAL}")
        logger.debug(f"Delete button state == tk.NORMAL: {self.delete_button['state'] == tk.NORMAL}")
        logger.debug(f"tk.NORMAL value: {repr(tk.NORMAL)}")
        logger.debug(f"tk.DISABLED value: {repr(tk.DISABLED)}")
        logger.debug("Button widget info:")
        logger.debug(f"  Keep button: {self.keep_button.winfo_class()}")
        logger.debug(f"  Keep button state type: {type(self.keep_button['state'])}")
        logger.debug(f"Registered shortcuts: {list(self.shortcut_manager.callbacks.keys())}")
        
        # Test the condition functions directly
        logger.debug("Testing condition functions:")
        try:
            up_condition = lambda: self.keep_button['state'] == 'normal'
            down_condition = lambda: self.delete_button['state'] == 'normal'
            logger.debug(f"Up condition result: {up_condition()}")
            logger.debug(f"Down condition result: {down_condition()}")
            
            # Force enable buttons for testing
            logger.debug("Force enabling buttons for test...")
            self.keep_button.config(state='normal')
            self.delete_button.config(state='normal')
            logger.debug(f"After force enable - Keep button state: {repr(self.keep_button['state'])}")
            logger.debug(f"After force enable - Delete button state: {repr(self.delete_button['state'])}")
            logger.debug(f"Up condition result after enable: {up_condition()}")
            logger.debug(f"Down condition result after enable: {down_condition()}")
            
        except Exception as e:
            logger.error(f"Error testing conditions: {e}")
        
        logger.debug("=== END DEBUG ===")
        # Force focus to canvas
        self.waveform_canvas.focus_set()
    
    # Cleanup Methods
    def on_closing(self):
        """Handle application closing."""
        logger.info("Closing application, stopping workers...")
        try:
            # Stop the workers first
            if hasattr(self, 'worker_manager'):
                self.worker_manager.stop_workers()
            
            # Clean up audio processor
            if hasattr(self, 'audio_processor'):
                self.audio_processor.cleanup()
            
            # Clean up shortcut manager
            if hasattr(self, 'shortcut_manager'):
                self.shortcut_manager.cleanup()
            
            # Destroy the master window if it exists and isn't already destroyed
            if hasattr(self, 'master') and self.master and self.master.winfo_exists():
                self.master.destroy()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main entry point for the application."""
    # Check for Engine DJ process on startup
    if not check_engine_dj_with_dialog(None, "start"):
        logger.info("Application startup cancelled due to Engine DJ running.")
        return

    # Initialize settings manager first to check if settings exist
    settings_manager = SettingsManager()
    settings_exist = settings_manager.load_settings()

    # Create root window
    root = tk.Tk()
    
    # For first run, show config dialog before creating the full application
    if not settings_exist:
        logger.info("Initial configuration required. Showing setup dialog.")
        from .ui.config_dialog import ConfigDialog
        
        dialog = ConfigDialog(root, settings_manager, first_run=True)
        root.wait_window(dialog)
        
        # Check if settings were saved after dialog closed
        if not settings_manager.load_settings():
            logger.info("First-run configuration canceled. Exiting application.")
            # The dialog was closed without saving, exit the application
            return
    
    # Only create the application if we have valid settings
    app = AudioProcessorApp(root, settings_manager)
    
    # Set up the close handler
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    # Don't do anything after mainloop - the window might be destroyed


if __name__ == "__main__":
    main()
