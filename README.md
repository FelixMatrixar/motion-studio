 # MotionStudio - Local Development Guide

## 1. Clone the Repository git clone <your-repo-url>
cd motion-studio
 ## 2. Frontend Setup (React/Vite)
 Open a terminal and navigate to the frontend directory:
 cd frontend
 
 Install the Node dependencies:
 npm install

Create a `.env.local` file inside the `frontend` folder and add these keys:
```
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_anon_key
```

 Start the local development server:
 npm run dev

## 3. Backend Setup (FastAPI) Open a NEW terminal window and navigate to the backend directory:
 cd backend

 Create and activate a Python virtual environment:
python -m venv venv$ source venv/bin/activate  # On Windows, use: venv\Scripts\activate

 Install the Python dependencies:
pip install -r requirements.txt
 Create a `.env` file inside the `backend` folder and add these keys:
SUPABASE_URL=your_supabase_url SUPABASE_KEY=your_supabase_service_key
DASHSCOPE_API_KEY=your_dashscope_api_key PORT=8000

Start the FastAPI server with live-reloading: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

## 4. Access the App Frontend URL: http://localhost:5173
 Backend API Docs: http://localhost:8000/docs