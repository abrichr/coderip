from watchdog.events import FileSystemEventHandler
from .models import CodeSection, File
from loguru import logger
import os
import re

class TagFinder(FileSystemEventHandler):
    def __init__(self, tag_data, data_lock):
        logger.info(f"Initializing TagFinder {tag_data=} {data_lock=}")
        super().__init__()
        self.tag_data = tag_data
        self.data_lock = data_lock

    # ... rest of the TagFinder class ...
