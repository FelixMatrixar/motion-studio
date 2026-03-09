import os
import requests
import time
from typing import Dict, Any

class AlibabaApiClient:
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is missing from your .env file!")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def detect_image(self, image_url: str) -> bool:
        """
        Validates the character image.
        Returns True if passed, False otherwise.
        """
        api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/aa-detect"
        
        payload = {
            "model": "animate-anyone-detect-gen2",
            "input": {
                "image_url": image_url
            }
        }

        print(f"[Image Detect] Validating reference image...")
        response = requests.post(api_url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to call Image Detect API: {response.text}")
            
        response_data = response.json()
        check_pass = response_data.get("output", {}).get("check_pass", False)
        
        if not check_pass:
            print("[Image Detect] Image rejected by Alibaba.")
            return False

        print(f"[Image Detect] Image passed validation!")
        return True

    def generate_template(self, video_url: str) -> str:
        """
        Submits a video for template generation and polls for completion.
        Returns the template_id.
        """
        api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/aa-template-generation/"
        
        headers = {**self.headers, "X-DashScope-Async": "enable"}
        
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
        
        return self._poll_task(task_id, "template_id")

    def generate_video(self, ref_image: str, template_id: str, prompt: str = None) -> str:
        """
        Submits a request to generate the final video.
        Returns the video_url.
        """
        api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
        
        headers = {**self.headers, "X-DashScope-Async": "enable"}

        payload = {
            "model": "animate-anyone-gen2",
            "input": {
                "image_url": ref_image,
                "template_id": template_id
            },
            "parameters": {
                "use_ref_img_bg": False,
                "video_ratio": "9:16"
            }
        }
        
        if prompt:
            # Note: The prompt is not explicitly used in the original payload for `animate-anyone-gen2` 
            # based on the provided code, but if needed, it can be added.
            # The original code didn't use 'prompt' in the payload, only in the function signature.
            pass

        print(f"[AnimateAnyone] Submitting final task to AnimateAnyone Gen 2...")
        response = requests.post(api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create AnimateAnyone task: {response.text}")
            
        response_data = response.json()
        task_id = response_data.get("output", {}).get("task_id")
        
        if not task_id:
            raise Exception(f"Task ID not found in response: {response_data}")
            
        print(f"[AnimateAnyone] Task submitted successfully. Task ID: {task_id}")

        return self._poll_task(task_id, "video_url")

    def _poll_task(self, task_id: str, result_key: str) -> str:
        poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        
        while True:
            poll_response = requests.get(poll_url, headers=self.headers)
            if poll_response.status_code != 200:
                raise Exception(f"Polling failed: {poll_response.text}")
                
            poll_data = poll_response.json()
            task_status = poll_data.get("output", {}).get("task_status")
            
            if task_status == "SUCCEEDED":
                result = poll_data.get("output", {}).get(result_key)
                print(f"[Task {task_id}] Succeeded! Result: {result}")
                return result
                
            elif task_status in ["FAILED", "CANCELED", "UNKNOWN"]:
                error_code = poll_data.get("output", {}).get("code", "Unknown code")
                error_msg = poll_data.get("output", {}).get("message", "Unknown error")
                raise Exception(f"Task Failed: {task_status} | Code: {error_code} | Reason: {error_msg}")
                
            print(f"[Task {task_id}] Status: {task_status}... waiting 5 seconds.")
            time.sleep(5)
