"""Configuration constants for the DJ Library Organizer application."""

# --- Application Constants ---
APP_TITLE = "PulzWave's DJ Library Organizer 0.01"
WINDOW_GEOMETRY = "1200x800"
CUSTOM_ID3_VALUE = "true"
RATING_TXXX_DESC = "RATING"
API_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

# --- Default values for settings (Will be overridden by SettingsManager) ---
# These will only be used if the settings file doesn't exist and the user cancels the initial setup
DEFAULT_CUSTOM_ID3_TAG = "PULZWAVE_APPROVED"
DEFAULT_POPM_EMAIL = "changeme@pulzwave.com"
DEFAULT_GENRE_LIST = ["House", "Afro House", "Deep House", "Melodic House", "Minimal House", "Tech House", "Progressive House", "Funky House", "Big Room"]
DEFAULT_NUM_THREADS = 4
DEFAULT_ENGINE_DB_PATH = ""
DEFAULT_DJ_POOL_FOLDER_NAME = ""
DEFAULT_API_URL = ""
DEFAULT_API_ENABLED = False
