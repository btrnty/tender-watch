#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import datetime
import requests
import pandas as pd

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

# 4. Select and rename columns for CSV output
out = df[[
    'tender.id',
    'tender.title',
    'tender.procuringEntity.party.name',
    'tender.value.amount',
    'tender.value.currency',
    'tender.tenderPeriod.startDate',
    'tender.tenderPeriod.endDate'
]]
out.columns = [
    'ID', 'Title', 'Buyer', 'ValueAmount', 'ValueCurrency', 'StartDate', 'EndDate'
]

# 5. Save the CSV
filename = 'daily_tender_notices.csv'
out.to_csv(filename, index=False)
print(f"Saved {filename} with {len(out)} records.")
