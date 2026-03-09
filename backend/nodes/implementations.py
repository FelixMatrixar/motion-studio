from typing import Dict, Any
from core.interfaces import INode, IMediaProcessor, IStorageService
from services.alibaba import AlibabaApiClient

class VideoProcessingNode(INode):
    def __init__(self, media_processor: IMediaProcessor, storage_service: IStorageService):
        self.media_processor = media_processor
        self.storage_service = storage_service

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        video_url = inputs.get("video_url")
        # action = inputs.get("action", "trim_and_resize") # Currently only one action supported
        
        if not video_url:
            raise ValueError("Missing 'video_url' for VideoProcessingNode")

        print(f"[VideoProcessingNode] Processing video: {video_url}")
        
        # 1. Process video locally
        local_processed_path = await self.media_processor.trim_and_resize(video_url)
        
        # 2. Upload to storage
        public_url = await self.storage_service.upload(local_processed_path)
        
        return {"output_path": public_url}

class AlibabaImageNode(INode):
    def __init__(self, api_client: AlibabaApiClient):
        self.api_client = api_client

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        image_url = inputs.get("image_url")
        if not image_url:
            raise ValueError("Missing 'image_url' for AlibabaImageNode")

        is_valid = self.api_client.detect_image(image_url)
        if not is_valid:
             raise ValueError("Image rejected by Alibaba: Ensure it is a clear, unobstructed full or half-body portrait.")
             
        return {"validated_image_url": image_url}

class AlibabaTemplateNode(INode):
    def __init__(self, api_client: AlibabaApiClient, storage_service: IStorageService = None):
        self.api_client = api_client
        self.storage_service = storage_service

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        video_url = inputs.get("video_url")
        if not video_url:
            raise ValueError("Missing 'video_url' for AlibabaTemplateNode")

        template_id = self.api_client.generate_template(video_url)
        
        # Cleanup if storage service is provided
        if self.storage_service:
            try:
                await self.storage_service.delete(video_url)
            except Exception as e:
                print(f"[AlibabaTemplateNode] Warning: Failed to cleanup temporary file: {e}")

        return {"template_id": template_id}

class AlibabaGenerationNode(INode):
    def __init__(self, api_client: AlibabaApiClient):
        self.api_client = api_client

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        ref_image = inputs.get("validated_image_url") or inputs.get("reference_image")
        template_id = inputs.get("template_id")
        prompt = inputs.get("prompt", "apply the motion to the reference image")

        if not ref_image or not template_id:
            raise ValueError("AlibabaGenerationNode requires 'validated_image_url' and 'template_id'.")

        video_url = self.api_client.generate_video(ref_image, template_id, prompt)
        
        return {"video_url": video_url}
