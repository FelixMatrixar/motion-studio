import os
import asyncio
import uuid
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from core.interfaces import IStorageService

load_dotenv()

class SupabaseStorageService(IStorageService):
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        if not self.url or not self.key:
            raise ValueError("Missing Supabase credentials in .env file!")
        self.client: Client = create_client(self.url, self.key)
        self.bucket_name = "motion-studio-media"

    async def upload(self, local_path: str, destination_path: str = None) -> str:
        if not destination_path:
             destination_path = f"processed/{uuid.uuid4()}_{os.path.basename(local_path)}"

        print(f"[Storage] Uploading {destination_path} to Supabase...")
        
        def _upload_sync():
            self.client.storage.from_(self.bucket_name).upload(
                file=local_path,
                path=destination_path,
                file_options={"content-type": "video/mp4"}
            )
            return self.client.storage.from_(self.bucket_name).get_public_url(destination_path)
            
        public_url = await asyncio.to_thread(_upload_sync)
        print(f"[Storage] Upload complete. Public URL: {public_url}")
        
        # Give Supabase 2 seconds to propagate the public link
        await asyncio.sleep(2)
        
        return public_url

    async def delete(self, path: str) -> None:
        """
        Deletes a file from Supabase storage.
        Path should be the relative path in the bucket, or the full URL.
        If full URL, it will try to extract the relative path.
        """
        try:
            # Check if it is a full URL
            if self.url in path:
                # Extract 'processed/uuid_processed.mp4' from the full URL
                # The format is usually .../storage/v1/object/public/bucket_name/path
                # But here we might just split by bucket name
                if f"/public/{self.bucket_name}/" in path:
                    path = path.split(f"/public/{self.bucket_name}/")[-1]
            
            print(f"[Cleanup] Deleting file from Supabase: {path}")
            self.client.storage.from_(self.bucket_name).remove([path])
            print("[Cleanup] File deleted successfully.")
        except Exception as e:
            print(f"[Cleanup Warning] Failed to delete file: {e}")
