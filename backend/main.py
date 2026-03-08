from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any
import re
from node_registry import execute_node

app = FastAPI(title="MotionStudio DAG Orchestrator")

# Critical for local development with Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
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
    state: Dict[str, Any]  # Global variables passed from frontend
    nodes: List[NodeDef]
    edges: List[EdgeDef]

def inject_variables(inputs: Dict[str, Any], global_state: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves {{variable_names}} from the global state."""
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

@app.post("/execute-graph")
async def execute_graph(payload: GraphPayload):
    # Flatten the state so node outputs can be accessed downstream
    current_state = {**payload.state}
    
    # Note: Assuming nodes are provided in topological order for now.
    for node in payload.nodes:
        try:
            resolved_inputs = inject_variables(node.inputs, current_state)
            print(f"\n-> Executing Node: {node.id} | Type: {node.type}")
            
            # Delegate to the node registry
            node_output = await execute_node(node.type, resolved_inputs)
            
            # Append outputs back to the global state
            for out_key, out_val in node_output.items():
                current_state[f"{node.id}.{out_key}"] = out_val
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Node {node.id} failed: {str(e)}")

    return {"status": "success", "graph_id": payload.graph_id, "final_state": current_state}