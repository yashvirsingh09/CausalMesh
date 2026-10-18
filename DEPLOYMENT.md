# CausalMesh: Live Deployment & Local Setup Guide

> **Hackathon Requirement:**  
> *"FalkorDB must be the primary graph database, and it must support a central part of the product.*  
> *A live deployment is preferred. Projects that cannot be deployed must include complete local setup instructions and a working demo video."*  
> **Demo Video Walkthrough:** [https://youtu.be/skAD7R8OXp8](https://youtu.be/skAD7R8OXp8)  

This guide covers:
1. **FalkorDB Configuration** (FalkorDB Cloud vs Local Docker vs In-Memory)
2. **Live Cloud Deployment** (Frontend on Vercel + Backend on Render/Railway + FalkorDB Cloud)
3. **1-Command Full-Stack Docker Deployment** (`docker compose up --build`)
4. **Complete Local Setup Instructions** (Windows, Linux, macOS)

---

## 1. FalkorDB Setup Options

FalkorDB is the primary context layer in CausalMesh. Every blast radius calculation, root cause investigation, playbook step, and "who knows what" attribution query runs directly in FalkorDB.

### Option A: FalkorDB Cloud (Recommended for Live Deployments)
1. Sign up for a free instance at [app.falkordb.cloud](https://app.falkordb.cloud).
2. Create a database subscription (free tier available).
3. Copy the host, port, username, and password from the dashboard.
4. Configure your environment:
   ```env
   FALKORDB_HOST=your-subdomain.falkordb.cloud
   FALKORDB_PORT=6379
   FALKORDB_PASSWORD=your_cloud_password
   FALKORDB_SSL=true
   ```
5. Seed the cloud graph with CausalMesh topology and memory:
   ```bash
   python backend/graph/seed.py
   ```

### Option B: Local Docker FalkorDB
Run official FalkorDB image with embedded FalkorDB Browser:
```bash
docker run -d -p 6379:6379 -p 3000:3000 --name causalmesh-falkordb falkordb/falkordb:latest
```
- FalkorDB Database: `localhost:6379`
- FalkorDB Visual Browser: `http://localhost:3000`

### Option C: Built-in In-Memory Engine (Zero Setup / Offline Demo)
If no external FalkorDB instance is detected, CausalMesh automatically activates its fast in-memory graph engine with identical OpenCypher syntax and GraphBLAS shortest-path traversals.

---

## 2. Live Cloud Deployment

You can deploy CausalMesh live across modern cloud platforms in less than 5 minutes:

### Step 1: Deploy Backend (Render / Railway / Cloud Run)

#### Using Render (Free Tier):
1. Create a new **Web Service** on [render.com](https://render.com) connected to your GitHub repository.
2. Select **Root Directory**: `backend`
3. Select **Environment**: `Python 3` (or choose `Docker` to use `backend/Dockerfile`).
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. Add Environment Variables:
   - `FALKORDB_HOST` = (Your FalkorDB Cloud host or omit for in-memory fallback)
   - `FALKORDB_PORT` = `6379`
   - `FALKORDB_PASSWORD` = (Your FalkorDB password)
   - `FALKORDB_SSL` = `true`
   - `OPENAI_API_KEY` / `GROQ_API_KEY` / `GOOGLE_API_KEY` = (Optional for live LLM mode)
7. Note down your backend URL: e.g., `https://causalmesh-backend.onrender.com`.

---

### Step 2: Deploy Frontend (Vercel)

#### Using Vercel:
1. Go to [vercel.com](https://vercel.com) and click **Add New Project**.
2. Import your CausalMesh GitHub repository.
3. Configure the project:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
4. Add Environment Variable:
   - `BACKEND_URL` = `https://causalmesh-backend.onrender.com`
5. Click **Deploy**.
6. Vercel automatically compiles the Next.js 14 frontend and proxies all `/api/*` and SSE streams to your live FastAPI backend.

---

## 3. 1-Command Full-Stack Docker Deployment

For single-server deployment (AWS EC2, DigitalOcean Droplet, Linode, Hetzner, etc.):

```bash
# Clone the repository
git clone https://github.com/yashv/causalmesh.git
cd causalmesh

# Build and start all 3 services: FalkorDB + Backend + Frontend
docker compose up --build -d
```

Services started:
- **Frontend**: `http://<your-server-ip>:3001`
- **Backend API**: `http://<your-server-ip>:8000` (Swagger UI at `/docs`)
- **FalkorDB Browser**: `http://<your-server-ip>:3000`
- **FalkorDB Database**: `<your-server-ip>:6379`

To view logs:
```bash
docker compose logs -f
```

To stop:
```bash
docker compose down
```

---

## 4. Complete Local Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- (Optional) Docker for live FalkorDB container

### 1-Click Startup Scripts

#### Windows (PowerShell):
```powershell
.\run-dev.ps1
```
*Automatically sets up virtual environment, installs dependencies, launches FastAPI backend on `:8000`, and launches Next.js frontend on `:3001`.*

#### Linux / macOS:
```bash
chmod +x run-dev.sh
./run-dev.sh
```

---

### Manual Step-by-Step Setup

#### 1. Start FalkorDB (Optional):
```bash
docker compose up -d falkordb
```
*(Skip if running in offline in-memory demo mode).*

#### 2. Setup & Start Backend:
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run all 37 tests to verify system health
python -m pytest -v

# Start FastAPI server
python main.py
```
Backend will be listening on `http://localhost:8000` with OpenAPI documentation at `http://localhost:8000/docs`.

#### 3. Setup & Start Frontend:
In a new terminal window:
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```
Open `http://localhost:3001` in your browser.

---

## 5. Verification Checklist

- [x] Backend healthcheck returns `{"status": "healthy"}` at `http://localhost:8000/health`.
- [x] All 37 pytest tests pass: `python -m pytest -v`.
- [x] Frontend builds with zero errors: `npm run build`.
- [x] Topology graph renders 25 nodes on Cytoscape.js canvas.
- [x] Triggering incident cascades visual path animation and populates postmortem.
- [x] Procedural Playbooks, Episodic Memory, and Company Brain modals open and display FalkorDB graph data.
