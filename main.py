# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import metrics, backtest, generate, compare, run_generated

app = FastAPI()

# Allow frontend to access this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(metrics.router)
app.include_router(backtest.router)
app.include_router(generate.router)
app.include_router(compare.router)
app.include_router(run_generated.router)
