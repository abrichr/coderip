from openai import OpenAI
import os
from loguru import logger
from pprint import pformat
from .config import OPENAI_API_KEY

def get_model_response(prompt: str, model: str = "gpt-4-1106-preview"):
    # ... model response logic ...
