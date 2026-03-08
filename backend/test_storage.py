import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load the .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in .env file!")

# 2. Initialize the client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_storage_test():
    bucket_name = "motion-studio-media"
    test_filename = "test_upload.txt"
    storage_path = f"processed/{test_filename}"
    
    # Create a quick dummy file locally
    with open(test_filename, "w") as f:
        f.write("Supabase storage is locked and loaded!")
        
    print(f"Attempting to upload to bucket: '{bucket_name}'...")
    
    try:
        # 3. Upload the file
        supabase.storage.from_(bucket_name).upload(
            file=test_filename,
            path=storage_path,
            file_options={"content-type": "text/plain", "upsert": "true"}
        )
        
        # 4. Generate the public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(storage_path)
        print(f"\n✅ Upload Successful!")
        print(f"🔗 Public URL: {public_url}")
        print("\nClick the link above to verify it opens in your browser.")
        
    except Exception as e:
        print(f"\n❌ Upload Failed: {e}")
        
    finally:
        # Clean up the local dummy file
        if os.path.exists(test_filename):
            os.remove(test_filename)

if __name__ == "__main__":
    run_storage_test()