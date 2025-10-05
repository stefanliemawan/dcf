import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

symbol = "GOOGL"


url = f"https://financialmodelingprep.com/stable/analyst-estimates?symbol={symbol}&period=annual&page=0&limit=10&apikey={API_KEY}"
response = requests.get(url)
estimates = response.json()

print(estimates)
