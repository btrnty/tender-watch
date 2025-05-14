#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import datetime
import requests
import pandas as pd
import openai
import sys

# 0. Load your OpenAI key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Date range: yesterday → today
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)

# 2. Fetch the raw OCDS JSON
url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease"
params = {
    "endDateFrom":  yesterday.isoformat(),
    "endDateEnd":    today.isoformat(),
    "DataFormat":    "json",
}
resp = requests.get(url, params=params, timeout=60)
resp.raise_for_status()
raw = resp.json()

if not raw:
    print("No tenders yesterday.")
    sys.exit(0)

# 3. Explode 'releases' into a flat DataFrame
df = pd.json_normalize(raw, record_path=["releases"])
if df.empty:
    print("No tenders yesterday.")
    sys.exit(0)

# 4. Summarise each tender with OpenAI using lower-cost model and error handling
def summarise(row):
    prompt = (
        f"Summarise this Kosovo public tender in max 3 bullet points:\n"
        f"Title: {row['tender.title']}\n"
        f"Buyer: {row['tender.procuringEntity.party.name']}\n"
        f"Value: {row['tender.value.amount']} €\n"
        f"Deadline: {row['tender.tenderPeriod.endDate']}"
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except openai.RateLimitError:
        return "⚠️ Summary skipped (quota reached)"
    except openai.OpenAIError as e:
        return f"⚠️ OpenAI error: {e}"

# 5. Apply summarisation and export
print(f"Processing {len(df)} tenders...")
df["summary"] = df.apply(summarise, axis=1)
out = df[[
    "tender.title",
    "tender.procuringEntity.party.name",
    "tender.value.amount",
    "tender.tenderPeriod.endDate",
    "summary"
]]
out.to_csv("daily_tenders.csv", index=False)
print("Saved daily_tenders.csv")

