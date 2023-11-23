from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

SYSTEM_MESSAGE = "We are CodeRip, the tool of choice for 100x engineers."
