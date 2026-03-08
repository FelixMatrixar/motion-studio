import asyncio

async def execute_node(node_type: str, inputs: dict) -> dict:
    """Router function to trigger the correct logic based on node type."""
    registry = {
        "ffmpeg_processor": mock_ffmpeg_processor,
        "qwen_video_generator": mock_qwen_generator
    }
    
    if node_type not in registry:
        raise ValueError(f"Unknown node type: {node_type}")
        
    return await registry[node_type](inputs)

async def mock_ffmpeg_processor(inputs: dict) -> dict:
    print(f"   [FFmpeg] Downloading and trimming video from: {inputs.get('video_url')}")
    await asyncio.sleep(1)  # Simulating local FFmpeg processing
    
    # Return the path where the processed file was saved
    return {"output_path": "/tmp/processed_motion_video.mp4"}

async def mock_qwen_generator(inputs: dict) -> dict:
    print(f"   [Qwen API] Generating video...")
    print(f"      - Ref Image: {inputs.get('reference_image')}")
    print(f"      - Motion Source: {inputs.get('motion_video')}")
    print(f"      - Prompt: {inputs.get('prompt')}")
    
    await asyncio.sleep(2)  # Simulating Alibaba API call
    
    return {
        "video_url": "https://dashscope-result-placeholder.aliyun.com/video/success.mp4", 
        "task_id": "wanx-task-777"
    }