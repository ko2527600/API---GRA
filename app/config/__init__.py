"""Configuration module - makes app/config a Python package"""
# Import settings from the parent config module
# We need to import from the parent directory's config.py file
import sys
import os

# Get the parent directory (app/)
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import the config module from the parent directory
# We do this by temporarily modifying sys.path
original_path = sys.path.copy()
try:
    # Add the app directory to path so we can import config.py
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    # Now import the Settings class and settings instance from config.py
    # We need to use importlib to avoid circular imports
    import importlib.util
    config_path = os.path.join(app_dir, 'config.py')
    spec = importlib.util.spec_from_file_location("app_config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    settings = config_module.settings
    Settings = config_module.Settings
finally:
    sys.path = original_path

__all__ = ["settings", "Settings"]
