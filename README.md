# AI-Powered API Performance Testing in CI/CD

**Automated AI-driven generation and execution of API performance tests using Jenkins, FastAPI, Groq LLM, and Apache JMeter.**

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Uvicorn-009688)
![JMeter](https://img.shields.io/badge/Apache%20JMeter-5.6.3%2B-D22128)
![Jenkins](https://img.shields.io/badge/CI%2FCD-Jenkins-D24939)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Key Features](#2-key-features)
3. [System Architecture](#3-system-architecture)
4. [Jenkins CI/CD Integration](#4-jenkins-cicd-integration)

7. [Project Structure](#6-project-structure)
7. [Technologies](#7-technologies)
8. [Prerequisites](#8-prerequisites)
9. [Installation and Setup](#9-installation-and-setup)
10. [Configuration](#10-configuration)
11. [Usage](#11-usage)
12. [REST API Reference](#12-rest-api-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [Known Limitations](#14-known-limitations)
15. [Future Improvements](#15-future-improvements)
16. [Author](#author)
17. [License](#license)

---

## 1. Overview

This project introduces an AI-driven approach to automating API performance testing within a CI/CD pipeline.

Integrated with **Jenkins**, the solution automates the generation and execution of load testing scenarios from OpenAPI specifications, reducing manual intervention in the performance testing process.

A FastAPI-based service acts as the AI-powered generation engine, using a Large Language Model (LLM) provided by **Groq** to analyze API specifications and design appropriate performance testing scenarios.

The generated scenarios are converted into Apache JMeter (`.jmx`) test plans and executed automatically as part of the Jenkins pipeline.

### Workflow

1. Jenkins retrieves the OpenAPI specification from the project repository.
2. The specification is sent to the FastAPI service.
3. The AI engine analyzes the API and generates a load testing scenario.
4. The scenario is converted into an executable JMeter test plan.
5. Apache JMeter executes the generated test.
6. Jenkins collects execution results, logs, and performance reports.

### Main Objectives

- Automate API performance test generation using LLMs.
- Integrate AI-driven testing into an existing CI/CD workflow.
- Reduce manual JMeter test plan configuration.
- Enable automated performance testing from OpenAPI specifications.
- Collect and expose test execution results within the pipeline.

---

## 2. Key Features

### OpenAPI Specification Analysis

- Support for OpenAPI specifications in **YAML** and **JSON** formats.
- Automatic extraction and analysis of API endpoints.
- Identification of HTTP methods, paths, parameters, and request information.

### AI-Powered Scenario Generation

- LLM-based design of load testing scenarios.
- Automatic definition of virtual users, ramp-up period, and loop count.
- Intelligent organization and sequencing of API requests.
- Generation based on the analyzed API specification.

### JMeter Test Plan Generation

- Automatic generation of executable `.jmx` files.
- Integration with a reusable JMeter template.
- Configuration of HTTP requests and test execution parameters.

### Asynchronous Test Execution

- Background execution through Apache JMeter.
- Unique job identification using `jobId`.
- Execution status monitoring.
- Retrieval of logs and execution artifacts.

### Performance Results and Reporting

- Raw JMeter results (`.jtl`).
- Detailed execution logs.
- Standard output capture.
- HTML performance reports.

---

## 3. System Architecture

The platform follows a modular architecture separating API endpoints, specification analysis, AI-based scenario generation, JMeter test plan creation, and test execution.

```text
                   Developer / QA Engineer
                            |
                            v
                   OpenAPI Specification
                      YAML / JSON
                            |
                            v
                 +----------------------+
                 |    FastAPI Server    |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 |   OpenAPI Analyzer   |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 |  Scenario Generator  |
                 |      (Groq LLM)      |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 |     JMX Generator    |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 |    Apache JMeter     |
                 +----------------------+
                            |
                            v
                 +----------------------+
                 |  Execution Results   |
                 +----------------------+
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
           Logs          JTL Files     HTML Reports
```

---

## 4. Jenkins CI/CD Integration

The solution integrates AI-powered API performance testing into a Jenkins pipeline.

Jenkins orchestrates the testing workflow, while the FastAPI service handles OpenAPI analysis and AI-based scenario generation.

### Pipeline Workflow

| Stage | Description |
|---|---|
| **Specification Retrieval** | Retrieve the OpenAPI specification from the source repository. |
| **AI Scenario Generation** | Send the specification to the FastAPI service. |
| **JMeter Test Execution** | Execute the generated JMX test plan. |
| **Results Collection** | Collect JMeter logs, JTL files, and HTML reports. |
| **Pipeline Status** | Report the execution outcome through Jenkins. |

### Integration Components

| Component | Responsibility |
|---|---|
| Jenkins | CI/CD pipeline orchestration |
| FastAPI | AI scenario generation service |
| Groq LLM | OpenAPI analysis and scenario design |
| Apache JMeter | Load test execution |
| Docker | Service containerization |
| Prism | API mocking, when enabled |

### Example Pipeline Steps

The following shell commands illustrate how a Jenkins stage can interact with the service (adapt them to your own `Jenkinsfile`):

```bash
# 1. Submit the OpenAPI specification
curl -X POST "http://fastapi-host:8000/generateScenario" \
  -F "file=@openapi.json" \
  -F "threads=50" -F "rampUp=10" -F "loops=5"

# 2. Poll the execution status using the returned jobId
curl "http://fastapi-host:8000/status/JOB_ID"

# 3. Archive the artifacts
curl -o results.jtl  "http://fastapi-host:8000/download/JOB_ID/jtl"
curl -o report.zip   "http://fastapi-host:8000/download/JOB_ID/report"
```

---

## 6. Project Structure

```text
AI-Performance-Testing/
│
├── api/
│   ├── __init__.py
│   └── routes.py
│
├── docs/
│   └── images/
│
├── examples/
│   └── petstore.json
│
├── models/
│   ├── __init__.py
│   ├── request_models.py
│   └── scenario_model.py
│
├── prompts/
│   ├── __init__.py
│   ├── scenario_prompt.py
│   └── system_prompt.py
│
├── scripts/
│   ├── setup_monitoring.bat
│   └── start_test.bat
│
├── services/
│   ├── __init__.py
│   ├── api_analyzer.py
│   ├── file_service.py
│   ├── groq_client.py
│   ├── jmeter_executor.py
│   ├── jmx_generator.py
│   ├── job_store.py
│   ├── json_cleaner.py
│   ├── openapi_parser.py
│   ├── prism_service.py
│   ├── scenario_generator.py
│   └── target_resolver.py
│
├── templates/
│   └── jmeter_template.jmx
│
├── generated/              # Generated test plans and reports
├── uploads/                # Uploaded API specifications
├── workspace/              # Temporary execution files
├── logs/                   # Application and execution logs
│
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 7. Technologies

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Artificial Intelligence | Groq API, LLM |
| CI/CD | Jenkins |
| Data Validation | Pydantic |
| Specification Processing | OpenAPI, PyYAML |
| Performance Testing | Apache JMeter 5.6.3+ |
| Mock API | Prism |
| Containerization | Docker, Docker Compose |
| Version Control | Git, GitHub |

---

## 8. Prerequisites

Before running the application, make sure the following tools are installed:

- Python 3.13
- Apache JMeter 5.6.3 or later (for local execution)
- Docker Desktop or Docker Engine (for containerized execution)
- A valid Groq API key

---

## 9. Installation and Setup

### 9.1 Clone the repository

```bash
git clone https://github.com/SihamBouzagrar/AI-PoweredAI-Performance-Testing-in-CI_CD.git
cd AI-PoweredAI-Performance-Testing-in-CI_CD
```

### 9.2 Configure environment variables

Create a `.env` file from the provided example.

Linux / macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit the `.env` file:

```env
GROQ_API_KEY_V2=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

> **Warning:** Never commit your actual `.env` file or expose your API key.

### 9.3 Local installation

Create and activate a Python virtual environment.

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure the JMeter executable path using the variable expected by your local application configuration (see [Configuration](#10-configuration)).

Start the FastAPI server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Access the interactive API documentation:

```text
http://localhost:8000/docs
```

### 9.4 Docker installation

Configure the `.env` file, then build and start the service:

```bash
docker compose up -d --build
```

Check the container status:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs -f fastapi
```

---

## 10. Configuration

The application uses environment variables to configure the AI provider and testing environment.

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key read by the Python application |
| `GROQ_API_KEY_V2` | Variable used by Docker Compose to inject the key as `GROQ_API_KEY` |
| `GROQ_MODEL` | LLM model used for scenario generation |
| `JMETER_BIN` | Local JMeter executable path, if used by the application |
| `JMETER_EXECUTABLE` | JMeter executable path configured in Docker |
| `PRISM_HOST` | Prism mock server host, if required |
| `PRISM_PORT` | Prism mock server port |
| `API_HOST` / `API_PORT` | FastAPI server configuration, if supported |

> **Note:** The actual variable names must match the application's configuration and Docker Compose file.

---

## 11. Usage

### 11.1 Generate and execute a test scenario

Send an OpenAPI specification to the generation endpoint:

```bash
curl -X POST "http://localhost:8000/generateScenario" \
  -F "file=@examples/petstore.json"
```

Optional workload parameters can also be supplied:

```bash
curl -X POST "http://localhost:8000/generateScenario" \
  -F "file=@examples/petstore.json" \
  -F "threads=50" \
  -F "rampUp=30" \
  -F "loops=5"
```

### 11.2 Monitor execution status

Use the returned `jobId` to monitor the test:

```bash
curl "http://localhost:8000/status/JOB_ID"
```

### 11.3 Retrieve execution artifacts

Download the JMeter execution log:

```bash
curl -o jmeter.log "http://localhost:8000/download/JOB_ID/log"
```

Download standard output:

```bash
curl -o stdout.log "http://localhost:8000/download/JOB_ID/stdout"
```

Download raw JMeter results:

```bash
curl -o results.jtl "http://localhost:8000/download/JOB_ID/jtl"
```

Download the HTML report archive:

```bash
curl -o report.zip "http://localhost:8000/download/JOB_ID/report"
```

---

## 12. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generateScenario` | Upload specification and generate a test scenario |
| `GET` | `/status/{jobId}` | Retrieve execution status |
| `GET` | `/download/{jobId}/log` | Download JMeter logs |
| `GET` | `/download/{jobId}/stdout` | Download standard output |
| `GET` | `/download/{jobId}/jtl` | Download raw JMeter results |
| `GET` | `/download/{jobId}/report` | Download the HTML report archive |

### `POST /generateScenario`

**Request:** `multipart/form-data`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | OpenAPI specification |
| `threads` | Integer | No | Number of virtual users |
| `rampUp` | Integer | No | Ramp-up period |
| `loops` | Integer | No | Number of iterations |

**Example response:**

```json
{
  "jobId": "example-job-id",
  "status": "QUEUED",
  "jmxFile": "generated/scenario_xxx.jmx"
}
```

### `GET /status/{jobId}`

**Example response:**

```json
{
  "jobId": "example-job-id",
  "status": "RUNNING",
  "error": null
}
```

**Possible execution states:**

| Status | Meaning |
|---|---|
| `QUEUED` | Job created, waiting to start |
| `RUNNING` | JMeter test in progress |
| `COMPLETED` | Execution finished successfully |
| `FAILED` | Execution failed (see `error` field) |

---

## 13. Troubleshooting

### HTTP 409 — Report not available

The test execution may still be running. Check its status before downloading the report:

```bash
curl "http://localhost:8000/status/JOB_ID"
```

### JMeter executable not found

Check the JMeter executable path configured for the current environment.

For a local Windows installation, an example is:

```env
JMETER_BIN=C:\jmeter\apache-jmeter-5.6.3\bin\jmeter.bat
```

For Docker, use the executable path inside the container.

### Groq API configuration error

Verify that the API key is correctly configured and injected into the FastAPI container.



---

## 14. Known Limitations

- **In-memory job storage:** job information is stored in memory and is not shared between multiple application workers or replicas. A shared backend such as Redis or a relational database would be needed for distributed execution.
- **API security:** authentication and authorization are not currently implemented. Additional security controls are required before exposing the service beyond a trusted internal network.
- **LLM dependency:** scenario generation depends on the availability and response quality of the configured LLM provider.
- **Execution environment:** JMeter and target API connectivity must be correctly configured for each deployment environment.

---

## 15. Future Improvements

- Persistent job management using Redis or PostgreSQL.
- Authentication and role-based access control.
- Advanced performance metrics analysis and visualization.
- AI-assisted interpretation of JMeter execution results.
- Native Jenkins plugin / shared library for easier pipeline integration.
- Support for additional LLM providers.
- Automated comparison of performance results across test runs.

---

## Author

**Siham Bouzagrar**
GitHub: [@SihamBouzagrar](https://github.com/SihamBouzagrar)

---

## License

This project was developed as part of an internship project in an enterprise environment.

**All Rights Reserved.** No reuse, distribution, modification, or commercial exploitation is permitted without prior authorization from the project owner and, where applicable, the relevant organization.