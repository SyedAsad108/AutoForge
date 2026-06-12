# AutoForge Python Dependency Audit Report

This document audits the deployment of the AWS Python SDK (`boto3`) across the AutoForge platform packages. It details where `boto3` is needed, how it is managed within isolated container runtimes, and the rationale behind the dependency layout.

---

## 1. Audit Matrix: `boto3` Locations

We verified the requirements files across the workspace:

| Target Environment | Configuration File | `boto3` Status | Purpose / Runtime Context |
| :--- | :--- | :---: | :--- |
| **Root Workspace** | `requirements.txt` | **Present** | Local host development environment. Installed when running python processes directly on the host machine without Docker. |
| **FastAPI Backend** | `backend/requirements.txt` | **Present** | Backend API container. Required to run `backend/services/athena_client.py` which executes Athena analytics queries. |
| **Factory Simulator**| `simulator/requirements.txt` | **Present** | Simulator container. Required to run `simulator/streaming/transport/kinesis_client.py` which streams telemetry directly to AWS Kinesis. |

---

## 2. Why `boto3` Exists in Multiple Locations

Although it seems like duplicate declarations, maintaining `boto3` in all three files is **strictly necessary** and is a best practice for containerized applications:

1. **Isolation of Runtimes**:
   In Docker Compose, the `backend` and `simulator` build distinct container images. They do not share a file system or python environment at runtime.
   - The `backend` container builds using only `backend/requirements.txt`.
   - The `simulator` container builds using only `simulator/requirements.txt`.
   If `boto3` were only declared in the root `requirements.txt`, both containers would experience a `ModuleNotFoundError` during startup when executing boto3 imports.

2. **Root Workspace Development**:
   A developer working locally might run the application directly on their host machine (e.g. `uvicorn backend.main:app` or `python simulator/main.py`). They install dependencies from the root `requirements.txt`. Having `boto3` there ensures local non-container runs work without manually digging into subdirectory packages.

---

## 3. Recommendations & Conclusion

* **Keep Declarations Segmented**: Do NOT attempt to consolidate the requirements files. Doing so would break the container build cache and self-containment of the Docker images.
* **Keep Version Constraints Aligned**: Ensure all three requirements files reference compatible versions of `boto3` (currently all set to `boto3>=1.34.0`) to prevent API variance between containerized runs and local host runs.
* **Conclusion**: The current setup is **correct**, verified, and optimized for Docker container separation.
