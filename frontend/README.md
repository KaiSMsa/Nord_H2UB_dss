# NORD_H2UB DSS – Green Port Planner

Decision support tool with:
- **Frontend**: Vue 3 (Vue CLI) web UI (dev server on `http://localhost:3000`)
- **Backend**: Node.js server
- **Optimization engine**: Python environment providing **OR-Tools** (installed in a virtual environment)

---

## Architecture

### Components
1. **Frontend (Vue 3)**
   - Runs a development server on port **3000**
   - Builds a static bundle (`dist/`) for deployment behind Nginx
   - Communicates with the backend via HTTP (API endpoints)

2. **Backend (Node.js)**
   - Provides REST endpoints used by the frontend
   - Calls/uses Python logic where OR-Tools is required (via the project’s Python virtualenv)

3. **Python venv (OR-Tools)**
   - Installed and managed under `backend/myenv`
   - Provides the `ortools` package used for optimization