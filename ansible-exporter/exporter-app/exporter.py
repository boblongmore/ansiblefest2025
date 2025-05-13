from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.responses import PlainTextResponse, JSONResponse
from datetime import datetime
from contextlib import asynccontextmanager
import numpy_financial as npf
import httpx
import os
import uvicorn
import asyncio

load_dotenv()
AAP_URL = os.getenv('aap_server')
AAP_TOKEN = os.getenv('aap_token')
JOB_ID = 46 # Replace with your job template ID
API_ENDPOINT=f"/api/controller/v2/workflow_job_templates/{JOB_ID}/workflow_jobs/"
EST_MANUAL_TIME = 60 # Time to do the task manually in minutes
EST_ENG_COST = 100 # Hourly rate of an engineer
INITIAL_INVESTMENT = -200000 / 3 # Initial spread out over 3 years
SUBS = 6000 # Subscription cost for 1 years
MAINTENANCE = 52 * EST_ENG_COST # Estimated one hour a week of maintenance on average
COST_OF_MISTAKES = ((3*EST_ENG_COST) * 21) # Estimate three engineers on 9 3-hour calls a year
IQ = (EST_ENG_COST * 160) # Estimate we will save 160 hours a year because of improved quality
BUSINESS_VALUE = 50000 # Estimated impact of reduced downtime on business value





metrics_cache = {
    "successful": 0,
    "failure": 0,
    "hours_saved": 0.0,
    "money_saved": 0.0,
    "irr_calc": 0.0,
    "roi": 0.0,
    "roi_predict": 0.0,
}

async def get_job_details(query):
    url = f"https://{AAP_URL}{API_ENDPOINT}{query}"
    headers = {"Authorization": f"Bearer {AAP_TOKEN}"}
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    return 0

async def auto_hours_saved(successful):
    manual_time = EST_MANUAL_TIME * successful['count']
    run_duration_total = 0
    for jobs in successful['results']:
        start = datetime.fromisoformat(jobs['started'])
        finish = datetime.fromisoformat(jobs['finished'])
        duration = finish - start
        run_duration_total += duration.seconds
    automation_time = run_duration_total / 60
    return (manual_time / 60) - (automation_time / 60)

async def auto_money_saved(successful):
    manual_time = EST_MANUAL_TIME * successful['count']
    manual_cost = (manual_time / 60) * EST_ENG_COST
    run_duration_total = 0
    for jobs in successful['results']:
        start = datetime.fromisoformat(jobs['started'])
        finish = datetime.fromisoformat(jobs['finished'])
        duration = finish - start
        run_duration_total += duration.seconds
    automation_time = run_duration_total / 60
    automation_cost = (automation_time / 60) * EST_ENG_COST
    return (manual_cost - automation_cost)

async def calc_irr(successful):
    savings = await auto_money_saved(successful)
    irr = npf.irr([INITIAL_INVESTMENT, savings, savings, savings])
    irr_value = irr * 100
    return irr_value

async def calc_roi(successful):
    MS = await auto_money_saved(successful)
    benefits = MS + COST_OF_MISTAKES + IQ + BUSINESS_VALUE # Realtime money saved plus estimated cost of mistakes and quality saved
    initial_investment = -INITIAL_INVESTMENT
    TC = initial_investment + SUBS + MAINTENANCE
    NB = benefits - TC
    roi = (NB / TC) * 100
    return roi, NB, TC

async def calc_roi_predict(successful):
    MS = await auto_money_saved(successful)
    benefits = (MS * 36) + (COST_OF_MISTAKES * 3) + (IQ * 3) + (BUSINESS_VALUE * 3) # Realtime money saved plus estimated cost of mistakes and quality saved
    initial_investment = -INITIAL_INVESTMENT * 3
    TC = initial_investment + (SUBS * 3)  + (MAINTENANCE * 3)
    NB = benefits - TC
    roi_predict = (NB / TC) * 100
    return roi_predict

async def refresh_metrics():
    while True:
        try:
            successful = await get_job_details("?status=successful")
            failure = await get_job_details("?status=failed")
            hours_saved = await auto_hours_saved(successful)
            money_saved = await auto_money_saved(successful)
            irr_calc = await calc_irr(successful)
            roi, _, _ = await calc_roi(successful)
            roi_predict = await calc_roi_predict(successful)

            # Update the cache
            metrics_cache["successful"] = successful['count']
            metrics_cache["failure"] = failure['count']
            metrics_cache["hours_saved"] = hours_saved
            metrics_cache["money_saved"] = money_saved
            metrics_cache["irr_calc"] = irr_calc
            metrics_cache["roi"] = roi
            metrics_cache["roi_predict"] = roi_predict

        except Exception as e:
            print(f"Error refreshing metrics: {e}")

        # Wait 300 seconds (5 minutes) before refreshing again
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(refresh_metrics())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/job_metrics", response_class=PlainTextResponse)
async def job_metrics():
    return f"""
# HELP ansible_job_template_run_success Number of successful template runs
# TYPE ansible_job_template_run_success gauge
ansible_job_template_run_success {metrics_cache["successful"]}
# HELP ansible_job_template_run_failure Number of failed template runs
# TYPE ansible_job_template_run_failure gauge
ansible_job_template_run_failure {metrics_cache["failure"]}
# HELP ansible_job_template_hours_saved Number of hours saved by automating tasks
# TYPE ansible_job_template_hours_saved gauge
ansible_job_template_hours_saved {metrics_cache["hours_saved"]:.2f}
# HELP ansible_job_template_money_saved Amount of money saved by automating tasks
# TYPE ansible_job_template_money_saved gauge
ansible_job_template_money_saved {metrics_cache["money_saved"]:.2f}
# HELP ansible_job_template_irr_calc Calculated IRR for three years
# TYPE ansible_job_template_irr_calc gauge
ansible_job_template_irr_calc {metrics_cache["irr_calc"]:.2f}
# HELP ansible_job_template_roi_calc Return on Investment for project
# TYPE ansible_job_template_roi_calc gauge
ansible_job_template_roi_calc {metrics_cache["roi"]:.2f}
# HELP ansible_job_template_roi_prediction Return on Investment for project
# TYPE ansible_job_template_roi_prediction gauge
ansible_job_template_roi_prediction {metrics_cache["roi_predict"]:.2f}
"""

if __name__ == "__main__":
    uvicorn.run(app, host='127.0.0.1', port=5000)
