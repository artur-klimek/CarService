"""
Configuration Module for CarService Application.

This module provides configuration management for the CarService application.
It handles loading, saving, and managing application settings from both
environment variables and configuration files.

Key Features:
    - JSON-based configuration file support
    - Environment variable overrides
    - Default configuration values
    - Logging configuration
    - Server settings
    - Database configuration
    - User management settings

Dependencies:
    - os: For environment variables and file operations
    - json: For configuration file handling
    - pathlib: For path manipulation
    - datetime: For timestamp handling
    - typing: For type hints

Note:
    The configuration system prioritizes values in the following order:
    1. Environment variables
    2. Configuration file values
    3. Default values
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Initialize logger
logger = logging.getLogger(__name__)


class Config:
    """
    Configuration class for the CarService application.

    This class manages all application configuration settings, including
    database, logging, server, and user management settings. It provides
    methods to load, save, and access configuration values.

    Attributes:
        DEFAULT_CONFIG (Dict[str, Any]): Default configuration values
        BASE_DIR (Path): Base directory of the application
        SECRET_KEY (str): Application secret key
        DEBUG (bool): Debug mode flag
        SQLALCHEMY_DATABASE_URI (str): Database connection URI
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): SQLAlchemy tracking flag
        LOG_DIR (Path): Directory for log files
        MAX_LOG_FILES (int): Maximum number of log files to keep
        MAX_LOG_SIZE_MB (int): Maximum size of each log file in MB
        HOST (str): Server host address
        PORT (int): Server port number

    Note:
        Configuration values can be overridden by environment variables
        or a configuration file.
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
            "uri": "sqlite:///carservice.db"
        },
        "secret_key": os.environ.get("SECRET_KEY", "dev"),
        "users": {
            "max_vehicles_per_user": 20,
            "create_default_admin": False,
            "default_admin": {
                "username": "admin",
                "email": "admin@carservice.com",
                "password": "admin123"
            }
        }
    }
    
    # Base directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + str(BASE_DIR / 'app.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging settings
    LOG_DIR = BASE_DIR / 'logs'
    MAX_LOG_FILES = 5
    MAX_LOG_SIZE_MB = 10
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    
    def __init__(self, config_file: str = 'config.json') -> None:
        """
        Initialize configuration from JSON file.

        Args:
            config_file (str): Path to the configuration file.
                Defaults to 'config.json'.

        Note:
            Creates default configuration file if it doesn't exist.
            Loads environment variables and configuration file values.
        """
        logger.info(f"Initializing configuration from {config_file}")
        self.config_file = config_file
        self.config = self._load_config()
        
        # Flask settings
        self.SECRET_KEY = (
            os.environ.get('FLASK_SECRET_KEY') or
            self.get('SECRET_KEY') or
            os.urandom(24)
        )
        self.SQLALCHEMY_DATABASE_URI = self.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///carservice.db'
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = self.get(
            'SQLALCHEMY_TRACK_MODIFICATIONS',
            False
        )
        logger.debug("Flask settings initialized")
        
        # Logging settings
        self.LOG_LEVEL = self.get('LOG_LEVEL', 'INFO')
        self.LOG_FILE = self.get('LOG_FILE', 'carservice.log')
        logger.debug("Logging settings initialized")
        
        # Default users configuration
        self.DEFAULT_ADMIN = self.get('DEFAULT_ADMIN', {
            'enabled': False,
            'username': 'admin',
            'email': 'admin@carservice.com',
            'password': 'admin123'
        })
        
        self.DEFAULT_CLIENT = self.get('DEFAULT_CLIENT', {
            'enabled': False,
            'username': 'client',
            'email': 'client@carservice.com',
            'password': 'client123'
        })
        
        self.DEFAULT_EMPLOYEE = self.get('DEFAULT_EMPLOYEE', {
            'enabled': False,
            'username': 'employee',
            'email': 'employee@carservice.com',
            'password': 'employee123'
        })
        logger.debug("Default user configurations initialized")
        
        logger.info("Configuration initialization completed")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create default if not exists.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
            
        Raises:
            Exception: If there's an error loading the configuration file.
        """
        try:
            if os.path.exists(self.config_file):
                logger.debug(f"Loading configuration from {self.config_file}")
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info("Configuration loaded successfully")
                return config
            else:
                logger.warning(
                    f"Configuration file {self.config_file} not found. "
                    "Creating default configuration."
                )
                with open(self.config_file, 'w') as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=4)
                logger.info("Default configuration file created")
                return self.DEFAULT_CONFIG
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            logger.warning("Using default configuration")
            return self.DEFAULT_CONFIG

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Dict[str, Any]: Logging configuration dictionary containing:
                - log_dir: Directory for log files
                - max_log_files: Maximum number of log files
                - max_log_size_mb: Maximum log file size in MB
        """
        logger.debug("Retrieving logging configuration")
        return {
            'log_dir': str(self.LOG_DIR),
            'max_log_files': self.MAX_LOG_FILES,
            'max_log_size_mb': self.MAX_LOG_SIZE_MB
        }

    def get_server_config(self) -> Dict[str, Any]:
        """
        Get server configuration.
        
        Returns:
            Dict[str, Any]: Server configuration dictionary containing:
                - host: Server host address
                - port: Server port number
        """
        logger.debug("Retrieving server configuration")
        return {
            'host': self.HOST,
            'port': self.PORT
        }

    def get_database_uri(self) -> str:
        """
        Get database URI.
        
        Returns:
            str: Database connection URI
        """
        logger.debug("Retrieving database URI")
        return self.SQLALCHEMY_DATABASE_URI

    def get_secret_key(self) -> str:
        """
        Get secret key.
        
        Returns:
            str: Application secret key
        """
        logger.debug("Retrieving secret key")
        return self.SECRET_KEY

    def get_max_vehicles_per_user(self) -> int:
        """
        Get maximum number of vehicles per user.
        
        Returns:
            int: Maximum number of vehicles allowed per user
        """
        logger.debug("Retrieving max vehicles per user setting")
        return self.config.get(
            "users", {}
        ).get(
            "max_vehicles_per_user",
            self.DEFAULT_CONFIG["users"]["max_vehicles_per_user"]
        )

    def should_create_default_admin(self) -> bool:
        """
        Check if default admin account should be created.
        
        Returns:
            bool: True if default admin should be created, False otherwise
        """
        logger.debug("Checking default admin creation setting")
        return self.config.get(
            "users", {}
        ).get(
            "create_default_admin",
            self.DEFAULT_CONFIG["users"]["create_default_admin"]
        )

    def get_default_admin_config(self) -> Dict[str, str]:
        """
        Get default admin account configuration.
        
        Returns:
            Dict[str, str]: Default admin configuration containing:
                - username: Admin username
                - email: Admin email
                - password: Admin password
        """
        logger.debug("Retrieving default admin configuration")
        return self.config.get(
            "users", {}
        ).get(
            "default_admin",
            self.DEFAULT_CONFIG["users"]["default_admin"]
        )

    def initialize_config(self) -> None:
        """
        Initialize configuration.
        
        Creates necessary directories and performs initial setup.
        """
        logger.info("Initializing configuration")
        try:
            self.LOG_DIR.mkdir(exist_ok=True)
            logger.debug(f"Log directory created/verified: {self.LOG_DIR}")
        except Exception as e:
            logger.error(f"Error creating log directory: {str(e)}")
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key (str): Configuration key to retrieve
            default (Any, optional): Default value if key not found.
                Defaults to None.
                
        Returns:
            Any: Configuration value or default if not found
        """
        logger.debug(f"Retrieving configuration value for key: {key}")
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value and save to file.
        
        Args:
            key (str): Configuration key to set
            value (Any): Value to set for the key
            
        Note:
            Changes are immediately saved to the configuration file.
        """
        logger.info(f"Setting configuration value for key: {key}")
        try:
            self.config[key] = value
            self._save_config()
            logger.debug("Configuration updated and saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise

    def _save_config(self) -> None:
        """
        Save configuration to JSON file.
        
        Raises:
            Exception: If there's an error saving the configuration file.
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.debug(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration file: {str(e)}")
            raise

    def get_default_admin(self) -> Dict[str, Any]:
        """
        Get default admin configuration.
        
        Returns:
            Dict[str, Any]: Default admin configuration
        """
        logger.debug("Retrieving default admin settings")
        return self.DEFAULT_ADMIN

    def get_default_client(self) -> Dict[str, Any]:
        """
        Get default client configuration.
        
        Returns:
            Dict[str, Any]: Default client configuration
        """
        logger.debug("Retrieving default client settings")
        return self.DEFAULT_CLIENT

    def get_default_employee(self) -> Dict[str, Any]:
        """
        Get default employee configuration.
        
        Returns:
            Dict[str, Any]: Default employee configuration
        """
        logger.debug("Retrieving default employee settings")
        return self.DEFAULT_EMPLOYEE

    def is_default_admin_enabled(self) -> bool:
        """
        Check if default admin is enabled.
        
        Returns:
            bool: True if default admin is enabled, False otherwise
        """
        logger.debug("Checking if default admin is enabled")
        return self.DEFAULT_ADMIN.get('enabled', False)

    def is_default_client_enabled(self) -> bool:
        """
        Check if default client is enabled.
        
        Returns:
            bool: True if default client is enabled, False otherwise
        """
        logger.debug("Checking if default client is enabled")
        return self.DEFAULT_CLIENT.get('enabled', False)

    def is_default_employee_enabled(self) -> bool:
        """
        Check if default employee is enabled.
        
        Returns:
            bool: True if default employee is enabled, False otherwise
        """
        logger.debug("Checking if default employee is enabled")
        return self.DEFAULT_EMPLOYEE.get('enabled', False)
