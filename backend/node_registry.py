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
        "alibaba_template_generator": run_alibaba_template_generator,
        "alibaba_image_detector": run_alibaba_image_detector,
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
                # Scale width to 720, automatically calculate height to preserve aspect ratio. 
                # The -2 ensures the height is an even number (required by libx264).
                .filter('scale', 720, -2)
                .filter('fps', fps=24)
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
    
    # Give Supabase 2 seconds to propagate the public link
    await asyncio.sleep(2)
    
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
# 4. ALIBABA IMAGE DETECTOR NODE
# ==========================================

def _call_image_detect_sync(image_url: str) -> dict:
    """Synchronous API call to validate the character image."""
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/aa-detect"
    
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "animate-anyone-detect-gen2",
        "input": {
            "image_url": image_url
        }
    }

    print(f"[Image Detect] Validating reference image...")
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to call Image Detect API: {response.text}")
        
    response_data = response.json()
    check_pass = response_data.get("output", {}).get("check_pass", False)
    
    if not check_pass:
        raise ValueError("Image rejected by Alibaba: Ensure it is a clear, unobstructed full or half-body portrait.")

    print(f"[Image Detect] Image passed validation!")
    
    # We return the original image URL so the DAG can pass it to the final node
    return {"validated_image_url": image_url}

async def run_alibaba_image_detector(inputs: dict) -> dict:
    image_url = inputs.get("image_url")
    if not image_url:
        raise ValueError("Missing 'image_url' for image detector")
        
    return await asyncio.to_thread(_call_image_detect_sync, image_url)


# ==========================================
# 5. ALIBABA TEMPLATE GENERATOR NODE
# ==========================================

def _call_template_gen_sync(video_url: str) -> dict:
    """Synchronous polling loop for AnimateAnyone Action Template."""
    
    # Print the exact URL for debugging
    print(f"\n[Template Gen] Sending this exact URL to Alibaba: {video_url}\n")
    
    # The dedicated endpoint for template generation
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/aa-template-generation/"
    
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "animate-anyone-template-gen2",
        "input": {
            "video_url": video_url
        }
    }

    print(f"[Template Gen] Submitting raw video for template extraction...")
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to create Template generation task: {response.text}")
        
    response_data = response.json()
    task_id = response_data.get("output", {}).get("task_id")
    
    if not task_id:
        raise Exception(f"Task ID not found in response: {response_data}")
        
    print(f"[Template Gen] Task submitted successfully. Task ID: {task_id}")

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
            template_id = poll_data.get("output", {}).get("template_id") 
            print(f"[Template Gen] Generation complete! Template ID: {template_id}")
            
            # Nuke the file from Supabase to save quota
            try:
                # Extract 'processed/uuid_processed.mp4' from the full URL
                bucket_path = video_url.split("/public/motion-studio-media/")[-1]
                print(f"[Cleanup] Deleting temporary file from Supabase: {bucket_path}")
                
                # Use the existing supabase client to delete it
                supabase.storage.from_("motion-studio-media").remove([bucket_path])
                print("[Cleanup] File deleted successfully. Quota reclaimed.")
            except Exception as e:
                print(f"[Cleanup Warning] Failed to delete temporary file: {e}")

            return {"template_id": template_id}
            
        elif task_status in ["FAILED", "CANCELED", "UNKNOWN"]:
            error_code = poll_data.get("output", {}).get("code", "Unknown code")
            error_msg = poll_data.get("output", {}).get("message", "Unknown error")
            raise Exception(f"Template Gen Task Failed: {task_status} | Code: {error_code} | Reason: {error_msg}")
            
        print(f"[Template Gen] Status: {task_status}... waiting 5 seconds.")
        time.sleep(5)

async def run_alibaba_template_generator(inputs: dict) -> dict:
    video_url = inputs.get("video_url")
    if not video_url:
        raise ValueError("Missing 'video_url' for template generator")
        
    return await asyncio.to_thread(_call_template_gen_sync, video_url)


# ==========================================
# 6. QWEN (DASHSCOPE) FINAL GENERATOR NODE
# ==========================================

def _call_qwen_sync(ref_image: str, template_id: str, prompt: str) -> dict:
    """Synchronous polling loop for final AnimateAnyone Gen 2 generation."""
    api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
    
    headers = {
        "X-DashScope-Async": "enable",
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "animate-anyone-gen2",
        "input": {
            "image_url": ref_image,
            "template_id": template_id  # This now receives the AACT.xxx ID!
        },
        "parameters": {
            "use_ref_img_bg": False,
            "video_ratio": "9:16"
        }
    }

    print(f"[AnimateAnyone] Submitting final task to AnimateAnyone Gen 2...")
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise Exception(f"Failed to create AnimateAnyone task: {response.text}")
        
    response_data = response.json()
    task_id = response_data.get("output", {}).get("task_id")
    
    if not task_id:
        raise Exception(f"Task ID not found in response: {response_data}")
        
    print(f"[AnimateAnyone] Task submitted successfully. Task ID: {task_id}")

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
    # Changed input variable name expectations to reflect the new DAG flow
    ref_image = inputs.get("validated_image_url") or inputs.get("reference_image")
    template_id = inputs.get("template_id") 
    prompt = inputs.get("prompt", "apply the motion to the reference image")
    
    if not ref_image or not template_id:
         raise ValueError("Qwen node requires both a reference image URL and a 'template_id'. Ensure the image detection and template generation nodes ran successfully.")

    output_data = await asyncio.to_thread(_call_qwen_sync, ref_image, template_id, prompt)
    
    return output_data