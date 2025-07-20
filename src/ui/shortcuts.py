"""Keyboard shortcut management."""

from ..utils.logger import get_logger

logger = get_logger()


class KeyboardShortcutManager:
    """Manages keyboard shortcuts for the application."""
    
    def __init__(self, master):
        """
        Initialize keyboard shortcut manager.
        
        Args:
            master: Root tkinter window
        """
        self.master = master
        self.callbacks = {}
    
    def register_callback(self, key, callback, description=""):
        """
        Register a keyboard shortcut callback.
        
        Args:
            key (str): Key combination (e.g., '<Up>', '<space>')
            callback: Function to call when key is pressed
            description (str): Description of what the shortcut does
        """
        self.callbacks[key] = {
            'callback': callback,
            'description': description
        }
        def handler(event=None):
            logger.debug(f"Shortcut triggered: {key}")
            callback()
            return "break"
        self.master.bind_all(key, handler, add='+')
    
    def register_conditional_callback(self, key, callback, condition_func, description=""):
        """
        Register a conditional keyboard shortcut callback.
        
        Args:
            key (str): Key combination
            callback: Function to call when key is pressed
            condition_func: Function that returns True if callback should execute
            description (str): Description of what the shortcut does
        """
        def conditional_wrapper(event=None):
            logger.debug(f"Conditional shortcut attempted: {key}")
            condition_result = condition_func()
            logger.debug(f"Condition result for {key}: {condition_result}")
            if condition_result:
                logger.debug(f"Condition met, executing callback for: {key}")
                callback()
            else:
                logger.debug(f"Condition not met for: {key}")
            return "break"
        
        self.callbacks[key] = {
            'callback': conditional_wrapper,
            'description': description
        }
        self.master.bind_all(key, conditional_wrapper, add='+')
    
    def register_key_handler(self, key, handler, description=""):
        """
        Register a key handler that receives the event.
        
        Args:
            key (str): Key combination
            handler: Function to call with event parameter
            description (str): Description of what the shortcut does
        """
        self.callbacks[key] = {
            'callback': handler,
            'description': description
        }
        def debug_handler(event=None):
            return handler(event)
        self.master.bind_all(key, debug_handler, add='+')
    
    def unregister_callback(self, key):
        """
        Unregister a keyboard shortcut.
        
        Args:
            key (str): Key combination to unregister
        """
        if key in self.callbacks:
            self.master.unbind_all(key)
            del self.callbacks[key]
    
    def get_shortcuts_info(self):
        """
        Get information about registered shortcuts.
        
        Returns:
            dict: Dictionary of shortcuts and their descriptions
        """
        return {key: info['description'] for key, info in self.callbacks.items()}
    
    def setup_default_shortcuts(self, app_instance):
        """
        Set up default keyboard shortcuts for the application.
        
        Args:
            app_instance: The main application instance
        """
        # Navigation and actions
        self.register_conditional_callback(
            '<Up>',
            app_instance.keep_file,
            app_instance.can_keep_file,
            "Keep file and save metadata"
        )
        
        self.register_conditional_callback(
            '<Down>',
            app_instance.delete_file,
            app_instance.can_delete_file,
            "Delete file"
        )
        
        # Playback controls
        self.register_callback(
            '<space>',
            app_instance.toggle_pause,
            "Toggle pause/play"
        )
        
        self.register_callback(
            '<Right>',
            app_instance.seek_forward,
            "Seek forward"
        )
        
        self.register_callback(
            '<Left>',
            app_instance.seek_backward,
            "Seek backward"
        )
        
        # Rating shortcuts
        for i in range(1, 6):
            self.register_key_handler(
                f'<KeyPress-{i}>',
                app_instance.set_rating_from_key,
                f"Set rating to {i}"
            )
        
        # Debug shortcut
        self.register_callback(
            '<F1>',
            app_instance.debug_shortcuts,
            "Debug shortcut information"
        )
    
    def cleanup(self):
        """Clean up all registered shortcuts."""
        for key in list(self.callbacks.keys()):
            self.unregister_callback(key)
