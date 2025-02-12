"""
Structured logging utilities for consistent log formatting
"""
from datetime import datetime
from typing import Any, Dict

def structured_log(message: str, **kwargs) -> Dict[str, Any]:
    """
    Creates a structured log message with consistent formatting.
    
    Args:
        message: The log message
        **kwargs: Additional context parameters to include in the log
        
    Returns:
        Dict containing the structured log message
    """
    log_data = {
        'message': message,
        'timestamp': datetime.utcnow().isoformat(),
        'context': kwargs
    }
    return log_data

__all__ = ['structured_log']
