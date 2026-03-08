import os
import tempfile
import urllib.request
import asyncio
import ffmpeg
import uuid
from http import HTTPStatus
import time
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURATION & SETUP
# ==========================================

# Load environment variables from .env FIRST
load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("DASHSCOPE_API_KEY is missing from your .env file!")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env file!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================
# 2. THE NODE ROUTER
# ==========================================

async def execute_node(node_type: str, inputs: dict) -> dict:
    """Router function to trigger the correct logic based on node type."""
    registry = {
        "ffmpeg_processor": run_ffmpeg_processor,
        "qwen_video_generator": run_qwen_generator
    }
    
    if node_type not in registry:
        raise ValueError(f"Unknown node type: {node_type}")
        
    return await registry[node_type](inputs)


# ==========================================
# 3. FFMPEG PROCESSING & STORAGE NODE
# ==========================================

def _process_ffmpeg_sync(input_url: str, action: str) -> str:
    """Synchronous core for FFmpeg to be run in a separate thread."""
    if input_url.startswith("http://") or input_url.startswith("https://"):
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        urllib.request.urlretrieve(input_url, temp_input)
        target_input = temp_input
        is_temp = True
    else:
        target_input = input_url
        is_temp = False

    output_filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}_processed.mp4")
    
    try:
        if action == "trim_and_resize":
            (
                ffmpeg
                .input(target_input, t=5) 
                .filter('scale', 768, 768, force_original_aspect_ratio='increase')
                .filter('crop', 768, 768)
                .filter('fps', fps=30)
                .output(output_filename, vcodec='libx264', crf=23, acodec='aac')
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        else:
            raise ValueError(f"Unsupported FFmpeg action: {action}")
            
    except ffmpeg.Error as e:
        print(f"FFmpeg stderr: {e.stderr.decode('utf8')}")
        raise RuntimeError("FFmpeg processing failed")
    finally:
        if is_temp and os.path.exists(target_input):
            os.remove(target_input)

    return output_filename

async def upload_to_public_storage(local_path: str) -> str:
    """Uploads processed files to Supabase and returns the public URL."""
    bucket_name = "motion-studio-media"
    file_name = f"processed/{uuid.uuid4()}_{os.path.basename(local_path)}"
    
    print(f"[Storage] Uploading {file_name} to Supabase...")
    
    def _upload_sync():
        supabase.storage.from_(bucket_name).upload(
            file=local_path,
            path=file_name,
            file_options={"content-type": "video/mp4"}
        )
        return supabase.storage.from_(bucket_name).get_public_url(file_name)
        
    public_url = await asyncio.to_thread(_upload_sync)
    print(f"[Storage] Upload complete. Public URL: {public_url}")
    
    if os.path.exists(local_path):
        os.remove(local_path)
        
    return public_url

async def run_ffmpeg_processor(inputs: dict) -> dict:
    video_url = inputs.get("video_url")
    action = inputs.get("action", "trim_and_resize")
    
    if not video_url:
        raise ValueError("Missing 'video_url' for FFmpeg processor")
        
    print(f"[FFmpeg] Processing video: {video_url}")
    output_path = await asyncio.to_thread(_process_ffmpeg_sync, video_url, action)
    public_url = await upload_to_public_storage(output_path)
    
    return {"output_path": public_url}


# ==========================================
# 4. QWEN (DASHSCOPE) GENERATOR NODE (Custom HTTP implementation)
# ==========================================

def _call_qwen_sync(ref_image: str, motion_vid: str, prompt: str) -> dict:
    """Synchronous polling loop for AnimateAnyone Gen 2."""
    
    # Note: For this specific API, we drop the '-intl' from the URL as per your docs
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
    
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    # IMPORTANT: 'motion_vid' MUST be a valid template_id (e.g., "AACT.xxx..."), not an mp4 URL!
    payload = {
        "model": "animate-anyone-gen2",
        "input": {
            "image_url": ref_image,
            "template_id": motion_vid  
        },
        "parameters": {
            "use_ref_img_bg": False,
            "video_ratio": "9:16"
        }
    }

    print(f"[AnimateAnyone] Submitting task to AnimateAnyone Gen 2...")
    
    # 1. Create the Task
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to create AnimateAnyone task: {response.text}")
        
    response_data = response.json()
    task_id = response_data.get("output", {}).get("task_id")
    
    if not task_id:
        raise Exception(f"Task ID not found in response: {response_data}")
        
    print(f"[AnimateAnyone] Task submitted successfully. Task ID: {task_id}")
    print(f"[AnimateAnyone] Polling for completion. This takes a few minutes...")

    # 2. Poll for the Result
    poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    poll_headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
    }

    while True:
        poll_response = requests.get(poll_url, headers=poll_headers)
        if poll_response.status_code != 200:
            raise Exception(f"Polling failed: {poll_response.text}")
            
        poll_data = poll_response.json()
        task_status = poll_data.get("output", {}).get("task_status")
        
        if task_status == "SUCCEEDED":
            final_url = poll_data.get("output", {}).get("video_url")
            print(f"[AnimateAnyone] Generation complete! URL: {final_url}")
            return {
                "video_url": final_url, 
                "task_id": task_id
            }
        elif task_status in ["FAILED", "CANCELED", "UNKNOWN"]:
            error_code = poll_data.get("output", {}).get("code", "Unknown code")
            error_msg = poll_data.get("output", {}).get("message", "Unknown error")
            raise Exception(f"Alibaba AI Task Failed: {task_status} | Code: {error_code} | Reason: {error_msg}")
            
        print(f"[AnimateAnyone] Status: {task_status}... waiting 10 seconds.")
        time.sleep(10)
        
async def run_qwen_generator(inputs: dict) -> dict:
    ref_image = inputs.get("reference_image")
    motion_vid = inputs.get("motion_video") 
    prompt = inputs.get("prompt", "apply the motion to the reference image")
    
    if not ref_image or not motion_vid:
         raise ValueError("Qwen node requires both 'reference_image' and 'motion_video'")

    # Run the blocking network polling loop in a thread
    output_data = await asyncio.to_thread(_call_qwen_sync, ref_image, motion_vid, prompt)
    
    return output_data