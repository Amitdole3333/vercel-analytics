# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json, os, statistics

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON data load karo
DATA_FILE = os.path.join(
    os.path.dirname(__file__), "..", "data", "q-vercel-latency.json"
)

with open(DATA_FILE) as f:
    ALL_DATA = json.load(f)


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


@app.options("/analytics")
async def options_analytics():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.post("/analytics")
def analytics(req: AnalyticsRequest):
    result = {}

    for region in req.regions:
        records = [r for r in ALL_DATA if r["region"] == region]

        if not records:
            result[region] = {"error": "region not found"}
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] / 100.0 for r in records]

        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        p95_index = max(0, int(n * 0.95) - 1)

        result[region] = {
            "avg_latency": round(statistics.mean(latencies), 4),
            "p95_latency": round(sorted_lat[p95_index], 4),
            "avg_uptime": round(statistics.mean(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > req.threshold_ms),
        }

    return JSONResponse(
        content=result,
        headers={"Access-Control-Allow-Origin": "*"},
    )


@app.get("/")
def root():
    return JSONResponse(
        content={"message": "Analytics API is running!"},
        headers={"Access-Control-Allow-Origin": "*"},
    )
