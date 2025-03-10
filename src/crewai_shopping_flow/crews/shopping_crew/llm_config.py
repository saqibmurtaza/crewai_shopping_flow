from crewai import LLM
from dotenv import load_dotenv
import os

load_dotenv()

llm = LLM(
    model="gemini/gemini-1.5-flash",
    temperature=0.5,
    api_key=os.getenv("GEMINI_API_KEY"),
)
