"""
Logging configuration module.
"""
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, level=logging.INFO):
    """Setup logger with console and file handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Console handler - without emojis for Windows
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # File handler - can use emojis
        log_file = log_dir / f'trading_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # Formatter for console (no emojis)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Formatter for file (with emojis)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger

# Helper function for Windows console output without emojis
def safe_print(message: str):
    """Print message without emojis for Windows console."""
    # Replace common emojis with text
    replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARN]',
        '📈': '[PRICE]',
        '🔔': '[SIGNAL]',
        '💰': '[TRADE]',
        '📊': '[CANDLE]',
        '🔌': '[CONN]',
        '💹': '[POS]'
    }
    for emoji, text in replacements.items():
        message = message.replace(emoji, text)
    print(message)