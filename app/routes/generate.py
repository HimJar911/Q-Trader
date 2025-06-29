# app/routes/generate.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY not found.")

client = OpenAI(api_key=api_key)

router = APIRouter()

class StrategyRequest(BaseModel):
    objective: str  # e.g. "momentum strategy for NASDAQ tech stocks"

@router.post("/generate-strategy")
def generate_strategy(payload: StrategyRequest):
    try:
        prompt = f"""
You're a senior quantitative strategist. Generate a robust Python trading strategy for this objective:

Objective: "{payload.objective}"

The output must be valid Python code with:
- A function named `strategy(df)`
- It should take a pandas DataFrame with a 'Close' column
- It must return a pandas Series named 'signal' (1 = buy, 0 = hold, -1 = sell)
- Use vectorized operations, not apply()
- No markdown, no explanations, just clean code.
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        code = response.choices[0].message.content.strip()
        return {"code": code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ OpenAI Error: {str(e)}")
