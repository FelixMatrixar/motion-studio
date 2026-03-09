from pydantic import BaseModel
from typing import Dict, List, Any, Optional

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
