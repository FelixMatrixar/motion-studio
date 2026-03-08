from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
import re
import uuid
import os
import ssl
import certifi

# Import the router function from your registry
from node_registry import execute_node

# 🛡️ THE SSL FIX FOR CENTOS 7
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

class NodeDef(BaseModel):
    id: str
    type: str
    inputs: Dict[str, Any]

class EdgeDef(BaseModel):
    source: str
    target: str

class GraphPayload(BaseModel):
    graph_id: str
    state: Dict[str, Any]
    nodes: List[NodeDef]
    edges: List[EdgeDef]

# === IN-MEMORY DATABASE FOR JOB STATUS ===
# (In production, you'd use Redis or Postgres for this)
jobs = {}

def inject_variables(inputs: Dict[str, Any], global_state: Dict[str, Any]) -> Dict[str, Any]:
    resolved_inputs = {}
    pattern = re.compile(r"\{\{(.+?)\}\}")
    for key, value in inputs.items():
        if isinstance(value, str):
            matches = pattern.findall(value)
            for match in matches:
                if match in global_state:
                    value = value.replace(f"{{{{{match}}}}}", str(global_state[match]))
        resolved_inputs[key] = value
    return resolved_inputs

# === THE BACKGROUND WORKER ===
async def run_dag_background(job_id: str, payload: GraphPayload):
    current_state = {**payload.state}
    print(f"\n=== Background Job {job_id} Started ===")
    
    try:
        for node in payload.nodes:
            resolved_inputs = inject_variables(node.inputs, current_state)
            
            # Update status so frontend knows what node we are on
            jobs[job_id]["message"] = f"Executing {node.type}..."
            
            node_output = await execute_node(node.type, resolved_inputs)
            
            for out_key, out_val in node_output.items():
                current_state[f"{node.id}.{out_key}"] = out_val

        # Mark as completed and save the final state
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["final_state"] = current_state
        print(f"=== Background Job {job_id} Completed ===")

    except Exception as e:
        print(f"\n[ERROR] Job {job_id} failed: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


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