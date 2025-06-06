"""
Configuration Module for CarService Application.

This module manages the application's configuration settings, including logging,
server parameters, and other application-specific settings. It provides a
centralized configuration management system that supports both file-based and
default configurations.

Key Features:
    - File-based configuration management
    - Default configuration fallback
    - Logging configuration
    - Server configuration
    - Configuration persistence
    - Type-safe configuration access

Dependencies:
    - os: File system operations
    - json: Configuration file handling
    - pathlib: Path manipulation
    - typing: Type hints

Note:
    The configuration system prioritizes file-based settings over defaults.
    If the configuration file doesn't exist, it will be created with default
    values. All configuration changes are persisted to the file.
"""

import logging
import os
from typing import Dict, Any, Optional
import json
from pathlib import Path


# Initialize logger
logger = logging.getLogger(__name__)


class Config:
    """
    Configuration management class for the CarService application.

    This class handles loading, managing, and providing access to application
    configuration settings. It supports both file-based configuration and
    default values, with proper type safety and error handling.

    Attributes:
        DEFAULT_CONFIG (Dict[str, Any]): Default configuration values
        config_path (str): Path to the configuration file
        config (Dict[str, Any]): Current configuration dictionary

    The default configuration includes:
        - Logging settings (level, directory, file limits)
        - Server settings (host, port, debug mode)
        - Other application-specific settings

    Methods:
        __init__: Initialize configuration
        _load_config: Load configuration from file
        get_logging_config: Get logging settings
        get_server_config: Get server settings
        get_database_uri: Get database connection URI
        get_secret_key: Get application secret key
        should_create_default_admin: Check if default admin account should be created
        get_default_admin_config: Get default admin account configuration
        save_config: Save current configuration
        update_config: Update configuration values
    """
    
    # Default configuration values
    DEFAULT_CONFIG: Dict[str, Any] = {
        "logging": {
            "level": "INFO",
            "log_dir": "logs",
            "max_log_files": 5,
            "max_log_size_mb": 10
        },
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False
        },
        "database": {
            "uri": "sqlite:///carservice.db",
            "track_modifications": False
        },
        "security": {
            "secret_key": "dev-secret-key",  # Should be changed in production
            "session_lifetime": 3600  # 1 hour in seconds
        },
        "admin": {
            "create_default": True,
            "username": "admin",
            "email": "admin@carservice.com",
            "password": "admin123"  # Should be changed in production
        }
    }
    
    def __init__(self, config_path: str = "config.json") -> None:
        """
        Initialize configuration from file or use defaults.

        This method initializes the configuration system by either loading
        existing configuration from a file or creating a new configuration
        file with default values.

        Args:
            config_path (str): Path to the configuration file.
                             Defaults to "config.json".

        Note:
            If the configuration file doesn't exist, it will be created
            with default values. The file path can be relative or absolute.
        """
        self.config_path = config_path
        logger.info(f"Initializing configuration from: {config_path}")
        self.config = self._load_config()
        logger.debug(f"Configuration loaded: {self.config}")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if not exists.

        This method attempts to load the configuration from the specified
        file. If the file doesn't exist, it creates a new file with default
        values. If there's an error loading the file, it falls back to
        default values.

        Returns:
            Dict[str, Any]: Configuration dictionary containing all settings

        Note:
            The method handles file I/O errors gracefully and logs any
            issues that occur during the loading process.
        """
        try:
            if os.path.exists(self.config_path):
                logger.debug(f"Loading configuration from: {self.config_path}")
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info("Configuration loaded successfully")
                return config
            else:
                logger.warning(
                    f"Configuration file not found: {self.config_path}. "
                    "Creating with default values."
                )
                # Create default config file
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=4)
                logger.info(
                    f"Default configuration created at: {self.config_path}"
                )
                return self.DEFAULT_CONFIG
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON in configuration file: {self.config_path}. "
                f"Error: {str(e)}"
            )
            return self.DEFAULT_CONFIG
        except Exception as e:
            logger.error(
                f"Error loading configuration: {str(e)}. "
                "Using default configuration."
            )
            return self.DEFAULT_CONFIG
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration settings.

        Returns the logging-specific configuration settings, including
        log level, directory, and file management parameters.

        Returns:
            Dict[str, Any]: Dictionary containing logging configuration:
                - level (str): Logging level (e.g., "INFO", "DEBUG")
                - log_dir (str): Directory for log files
                - max_log_files (int): Maximum number of log files to keep
                - max_log_size_mb (int): Maximum size of each log file in MB
        """
        logging_config = self.config.get(
            "logging",
            self.DEFAULT_CONFIG["logging"]
        )
        logger.debug(f"Retrieved logging configuration: {logging_config}")
        return logging_config
    
    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration settings.

        Returns the server-specific configuration settings, including
        host, port, and debug mode parameters.

        Returns:
            Dict[str, Any]: Dictionary containing server configuration:
                - host (str): Server host address
                - port (int): Server port number
                - debug (bool): Debug mode flag
        """
        server_config = self.config.get(
            "server",
            self.DEFAULT_CONFIG["server"]
        )
        logger.debug(f"Retrieved server configuration: {server_config}")
        return server_config
    
    def get_database_uri(self) -> str:
        """
        Get database connection URI.

        Returns the database connection string from the configuration.

        Returns:
            str: Database connection URI

        Note:
            Falls back to default SQLite URI if not configured.
        """
        db_config = self.config.get(
            "database",
            self.DEFAULT_CONFIG["database"]
        )
        uri = db_config.get("uri", self.DEFAULT_CONFIG["database"]["uri"])
        logger.debug(f"Retrieved database URI: {uri}")
        return uri
    
    def get_secret_key(self) -> str:
        """
        Get application secret key.

        Returns the secret key used for session management and security.

        Returns:
            str: Application secret key

        Note:
            Falls back to default development key if not configured.
            Should be changed in production.
        """
        security_config = self.config.get(
            "security",
            self.DEFAULT_CONFIG["security"]
        )
        key = security_config.get(
            "secret_key",
            self.DEFAULT_CONFIG["security"]["secret_key"]
        )
        logger.debug("Retrieved secret key")
        return key
    
    def should_create_default_admin(self) -> bool:
        """
        Check if default admin account should be created.

        Returns:
            bool: True if default admin should be created, False otherwise

        Note:
            This setting is typically used during initial application setup.
        """
        admin_config = self.config.get(
            "admin",
            self.DEFAULT_CONFIG["admin"]
        )
        should_create = admin_config.get(
            "create_default",
            self.DEFAULT_CONFIG["admin"]["create_default"]
        )
        logger.debug(f"Default admin creation enabled: {should_create}")
        return should_create
    
    def get_default_admin_config(self) -> Dict[str, str]:
        """
        Get default admin account configuration.

        Returns:
            Dict[str, str]: Dictionary containing admin account settings:
                - username (str): Admin username
                - email (str): Admin email
                - password (str): Admin password

        Note:
            These are default values and should be changed in production.
        """
        admin_config = self.config.get(
            "admin",
            self.DEFAULT_CONFIG["admin"]
        )
        config = {
            "username": admin_config.get(
                "username",
                self.DEFAULT_CONFIG["admin"]["username"]
            ),
            "email": admin_config.get(
                "email",
                self.DEFAULT_CONFIG["admin"]["email"]
            ),
            "password": admin_config.get(
                "password",
                self.DEFAULT_CONFIG["admin"]["password"]
            )
        }
        logger.debug("Retrieved default admin configuration")
        return config
    
    def save_config(self) -> None:
        """
        Save current configuration to file.

        This method persists the current configuration to the configuration
        file. It handles file I/O errors and logs the operation.

        Raises:
            IOError: If the configuration file cannot be written
            json.JSONDecodeError: If the configuration cannot be serialized
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with new values.

        This method updates the current configuration with new values and
        saves the changes to the configuration file.

        Args:
            updates (Dict[str, Any]): Dictionary containing configuration updates

        Raises:
            ValueError: If the updates dictionary is invalid
            IOError: If the configuration cannot be saved

        Note:
            The updates dictionary should follow the same structure as the
            configuration. Only specified values will be updated.
        """
        try:
            logger.debug(f"Updating configuration with: {updates}")
            self._deep_update(self.config, updates)
            self.save_config()
            logger.info("Configuration updated successfully")
        except Exception as e:
            logger.error(f"Failed to update configuration: {str(e)}")
            raise
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Recursively update a dictionary with another dictionary.

        This helper method performs a deep update of the configuration
        dictionary, preserving nested structures.

        Args:
            base (Dict[str, Any]): Base dictionary to update
            updates (Dict[str, Any]): Dictionary containing updates

        Raises:
            ValueError: If the updates structure is invalid
        """
        for key, value in updates.items():
            if (
                key in base and
                isinstance(base[key], dict) and
                isinstance(value, dict)
            ):
                self._deep_update(base[key], value)
            else:
                base[key] = value
