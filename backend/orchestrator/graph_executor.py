import re
import traceback
from typing import Callable, Awaitable
from core.models import GraphPayload
from core.interfaces import INode
from services.storage import SupabaseStorageService
from services.media import FFmpegVideoProcessor
from services.alibaba import AlibabaApiClient
from nodes.implementations import (
    VideoProcessingNode,
    AlibabaTemplateNode,
    AlibabaImageNode,
    AlibabaGenerationNode
)

class GraphExecutor:
    def __init__(self):
        # Instantiate services
        # In a real DI framework, these would be injected.
        self.storage_service = SupabaseStorageService()
        self.media_processor = FFmpegVideoProcessor()
        self.alibaba_client = AlibabaApiClient()

    def _get_node_instance(self, node_type: str) -> INode:
        if node_type == "ffmpeg_processor":
            return VideoProcessingNode(self.media_processor, self.storage_service)
        elif node_type == "alibaba_template_generator":
            return AlibabaTemplateNode(self.alibaba_client, self.storage_service)
        elif node_type == "alibaba_image_detector":
            return AlibabaImageNode(self.alibaba_client)
        elif node_type == "qwen_video_generator":
            return AlibabaGenerationNode(self.alibaba_client)
        else:
            raise ValueError(f"Unknown node type: {node_type}")

    def _inject_variables(self, inputs: dict, global_state: dict) -> dict:
        resolved_inputs = {}
        pattern = re.compile(r"\{\{(.+?)\}\}")
        for key, value in inputs.items():
            if isinstance(value, str):
                matches = pattern.findall(value)
                for match in matches:
                    if match in global_state:
                        val_to_inject = global_state[match]
                        # If the value is the ONLY thing in the string, replace it directly (keeping type)
                        if value == f"{{{{{match}}}}}":
                             value = val_to_inject
                        else:
                             value = value.replace(f"{{{{{match}}}}}", str(val_to_inject))
            resolved_inputs[key] = value
        return resolved_inputs

    async def execute(self, payload: GraphPayload, update_status_callback: Callable[[str], Awaitable[None]] = None):
        current_state = {**payload.state}
        
        print(f"\n=== Graph Execution Started ===")
        
        try:
            for node_def in payload.nodes:
                resolved_inputs = self._inject_variables(node_def.inputs, current_state)
                
                msg = f"Executing {node_def.type}..."
                print(msg)
                if update_status_callback:
                    # Run callback but don't block too long if it's just updating status
                    try:
                        await update_status_callback(msg)
                    except Exception as e:
                        print(f"Warning: Failed to update status: {e}")
                
                node_instance = self._get_node_instance(node_def.type)
                node_output = await node_instance.execute(resolved_inputs)
                
                for out_key, out_val in node_output.items():
                    current_state[f"{node_def.id}.{out_key}"] = out_val

            print(f"=== Graph Execution Completed ===")
            return current_state

        except Exception as e:
            print(f"\n[ERROR] Graph execution failed: {str(e)}")
            traceback.print_exc()
            raise e
