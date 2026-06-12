# AutoForge Windows Docker Compatibility Notes

This document details critical configurations and behaviors when running the AutoForge Docker stack on Windows systems (using PowerShell, Command Prompt, or Git Bash with Docker Desktop).

---

## 1. AWS Credentials & Path Expansion (`~/.aws`)

The `docker-compose.yml` mounts host-level AWS credentials via:
```yaml
volumes:
  - ~/.aws:/root/.aws:ro
```

This functions reliably on Windows due to Docker Compose's native path resolution:

* **Tilde (`~`) Expansion**:
  When you execute `docker compose up`, the Docker Compose CLI resolves `~` relative to the environment:
  - **PowerShell / CMD**: Resolves to the user's home directory path (e.g. `C:\Users\syeda`).
  - **Git Bash / WSL**: Resolves to the Linux-equivalent path (e.g. `/c/Users/syeda` or `/home/username`).
  Docker Desktop then binds the resulting host folder directory into the Linux container's filesystem at `/root/.aws` as read-only.
  
* **Manual Override (Optional)**:
  If a developer's system has a non-standard home configuration, the volume path can be explicitly mapped using the `USERPROFILE` environment variable in a local terminal or `.env` override:
  `- ${USERPROFILE}/.aws:/root/.aws:ro`
  However, the default `~/.aws` works out-of-the-box for 99% of developers.

---

## 2. Line Endings (CRLF vs LF)

Windows natively uses CRLF (`\r\n`) line endings, while Linux containers use LF (`\n`). 

* **Interpreter Failures**:
  If python scripts or shell scripts written on Windows are copied into a container with CRLF endings and executed as entrypoints (e.g., `./entrypoint.sh`), Linux fails with `\r: command not found` or `no such file or directory`.
  
* **AutoForge Mitigation**:
  The AutoForge Docker configuration bypasses this risk by **avoiding shell script wrappers as entrypoints**. 
  Instead, entry points are executed directly via the binary arrays in the Dockerfiles:
  - `CMD ["uvicorn", "backend.main:app", ...]`
  - `CMD ["python", "simulator/main.py"]`
  - `CMD ["npm", "run", "dev", ...]`
  Because Python and Node.js parser engines natively handle Windows CRLF line endings when parsing source code files, editing code files on a Windows host using a bind mount does not cause syntax or parsing failures inside the Linux containers.

---

## 3. WSL 2 Engine & Mount Permissions

Docker Desktop on Windows should be configured to run with the **WSL 2 backend** (rather than Hyper-V) for optimal performance.

* **File System Access**:
  Docker Desktop manages file sharing permissions automatically for the `C:\Users` folder directory.
* **Volume Write Permissions**:
  The `data/` and `logs/` folders must be writeable by the containers. Because these directories exist inside the project directory and are mapped via the root mount `.:/app`, Docker Desktop's filesystem driver mirrors host permissions. Under Windows, container write operations to these folders succeed automatically without needing explicit `chmod` updates.
