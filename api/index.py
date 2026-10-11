# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, statistics

app = FastAPI()

# CORS enable karo — kisi bhi website se request aane do
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON data load karo
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "q-vercel-latency.json")

with open(DATA_FILE) as f:
    ALL_DATA = json.load(f)

# Request ka format define karo
class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        # Sirf is region ke records nikalo
        records = [r for r in ALL_DATA if r["region"] == region]

        if not records:
            result[region] = {"error": "region not found"}
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes   = [r["uptime_pct"] / 100.0 for r in records]  # convert to 0-1 range

        # Sorted list for percentile
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)

        # Calculations
        avg_latency = statistics.mean(latencies)
        p95_index   = max(0, int(n * 0.95) - 1)
        p95_latency = sorted_lat[p95_index]
        avg_uptime  = statistics.mean(uptimes)
        breaches    = sum(1 for l in latencies if l > req.threshold_ms)

        result[region] = {
            "avg_latency": round(avg_latency, 4),
            "p95_latency": round(p95_latency, 4),
            "avg_uptime":  round(avg_uptime,  4),
            "breaches":    breaches
        }

    return result

@app.get("/")
def root():
    return {"message": "Analytics API is running!"}
