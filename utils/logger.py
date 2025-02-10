import logging
import sys
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

class StructuredMessage:
    def __init__(self, message, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def __str__(self):
        return json.dumps({
            'message': self.message,
            'timestamp': datetime.utcnow().isoformat(),
            'context': self.kwargs
        })

class StructuredLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, **kwargs):
        if isinstance(msg, StructuredMessage):
            super()._log(level, msg, args, exc_info, extra, stack_info)
        else:
            msg = StructuredMessage(msg, **kwargs if kwargs else {})
            super()._log(level, msg, args, exc_info, extra, stack_info)

class Logger:
    _instance = None
    _correlation_id = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        # Register the custom logger class
        logging.setLoggerClass(StructuredLogger)
        self.logger = logging.getLogger('TimesheetTracker')

        # Get log level from environment variable, default to INFO
        log_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
        self.logger.setLevel(getattr(logging, log_level))

        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            filename=log_dir / f'timesheet_tracker_{datetime.now().strftime("%Y%m%d")}.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, log_level))

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))

        # Custom JSON formatter
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record, self.datefmt),
                    'level': record.levelname,
                    'correlation_id': Logger._correlation_id or 'undefined',
                    'logger': record.name,
                }

                if isinstance(record.msg, StructuredMessage):
                    structured_data = json.loads(str(record.msg))
                    log_data.update(structured_data)
                else:
                    log_data['message'] = record.getMessage()

                if record.exc_info:
                    log_data['exception'] = self.formatException(record.exc_info)

                return json.dumps(log_data)

        formatter = JsonFormatter()
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def set_correlation_id(self, correlation_id=None):
        """Set a correlation ID for request tracking"""
        Logger._correlation_id = correlation_id or str(uuid.uuid4())
        return Logger._correlation_id

    def get_correlation_id(self):
        """Get the current correlation ID"""
        return Logger._correlation_id

    def get_logger(self):
        return self.logger

# Convenience function for structured logging
def structured_log(message, **kwargs):
    return StructuredMessage(message, **kwargs)