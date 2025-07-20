"""UI styling and theme configuration."""

import tkinter as tk
from tkinter import ttk


class UIStyleManager:
    """Manages UI styling and themes."""
    
    def __init__(self, master):
        """
        Initialize the style manager.
        
        Args:
            master: The root tkinter window
        """
        self.master = master
        self.style = ttk.Style(master)
    
    def apply_dark_theme(self):
        """Apply dark theme styling to the application."""
        self.style.theme_use('clam')
        
        # Base styles
        self.style.configure(
            '.', 
            font=('Helvetica', 10), 
            background='#2e2e2e', 
            foreground='white'
        )
        
        # Frame styles
        self.style.configure('TFrame', background='#2e2e2e')
        
        # Button styles
        self.style.configure(
            'TButton',
            font=('Helvetica', 12, 'bold'),
            padding=10,
            background='#4a4a4a',
            foreground='white'
        )
        self.style.map('TButton', background=[('active', '#6a6a6a')])
        
        # Label styles
        self.style.configure(
            'Header.TLabel',
            font=('Helvetica', 14, 'bold')
        )
        self.style.configure(
            'Status.TLabel',
            font=('Helvetica', 9)
        )
        self.style.configure(
            'Info.TLabel',
            font=('Helvetica', 10),
            foreground='cyan'
        )
        
        # Progress bar style
        self.style.configure(
            'Blue.Horizontal.TProgressbar',
            background='#00c8ff'
        )
        
        # Entry styles
        self.style.configure(
            'TEntry',
            fieldbackground='#555555',
            background='#555555',
            foreground='white',
            borderwidth=1,
            relief='solid'
        )
        
        # Combobox styles
        self._configure_combobox_styles()
    
    def _configure_combobox_styles(self):
        """Configure combobox-specific styles."""
        # Combobox listbox styling
        self.master.option_add('*TCombobox*Listbox*Background', '#555555')
        self.master.option_add('*TCombobox*Listbox*Foreground', 'white')
        self.master.option_add('*TCombobox*Listbox*selectBackground', '#00c8ff')
        self.master.option_add('*TCombobox*Listbox*selectForeground', 'black')
        
        # Main combobox style
        self.style.configure(
            'TCombobox',
            selectbackground='#00c8ff',
            fieldbackground='#555555',
            background='#555555',
            foreground='white'
        )
        self.style.map('TCombobox', fieldbackground=[('readonly', '#555555')])


class RadioButtonGroup:
    """Creates a group of radio buttons with consistent styling."""
    
    def __init__(self, parent, variable, values, labels=None, clear_button=False):
        """
        Initialize radio button group.
        
        Args:
            parent: Parent widget
            variable: Tkinter variable to bind to
            values: List of values for radio buttons
            labels: List of labels (if different from values)
            clear_button: Whether to add a clear button
        """
        self.parent = parent
        self.variable = variable
        self.values = values
        self.labels = labels or [str(v) for v in values]
        self.buttons = []
        
        self._create_buttons()
        
        if clear_button:
            self._add_clear_button()
    
    def _create_buttons(self):
        """Create the radio buttons."""
        for i, (value, label) in enumerate(zip(self.values, self.labels)):
            rb = tk.Radiobutton(
                self.parent,
                text=label,
                variable=self.variable,
                value=value,
                bg='#2e2e2e',
                fg='white',
                selectcolor='#4a4a4a',
                activebackground='#2e2e2e',
                activeforeground='white',
                borderwidth=0,
                highlightthickness=0
            )
            rb.pack(side=tk.LEFT)
            self.buttons.append(rb)
    
    def _add_clear_button(self):
        """Add a clear button to reset the selection."""
        clear_btn = tk.Button(
            self.parent,
            text="Clear",
            command=lambda: self.variable.set(0),
            bg='#4a4a4a',
            fg='white',
            relief='flat',
            padx=5
        )
        clear_btn.pack(side=tk.LEFT, padx=10)
