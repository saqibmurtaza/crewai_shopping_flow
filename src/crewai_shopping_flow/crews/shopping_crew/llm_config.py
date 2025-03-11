from crewai import LLM
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

llm = LLM(
    model="gemini/gemini-1.5-flash",
    temperature=0.5,
    api_key=api_key,
    timeout=30  # Add a timeout value
)
