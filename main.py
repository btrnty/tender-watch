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

def fetch_tender_notices():
    """
    Fetch tender releases for today from the Kosovo PPRC API.
    """
    url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease"
    params = {
        "endDateFrom": today.isoformat(),
        "endDateEnd":   today.isoformat(),
        "DataFormat":   "json",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get('releases', [])

# 2. Load and normalize releases
releases = fetch_tender_notices()
if not releases:
    print(f"No tender notices published on {today.isoformat()}.")
    sys.exit(0)

df = pd.json_normalize(releases)

# 3. Filter by tag == 'tender' (initial publication)
df = df[df['tag'].apply(lambda tags: isinstance(tags, list) and 'tender' in tags)]
if df.empty:
    print(f"No tender notices published on {today.isoformat()}.")
    sys.exit(0)

# 4. Filter by release date equals today (from df['date'])
df['release_date'] = pd.to_datetime(df['date']).dt.date
df = df[df['release_date'] == today]

if df.empty:
    print(f"No tender notices published on {today.isoformat()}.")
    sys.exit(0)

# 5. Select and rename needed columns
out = df[[
    'tender.id',
    'tender.title',
    'tender.procuringEntity.party.name',
    'tender.value.amount',
    'tender.value.currency',
    'tender.tenderPeriod.endDate'
]]
out.columns = [
    'ID',
    'Title',
    'Buyer',
    'ValueAmount',
    'ValueCurrency',
    'SubmissionDeadline'
]

# 6. Save CSV
dest = 'daily_tender_notices.csv'
out.to_csv(dest, index=False)
print(f"Saved {dest} with {len(out)} records for {today.isoformat()}.")
