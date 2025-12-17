import os
from dotenv import load_dotenv
load_dotenv(override=True)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(api_key)
