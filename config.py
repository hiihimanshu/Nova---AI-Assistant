import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_NAME = "NOVA"
WAKE_WORD = "nova"
VOICE_LANG = "en"

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    raise RuntimeError("PERPLEXITY_API_KEY not found in .env file")
