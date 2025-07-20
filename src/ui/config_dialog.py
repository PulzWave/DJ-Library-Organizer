"""Configuration dialog for the DJ Library Organizer application."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ConfigDialog(tk.Toplevel):
    """Configuration dialog window for setting application preferences."""
    
    def __init__(self, parent, settings_manager, on_save_callback=None, first_run=False):
        """
        Initialize the configuration dialog.
        
        Args:
            parent: Parent window
            settings_manager: SettingsManager instance
            on_save_callback: Callback function to run after settings are saved
            first_run: Whether this is the first run of the application
        """
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.on_save_callback = on_save_callback
        self.first_run = first_run
        
        self.title("Configuration" + (" - Initial Setup" if first_run else ""))
        self.geometry("800x800")  # Increased default size for better fit
        self.resizable(True, True)  # Allow resizing
        self.minsize(600, 500)      # Set a minimum size
        self.configure(bg='#2e2e2e')
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        if first_run:
            self.protocol("WM_DELETE_WINDOW", self.on_first_run_close)
        else:
            self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.create_widgets()
        self.load_current_settings()
        
        # Center the dialog on the parent window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.parent.winfo_width() // 2) - (width // 2) + self.parent.winfo_x()
        y = (self.parent.winfo_height() // 2) - (height // 2) + self.parent.winfo_y()
        self.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        """Create the dialog widgets."""
        main_frame = ttk.Frame(self, padding="20", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Style configuration (override for dialog)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background='#2e2e2e', foreground='white', font=('Helvetica', 10))
        style.configure("TFrame", background='#2e2e2e')
        style.configure("TButton", background='#4a4a4a', foreground='white', font=('Helvetica', 12, 'bold'), padding=10)
        style.map('TButton', background=[('active', '#6a6a6a')])
        style.configure("TCheckbutton", background='#2e2e2e', foreground='white')
        style.configure("TEntry", fieldbackground='#555555', background='#555555', foreground='white', borderwidth=1, relief='solid')
        style.map("TEntry", fieldbackground=[('readonly', '#555555')], foreground=[('readonly', 'white')])
        style.configure("TCombobox", selectbackground='#00c8ff', fieldbackground='#555555', background='#555555', foreground='white')
        style.map('TCombobox', fieldbackground=[('readonly', '#555555')])

        # Style the Text widget and scrollbar manually
        text_bg = '#3e3e3e'
        text_fg = 'white'
        scrollbar_bg = '#555555'
        scrollbar_trough = '#2e2e2e'

        # Required fields - marked with asterisk
        ttk.Label(main_frame, text="* Required fields", font=("Arial", 10, "italic")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Create the form widgets
        row = 1
        
        # CUSTOM_ID3_TAG
        ttk.Label(main_frame, text="* Custom ID3 Tag:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.custom_id3_tag_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.custom_id3_tag_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # POPM_EMAIL
        ttk.Label(main_frame, text="* POPM Email:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.popm_email_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.popm_email_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # GENRE_LIST (with Text widget for better multi-line input)
        ttk.Label(main_frame, text="* Genre List:").grid(row=row, column=0, sticky=tk.W, pady=5)
        genre_frame = ttk.Frame(main_frame, style="TFrame")
        genre_frame.grid(row=row, column=1, sticky=tk.W, pady=5)

        self.genre_list_text = tk.Text(genre_frame, width=38, height=5, bg=text_bg, fg=text_fg, insertbackground='white', borderwidth=1, relief='solid', highlightbackground='#555555', highlightcolor='#00c8ff')
        self.genre_list_text.pack(side=tk.LEFT)
        genre_scrollbar = tk.Scrollbar(genre_frame, command=self.genre_list_text.yview, bg=scrollbar_bg, troughcolor=scrollbar_trough, activebackground='#00c8ff', highlightbackground='#555555')
        genre_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.genre_list_text.config(yscrollcommand=genre_scrollbar.set)
        ttk.Label(main_frame, text="(One genre per line)").grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        # NUM_THREADS
        ttk.Label(main_frame, text="* Number of Threads:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.num_threads_var = tk.IntVar()
        thread_spinner = ttk.Spinbox(main_frame, from_=1, to=16, textvariable=self.num_threads_var, width=5)
        thread_spinner.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # ENGINE_DB_PATH
        ttk.Label(main_frame, text="* Engine DJ Database Path:").grid(row=row, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.engine_db_path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.engine_db_path_var, width=30).pack(side=tk.LEFT)
        ttk.Button(path_frame, text="Browse...", command=lambda: self.browse_file(self.engine_db_path_var, [("Database Files", "*.db"), ("All Files", "*.*")])).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # DJ_POOL_FOLDER_NAME
        ttk.Label(main_frame, text="* DJ Pool Folder:").grid(row=row, column=0, sticky=tk.W, pady=5)
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        self.dj_pool_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.dj_pool_folder_var, width=30).pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Browse...", command=lambda: self.browse_directory(self.dj_pool_folder_var)).pack(side=tk.LEFT, padx=5)
        row += 1
        
        # API_URL
        ttk.Label(main_frame, text="API URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.api_url_var, width=40).grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # API_ENABLED
        self.api_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Enable API Functionality", variable=self.api_enabled_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=self.on_save).pack(side=tk.LEFT, padx=10)
        if not self.first_run:
            ttk.Button(button_frame, text="Cancel", command=self.on_close).pack(side=tk.LEFT, padx=10)
        
    def load_current_settings(self):
        """Load current settings into the form."""
        settings = self.settings_manager.get_all()
        
        self.custom_id3_tag_var.set(settings.get("CUSTOM_ID3_TAG", "PULZWAVE_APPROVED"))
        self.popm_email_var.set(settings.get("POPM_EMAIL", "changeme@pulzwave.com"))
        
        # Load genres into text widget
        genre_list = settings.get("GENRE_LIST", ["House", "Tech House", "Progressive House"])
        self.genre_list_text.delete(1.0, tk.END)
        self.genre_list_text.insert(tk.END, "\n".join(genre_list))
        
        self.num_threads_var.set(settings.get("NUM_THREADS", 4))
        self.engine_db_path_var.set(settings.get("ENGINE_DB_PATH", ""))
        self.dj_pool_folder_var.set(settings.get("DJ_POOL_FOLDER_NAME", ""))
        self.api_url_var.set(settings.get("API_URL", ""))
        self.api_enabled_var.set(settings.get("API_ENABLED", False))
        
    def browse_file(self, var, file_types):
        """Open file browser dialog and set the selected path to var."""
        filename = filedialog.askopenfilename(filetypes=file_types)
        if filename:
            var.set(filename)
            
    def browse_directory(self, var):
        """Open directory browser dialog and set the selected path to var."""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)
    
    def validate_settings(self):
        """Validate the settings before saving."""
        # Check required fields
        custom_id3_tag = self.custom_id3_tag_var.get().strip()
        if not custom_id3_tag:
            messagebox.showerror("Error", "Custom ID3 Tag is required")
            return False
            
        popm_email = self.popm_email_var.get().strip()
        if not popm_email:
            messagebox.showerror("Error", "POPM Email is required")
            return False
            
        genre_text = self.genre_list_text.get(1.0, tk.END).strip()
        if not genre_text:
            messagebox.showerror("Error", "At least one genre is required")
            return False
            
        if self.num_threads_var.get() < 1:
            messagebox.showerror("Error", "Number of threads must be at least 1")
            return False
            
        engine_db_path = self.engine_db_path_var.get().strip()
        if not engine_db_path:
            messagebox.showerror("Error", "Engine DJ Database Path is required")
            return False
            
        dj_pool_folder = self.dj_pool_folder_var.get().strip()
        if not dj_pool_folder:
            messagebox.showerror("Error", "DJ Pool Folder is required")
            return False
            
        return True
    
    def on_save(self):
        """Save the settings and close the dialog."""
        if not self.validate_settings():
            return
            
        # Get genres from text widget
        genre_text = self.genre_list_text.get(1.0, tk.END).strip()
        genre_list = [genre.strip() for genre in genre_text.split('\n') if genre.strip()]
        
        # Update settings
        self.settings_manager.set("CUSTOM_ID3_TAG", self.custom_id3_tag_var.get().strip())
        self.settings_manager.set("POPM_EMAIL", self.popm_email_var.get().strip())
        self.settings_manager.set("GENRE_LIST", genre_list)
        self.settings_manager.set("NUM_THREADS", self.num_threads_var.get())
        self.settings_manager.set("ENGINE_DB_PATH", self.engine_db_path_var.get().strip())
        self.settings_manager.set("DJ_POOL_FOLDER_NAME", self.dj_pool_folder_var.get().strip())
        self.settings_manager.set("API_URL", self.api_url_var.get().strip())
        self.settings_manager.set("API_ENABLED", self.api_enabled_var.get())
        
        # Save settings to file
        if not self.settings_manager.save_settings():
            messagebox.showerror("Error", "Failed to save settings")
            return
            
        # Call the save callback if provided
        if self.on_save_callback:
            self.on_save_callback()
            
        self.destroy()
    
    def on_close(self):
        """Close the dialog without saving."""
        self.destroy()
        
    def on_first_run_close(self):
        """Handle close event during first run."""
        if messagebox.askyesno("Exit Application", "Initial configuration is required to run the application. Do you want to exit?"):
            # Just destroy the dialog, the main app will handle checking if settings exist
            self.destroy()
        else:
            # Keep the dialog open if they don't want to exit
            return
