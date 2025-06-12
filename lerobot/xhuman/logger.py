import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from datetime import datetime

custom_theme = Theme({
    "debug": "cyan",
    "info": "green",
    "warning": "yellow",
    "error": "red",
    "critical": "bold magenta"
})

console = Console(theme=custom_theme)

class RichLoggerHandler(logging.Handler):
    def emit(self, record):
        log_time = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname.lower()

        message = Text(f"[{log_time}] [{record.levelname}] {record.getMessage()}", style=level)
        panel = Panel(message, border_style=level, expand=False)
        console.print(panel)

def get_rich_logger(name="RichLogger"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = RichLoggerHandler()
    logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = get_rich_logger(name="XHuman")

