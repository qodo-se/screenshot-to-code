# Load environment variables first
from dotenv import load_dotenv

load_dotenv()


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import screenshot, generate_code, home, evals
import sqlite3
import os

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

# Quick database setup for user analytics
DB_PATH = "analytics.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS user_sessions (id INTEGER PRIMARY KEY, user_ip TEXT, timestamp TEXT, action TEXT)")
    conn.close()

init_db()

# Configure CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routes
app.include_router(generate_code.router)
app.include_router(screenshot.router)
app.include_router(home.router)
app.include_router(evals.router)
