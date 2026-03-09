from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import certifi
import os
import ssl
import uuid

# Import the new structure
from core.models import GraphPayload
from orchestrator.graph_executor import GraphExecutor

# 🛡️ THE SSL FIX FOR CENTOS 7 / Windows
# Tell Python to use certifi's modern certificates
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Force urllib (which Dashscope uses) to use these certs
ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())

app = FastAPI(title="MotionStudio DAG Orchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === IN-MEMORY DATABASE FOR JOB STATUS ===
# (In production, you'd use Redis or Postgres for this)
jobs = {}

# Initialize the Executor
executor = GraphExecutor()

# === THE BACKGROUND WORKER ===
async def run_dag_background(job_id: str, payload: GraphPayload):
    print(f"\n=== Background Job {job_id} Started ===")
    
    async def update_status(message: str):
        jobs[job_id]["message"] = message

    try:
        final_state = await executor.execute(payload, update_status_callback=update_status)
        
        # Mark as completed and save the final state
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["final_state"] = final_state
        jobs[job_id]["message"] = "Completed successfully"
        print(f"=== Background Job {job_id} Completed ===")

    except Exception as e:
        print(f"\n[ERROR] Job {job_id} failed: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Failed: {str(e)}"


# === ENDPOINTS ===

@app.post("/execute-graph")
async def execute_graph(payload: GraphPayload, background_tasks: BackgroundTasks):
    """Accepts the payload and kicks off the background task instantly."""
    job_id = str(uuid.uuid4())
    
    # Initialize the job in our tracker
    jobs[job_id] = {
        "status": "processing",
        "message": "Initializing DAG...",
        "final_state": None,
        "error": None
    }
    
    # Hand the heavy lifting to FastAPI's background worker
    background_tasks.add_task(run_dag_background, job_id, payload)
    
    # Return immediately!
    return {"job_id": job_id, "status": "processing"}

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Frontend calls this every few seconds to check progress."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
