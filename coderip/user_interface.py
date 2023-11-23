from .models import TagData
from .openai_client import get_model_response
from .monitor import execute_command
from loguru import logger
import time

def user_interaction_interface(tag_data: TagData, data_lock):
    # ... user interaction interface logic ...
