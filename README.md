# MotionStudio

MotionStudio is an AI-powered video animation platform that brings static character images to life using motion templates. It leverages the power of Alibaba's **Animate Anyone (Qwen)** model via DashScope to generate high-quality animations.

This project is built with a modern, modular architecture separating the React frontend from the FastAPI backend, ensuring scalability and maintainability.

---

## 🚀 Features

-   **AI Animation Generation**: animate full-body character images with any motion video.
-   **Modular Architecture**: Clean separation of concerns with a robust backend orchestrator.
-   **Drag-and-Drop Interface**: Easy-to-use file uploaders for images and videos.
-   **Webcam Support**: Record motion templates directly from your browser.
-   **Real-time Status**: Live updates on the animation generation process.
-   **Cloud Storage**: Integrated with Supabase for secure media handling.

---

## 🏗️ Architecture

The project is divided into two main components:

### 1. Backend (Python / FastAPI)
Located in `backend/`, the backend handles the core logic, API orchestration, and communication with AI services. It follows a layered architecture:
-   **Core (`backend/core/`)**: Defines interfaces (`INode`, `IStorageService`) and data models.
-   **Services (`backend/services/`)**: Concrete implementations for Storage (Supabase), Media Processing (FFmpeg), and AI Clients (Alibaba DashScope).
-   **Nodes (`backend/nodes/`)**: Individual pipeline steps (e.g., `VideoProcessingNode`, `AlibabaGenerationNode`).
-   **Orchestrator (`backend/orchestrator/`)**: The `GraphExecutor` manages the execution of the Directed Acyclic Graph (DAG) for video generation.

### 2. Frontend (React / TypeScript)
Located in `frontend/`, the frontend provides a responsive and intuitive user interface.
-   **Services (`frontend/src/services/`)**: API clients for communicating with the backend and Supabase.
-   **Hooks (`frontend/src/hooks/`)**: Custom React hooks for managing state (e.g., `useMediaCapture`, `useJobOrchestrator`).
-   **Components (`frontend/src/components/`)**: Reusable UI components styled with `styled-components`.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
-   **Python 3.8+**
-   **Node.js 16+**
-   **FFmpeg**: Must be installed and added to your system's PATH.
-   **Supabase Account**: For storage.
-   **Alibaba Cloud Account**: For DashScope API access.

---

## ⚙️ Setup Guide

### 1. Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```

2.  Create and activate a virtual environment:
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\Activate.ps1

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Create a `.env` file in the `backend/` directory:
    ```env
    DASHSCOPE_API_KEY=your_dashscope_api_key
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_service_role_key
    ```

### 2. Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Create a `.env` file in the `frontend/` directory (or rename `.env.example`):
    ```env
    VITE_API_URL=http://localhost:8000
    VITE_SUPABASE_URL=your_supabase_url
    VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
    ```

---

## ▶️ Running the Application

You will need to run both the backend and frontend servers simultaneously.

### Start the Backend
Open a terminal in the `backend/` directory and run:
```bash
# Ensure your virtual environment is activated
python -m uvicorn main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

### Start the Frontend
Open a new terminal in the `frontend/` directory and run:
```bash
npm run dev
```
The application will be available at `http://localhost:5173`.

---

## 🐛 Troubleshooting

-   **SSL Certificate Errors (Windows)**: If you encounter SSL errors when the backend tries to contact Alibaba APIs, ensure `certifi` is installed (`pip install certifi`) and the backend is using it (already handled in `main.py`).
-   **FFmpeg Not Found**: Ensure FFmpeg is installed and the `bin` folder is added to your system Environment Variables.
-   **CORS Issues**: If the frontend cannot talk to the backend, check that the backend is running and the `VITE_API_URL` is correct.
