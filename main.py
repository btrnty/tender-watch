#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os, datetime, requests, pandas as pd
from openai.error import RateLimitError, OpenAIError
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# 1) dates
today = datetime.date.today().isoformat()

# 2) fetch raw releases
url = "https://ocdskrpp.rks-gov.net/krppAPI/TenderRelease?DataFormat=json"
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()["releases"]

# 3) normalize to DataFrame
df = pd.json_normalize(data, sep="_")

# 4) filter only initial tenders published today
def is_initial_tender(tags, date_str):
    return "tender" in tags and "award" not in tags and date_str.startswith(today)

df = df[df.apply(lambda r: is_initial_tender(r["tag"], r["date"]), axis=1)]

# 5) pick columns
out = pd.DataFrame({
    "Title":        df["tender_title"],
    "Buyer":        df["tender_procuringEntity_party_name"],
    "ValueEUR":     df["tender_value_amount"],
    "Deadline":     df["tender_tenderPeriod_endDate"],
})

# 6) save CSV
out.to_csv("daily_tender_notices.csv", index=False)
print(f"✅ Saved {len(out)} tender notices for {today}")

# (optional) 7) send via email…
# your existing email-sending code here

