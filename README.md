# GreenPort DSS -- Developer Documentation

GreenPort is a web-based decision-support system (DSS) for strategic port decarbonization planning.

This repository contains the full source code of the application, structured as a frontend--backend system integrating a Python-based mixed-integer optimization model.

**Production deployment:**
https://greenport.it.ntnu.no/

**License:** MIT License

------------------------------------------------------------------------

# 1. System Overview

GreenPort is composed of three layers:

1.  Frontend (Vue 3)
2.  Backend API (Node.js + Express)
3.  Optimization Engine (Python + Google OR-Tools)

Architecture Flow:
```
Frontend (Vue 3)
↓ HTTP API
Node.js (Express)
↓ model_tank_index Python
Optimization Script
↓ Google OR-Tools (MIP Solver)
↓ JSON
Results
↓ Frontend Visualization
```

The optimization model is implemented using **Google OR-Tools (MPSolver)**.

------------------------------------------------------------------------

# 2. Repository Structure

```
Root/
│
├── frontend/ \# Vue 3 application
├── backend/ \# Node.js server
│ ├── server.js
│ └── model_tank_index.py
└── README.md
```

------------------------------------------------------------------------

# 3. Environment Requirements

-   Node.js \>= 16
-   npm \>= 8
-   Python \>= 3.9
-   pip
-   Google OR-Tools

Recommended:
- Python virtual environment
- ESLint-enabled IDE

------------------------------------------------------------------------

# 4. Frontend (Vue 3)

The frontend is implemented using Vue 3 and Bootstrap-Vue-3.

It provides:
- Step-based input forms
- Chart-based visualization
- Scenario comparison
- Export to Excel functionality

## 4.1 Tech Stack

### Core:
- vue \^3.5.13
- bootstrap \^5.3.3
- bootstrap-vue-3 \^0.3.12

### Visualization:
- chart.js \^4.1.1
- vue-chartjs \^5.3.2
- apexcharts \^4.5.0
- vue3-apexcharts \^1.8.0

### Data Export:
- exceljs \^4.4.0
- xlsx \^0.18.5
- file-saver \^2.0.5

### Utilities:
- lodash.clonedeep \^4.5.0

### Dev Tools:
- @vue/cli-service \^5.0.8
- eslint \^7.32.0

## 4.2 Install & Run (Frontend)

**Requirements**
- Node.js >= 16
- npm >= 8

```bash
cd frontend
npm install
npm run serve
```

------------------------------------------------------------------------

# 5. Backend (Node.js + Express)

The backend is a lightweight REST API server responsible for:

-   Receiving input data from frontend
-   Validating payload structure
-   Spawning Python optimization process
-   Returning solver results as JSON

## 5.1 Dependencies

-   express \^4.21.1
-   cors \^2.8.5

## 5.2 Install & Run (Backend)

Requirements: 
- Node.js \>= 16
- Python 3.9+
- OR-Tools installed

```bash
cd backend
npm install
node server.js
```

Ensure the Python executable and OR-Tools are available in your environment path.

------------------------------------------------------------------------

# 6. Optimization Engine (Python + OR-Tools)

The backend invokes a Python script via `model_tank_index.py`.

The script:

1.  Reads JSON input
2.  Constructs the mixed-integer model
3.  Solves using OR-Tools MPSolver
4.  Outputs structured JSON results

## 6.1 Python Dependencies

Standard:
- sys
- json
- math

Optimization:
- ortools

Install OR-Tools:
```
pip install ortools
```

Core import:
```
from ortools.linear_solver import pywraplp
```

## 6.2 Solver Characteristics

-   Mixed-integer programming (MIP)
-   Binary decision variables
-   Cost minimization objective

------------------------------------------------------------------------

# 7. API Execution Flow

1.  User submits scenario in frontend
2.  Frontend sends POST request (JSON payload)
3.  Express server receives request
4.  Server spawns Python optimization process
5.  Python script solves model
6.  Results returned as JSON
7.  Frontend renders charts and cost outputs

------------------------------------------------------------------------

# 8. Full Development Setup

Open two terminals:

Terminal 1 -- Backend:
```
cd backend
npm install
node server.js
```

Terminal 2 -- Frontend:
```
cd frontend
npm install
npm run serve
```

Ensure:
- Backend API URL is correctly configured in frontend
- Python and OR-Tools are properly installed

------------------------------------------------------------------------

# 9. Deployment Notes

The production version is available at:

https://greenport.it.ntnu.no/

Deployment requires:

-   Node.js runtime
-   Python runtime
-   OR-Tools installation
-   Reverse proxy (e.g., Nginx)
-   Process manager (e.g., PM2) recommended

------------------------------------------------------------------------

# 10. License

This project is licensed under the MIT License.

You may:
- Use
- Modify
- Distribute
- Integrate into other systems

provided that the original copyright and license notice are included.

------------------------------------------------------------------------

# 11. Contribution Guidelines

-   Maintain separation between UI and optimization logic
-   Do not embed solver logic in frontend
-   Keep optimization modifications inside Python script
-   Preserve API JSON structure
-   Validate input before solver execution

Pull requests should:
- Include a clear description
- Maintain backward compatibility
- Not break solver execution

------------------------------------------------------------------------

# 12. Research Context

GreenPort was developed as part of research on phased port decarbonization strategies using mixed-integer optimization models.

For academic use, please cite the associated publication (_to be updated_).
