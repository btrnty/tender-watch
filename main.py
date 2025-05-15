#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os, sys, datetime, requests, pandas as pd

# 0. (Optional) load OPENAI_API_KEY if you later re-enable summaries
# import openai; openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Compute today’s date
today = datetime.date.today().isoformat()

# 2. Fetch TenderRelease data
url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease"
params = {
    "endDateFrom": today,
    "endDateEnd":   today,
    "DataFormat":   "json",
}
resp = requests.get(url, params=params, timeout=60)
resp.raise_for_status()
raw = resp.json()

# 3. Flatten and filter
df = pd.json_normalize(raw, record_path=["releases"])

# — only those published *today* —
df = df[df["date"].str.startswith(today)]

# — only initial “tender” notices (B05) —
df = df[df["tag"].apply(lambda tags: isinstance(tags, list) and "tender" in tags)]

if df.empty:
    print("No tender notices published today.")
    sys.exit(0)

# 4. Pick and rename the columns we need
out = df[[
    "tender.title",
    "tender.procuringEntity.party.name",
    "tender.value.amount",
    "tender.tenderPeriod.endDate"
]]
out.columns = ["Title", "Buyer", "Value", "SubmissionDeadline"]

# 5. Save CSV
out.to_csv("daily_tender_notices.csv", index=False)
print(f"Saved daily_tender_notices.csv with {len(out)} rows.")

