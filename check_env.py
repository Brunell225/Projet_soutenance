import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
dotenv_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=dotenv_path)

print("\n📦 Variables .env lues par Django :\n")
print("DB_NAME     =", os.getenv("DB_NAME"))
print("DB_USER     =", os.getenv("DB_USER"))
print("DB_PASSWORD =", os.getenv("DB_PASSWORD"))
print("DB_HOST     =", os.getenv("DB_HOST"))
print("DB_PORT     =", os.getenv("DB_PORT"))
