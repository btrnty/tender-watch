#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import datetime
import requests
import pandas as pd

# 1. Compute today’s date
today = datetime.date.today()

# 2. Fetch TenderRelease data (we'll filter by release date)
url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease"
params = {
    "endDateFrom": today.isoformat(),
    "endDateEnd":   today.isoformat(),
    "DataFormat":   "json",
}
resp = requests.get(url, params=params, timeout=60)
resp.raise_for_status()
raw = resp.json()

# 3. Flatten releases and parse release date
df = pd.json_normalize(raw, record_path=["releases"])
df['release_date'] = pd.to_datetime(df['date']).dt.date

# 4. Keep only those published today and tagged 'tender'
df = df[df['release_date'] == today]
df = df[df['tag'].apply(lambda tags: isinstance(tags, list) and 'tender' in tags)]

if df.empty:
    print(f"No tender notices published on {today.isoformat()}.")
    sys.exit(0)

# 5. Select and rename the needed columns
out = df[[
    'tender.title',
    'tender.procuringEntity.party.name',
    'tender.value.amount',
    'tender.tenderPeriod.endDate'
]]
out.columns = ['Title', 'Buyer', 'Value', 'SubmissionDeadline']

# 6. Save to CSV
filename = 'daily_tender_notices.csv'
out.to_csv(filename, index=False)
print(f"Saved {filename} with {len(out)} records for {today.isoformat()}.")
