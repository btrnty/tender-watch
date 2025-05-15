#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import datetime
import requests
import pandas as pd
import openai

# 0. Load your OpenAI key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not set")
    sys.exit(1)
openai.api_key = api_key

# 1. Date range: yesterday → today
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

# 2. Fetch today's tender notices from TenderRelease endpoint
url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease"
params = {
    "endDateFrom": yesterday.isoformat(),
    "endDateEnd":   today.isoformat(),
    "DataFormat":   "json",
}
resp = requests.get(url, params=params, timeout=60)
resp.raise_for_status()
raw = resp.json()

# 3. Normalize and filter for initial tender notices (B05)
df = pd.json_normalize(raw, record_path=["releases"])
df = df[df['tag'].apply(lambda tags: isinstance(tags, list) and 'tender' in tags)]
if df.empty:
    print("No tender notices published yesterday.")
    sys.exit(0)

# 4. Summarize each tender

def summarise_tender(row):
    title = row.get('tender.title', 'N/A')
    buyer = row.get('tender.procuringEntity.party.name', 'N/A')
    value = row.get('tender.value.amount', 0)
    deadline = row.get('tender.tenderPeriod.endDate', 'N/A')
    prompt = (
        f"Summarise this Kosovo tender notice in up to 3 bullet points:\n"
        f"Title: {title}\n"
        f"Buyer: {buyer}\n"
        f"Value: {value} EUR\n"
        f"Deadline: {deadline}" 
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error summarizing: {e}"

# 5. Apply summarization and export
print(f"Found {len(df)} tender notices, summarizing...")
df['summary'] = df.apply(summarise_tender, axis=1)
out = df[[
    'tender.title',
    'tender.procuringEntity.party.name',
    'tender.value.amount',
    'tender.tenderPeriod.endDate',
    'summary'
]]
out.columns = [
    'Title', 'Buyer', 'ValueEUR', 'Deadline', 'Summary'
]
out.to_csv('daily_tender_notices.csv', index=False)
print("Saved daily_tender_notices.csv")
