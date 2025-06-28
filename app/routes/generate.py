# app/routes/generate.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# Load OpenAI key from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not found in .env file.")

client = OpenAI(api_key=api_key)

class StrategyRequest(BaseModel):
    objective: str  # Example: "momentum strategy for NASDAQ tech stocks"

@router.post("/generate-strategy")
def generate_strategy(payload: StrategyRequest):
    try:
        prompt = f"""
You're a senior quantitative strategist. Generate a detailed Python backtesting strategy based on this objective:

Objective: "{payload.objective}"

Give the response as clean Python code only, with no explanations or markdown. It should define a function that takes a DataFrame with a 'Close' column and returns a 'signal' column (1 for buy, 0 for hold, -1 for sell).
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        code = response.choices[0].message.content.strip()
        return {"code": code}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
