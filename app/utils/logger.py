"""
Logging module for the CarService application.

This module provides a centralized logging system with the following features:
- Singleton logger instance
- Log file rotation
- Console and file output
- Configurable log levels
- Automatic log cleanup
- Timestamp-based log files

The logger supports multiple output handlers:
- File handler with rotation based on size
- Console handler for immediate feedback
- Customizable log formats for different handlers

Dependencies:
    - logging: Python's built-in logging module
    - logging.handlers: For log rotation functionality
    - pathlib: For cross-platform path handling
    - datetime: For timestamp-based log files

Note:
    This module implements the Singleton pattern to ensure
    a single logger instance throughout the application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, List
from pathlib import Path
from datetime import datetime

class Logger:
    """
    Logger class for managing application logs.

    This class implements a singleton pattern to ensure a single logger
    instance throughout the application. It provides methods for:
    - Logger setup and configuration
    - Log file rotation
    - Old log cleanup
    - Multiple output handlers

    Attributes:
        _instance (Optional[Logger]): Singleton instance
        _initialized (bool): Initialization flag
        logger (logging.Logger): Configured logger instance

    Note:
        The logger is configured with both file and console handlers
        by default, with different formatters for each.
    """
    
    _instance: Optional['Logger'] = None
    
    def __new__(cls) -> 'Logger':
        """
        Create or return the singleton logger instance.

        This method implements the singleton pattern to ensure
        only one logger instance exists throughout the application.

        Returns:
            Logger: The singleton logger instance

        Note:
            This method is called before __init__ and ensures
            that only one logger instance is created.
        """
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
            logging.debug("Creating new Logger instance")
        return cls._instance
    
    def __init__(self) -> None:
        """
        Initialize the logger if not already initialized.

        This method sets up the basic logger configuration if
        it hasn't been initialized before. It creates a logger
        with the name 'CarService' and sets the default level
        to INFO.

        Note:
            Due to the singleton pattern, this method only
            performs initialization once, even if called multiple times.
        """
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.logger = logging.getLogger('CarService')
        self.logger.setLevel(logging.INFO)
        logging.debug("Logger initialized with default configuration")
        
    def setup(self, log_dir: str, level: str = 'INFO', 
              max_log_files: int = 5, max_log_size_mb: int = 10) -> None:
        """
        Set up the logger with specified configuration.

        This method configures the logger with:
        - File handler with rotation
        - Console handler
        - Custom formatters
        - Specified log level
        - Log directory creation

        Args:
            log_dir (str): Directory to store log files
            level (str, optional): Logging level. Defaults to 'INFO'
            max_log_files (int, optional): Maximum number of log files to keep.
                Defaults to 5
            max_log_size_mb (int, optional): Maximum size of each log file in MB.
                Defaults to 10

        Raises:
            OSError: If log directory cannot be created
            ValueError: If invalid logging level is specified

        Note:
            This method clears any existing handlers before
            applying the new configuration.
        """
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            logging.debug(f"Log directory ensured at: {log_path}")
            
            # Set logging level
            try:
                level = getattr(logging, level.upper(), logging.INFO)
                self.logger.setLevel(level)
                logging.debug(f"Log level set to: {level}")
            except AttributeError:
                logging.warning(f"Invalid log level '{level}', using INFO")
                level = logging.INFO
                self.logger.setLevel(level)
            
            # Clear existing handlers
            self.logger.handlers.clear()
            logging.debug("Cleared existing log handlers")
            
            # Create formatters
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - '
                '%(filename)s:%(lineno)d - %(message)s'
            )
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            
            # File handler with rotation
            log_file = log_path / f'carservice_{datetime.now().strftime("%Y%m%d")}.log'
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_log_size_mb * 1024 * 1024,
                backupCount=max_log_files,
                encoding='utf-8'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            logging.debug(f"Added file handler: {log_file}")
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
            logging.debug("Added console handler")
            
            # Log successful setup
            self.logger.info(
                f"Logger configured - Level: {logging.getLevelName(level)}, "
                f"Max files: {max_log_files}, Max size: {max_log_size_mb}MB"
            )
        except Exception as e:
            logging.error(f"Error setting up logger: {str(e)}")
            raise
        
    def cleanup_old_logs(self, log_dir: str, max_log_files: int) -> None:
        """
        Clean up old log files keeping only the specified number of most recent ones.

        This method:
        - Finds all log files in the specified directory
        - Sorts them by modification time
        - Removes excess files beyond the specified limit
        - Logs any errors during cleanup

        Args:
            log_dir (str): Directory containing log files
            max_log_files (int): Maximum number of log files to keep

        Note:
            Files are sorted by modification time, with the most
            recent files being kept. The method handles errors
            gracefully and logs any issues encountered.
        """
        try:
            log_path = Path(log_dir)
            if not log_path.exists():
                logging.warning(f"Log directory does not exist: {log_dir}")
                return
                
            log_files: List[Path] = sorted(
                [f for f in log_path.glob('carservice_*.log')],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            logging.debug(
                f"Found {len(log_files)} log files, "
                f"keeping {min(max_log_files, len(log_files))} most recent"
            )
            
            # Remove excess log files
            for old_file in log_files[max_log_files:]:
                try:
                    old_file.unlink()
                    logging.debug(f"Removed old log file: {old_file}")
                except Exception as e:
                    self.logger.error(
                        f"Error removing old log file {old_file}: {str(e)}"
                    )
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {str(e)}")
                
    def get_logger(self) -> logging.Logger:
        """
        Get the configured logger instance.

        Returns:
            logging.Logger: The configured logger instance

        Note:
            This method should be used to access the logger
            throughout the application to ensure consistent
            logging configuration.
        """
        if not self._initialized:
            logging.warning("Logger accessed before initialization")
        return self.logger
