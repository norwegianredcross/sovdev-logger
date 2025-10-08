# Development Environment Rules

**File**: `.terchris/rules-environment.md`
**Purpose**: Define patterns for working with DevContainer Toolbox and cross-platform development
**Target Audience**: LLM assistants, developers setting up local environment
**Last Updated**: October 07, 2025

## 📋 Overview

This document establishes rules for working with the sovdev-logger development environment, including DevContainer Toolbox usage, file system access patterns, and network connectivity to host services.

## Environment Architecture

### DevContainer Toolbox Setup

This repository uses the **DevContainer Toolbox** - a standardized development container that provides a consistent environment across all platforms (Mac, Windows, Linux).

**Key Components:**
- `.devcontainer/` - Core toolbox (DO NOT EDIT - shared across projects)
- `.devcontainer.extend/` - Project-specific customizations
- Container name: `devcontainer-toolbox`
- Base image: Debian 12 (bookworm) with Python 3.11, Node.js 22, Azure CLI, PowerShell
- User: `vscode` (non-root)
- Workspace mount: Host project root → Container `/workspace` (always mounted at this path regardless of host location)

## How Claude Code Should Work with the DevContainer

### 1. File System Access

Claude has **dual access** to the codebase:

**Host Access:**
```bash
# Direct file operations on host filesystem (Mac/Windows/Linux)
# Use the actual host path provided by the working directory
Read <host-project-root>/file.ts
Edit <host-project-root>/file.ts
```

**Container Access (for execution):**
```bash
# Execute commands inside the devcontainer
docker exec devcontainer-toolbox bash -c "cd /workspace && npm install"
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm test"
```

### 2. When to Use Each Access Method

| Task | Use | Reason |
|------|-----|--------|
| Read files | **Host (Read tool)** | Faster, direct access |
| Edit files | **Host (Edit/Write tools)** | Changes immediately visible to user |
| Run npm/node commands | **Container** | Correct Node.js version (22.20.0) |
| Run Python scripts | **Container** | Correct Python version (3.11.13) |
| Install dependencies | **Container** | Isolated environment |
| Build/compile code | **Container** | Consistent toolchain |
| Run tests | **Container** | Production-like environment |

### 3. Command Execution Pattern

**Template for running commands in devcontainer:**
```bash
docker exec devcontainer-toolbox bash -c "cd /workspace/[subdir] && [command]"
```

**Examples:**
```bash
# Install TypeScript dependencies
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm install"

# Run TypeScript code
docker exec devcontainer-toolbox bash -c "cd /workspace/typescript && npm start"

# Run Python script
docker exec devcontainer-toolbox bash -c "cd /workspace && python test-script.py"

# Check Node.js version
docker exec devcontainer-toolbox node --version

# Check Python version
docker exec devcontainer-toolbox python --version
```

### 4. Important Notes

**DO NOT use `-it` flags:**
```bash
# ❌ Wrong - will fail with "input device is not a TTY"
docker exec -it devcontainer-toolbox bash

# ✅ Correct - works in Claude's non-interactive environment
docker exec devcontainer-toolbox bash -c "command"
```

**File changes are bidirectional:**
- Changes made on host (via Read/Edit/Write) are immediately visible in container
- Changes made in container are immediately visible on host (same filesystem mount)

**Container lifecycle:**
- Container starts when user opens the project in VSCode
- Container stops when user closes VSCode (configured via `shutdownAction`)
- Claude should assume the container is running during the session

### 5. Troubleshooting DevContainer Access

**Check if container is running:**
```bash
docker ps --filter name=devcontainer-toolbox
```

**View container logs:**
```bash
docker logs devcontainer-toolbox
```

**Check workspace mount:**
```bash
docker exec devcontainer-toolbox ls -la /workspace
```

## Typical Project Structure (with DevContainer Toolbox)

```
<project-root>/
├── .devcontainer/          # Core toolbox (57 files, all tools/languages)
├── .devcontainer.extend/   # Project-specific setup
├── .terchris/              # Claude rules and plans (optional)
├── src/ or typescript/     # Source code (varies by project)
├── docs/                   # Documentation (optional)
└── [project-specific files]
```

**Note:** The `.devcontainer/` and `.devcontainer.extend/` folders indicate this project uses the DevContainer Toolbox.

## Development Workflow

1. **User opens project in VSCode** → DevContainer starts automatically
2. **Claude reads/edits files** → Use host filesystem paths
3. **Claude runs code** → Execute via `docker exec` in container
4. **User sees results** → Both in terminal and file changes

## Pre-installed Tools in DevContainer

Available without installation:
- Node.js v22.20.0 + npm
- Python 3.11.13
- PowerShell 7.5.2
- Azure CLI 2.77.0
- Git (with auto-configured identity)
- Standard development tools (curl, wget, git, etc.)

Additional languages available via `.devcontainer/additions/install-*.sh` scripts:
- TypeScript (via Node.js + npm)
- C# / .NET
- Go
- Java
- PHP / Laravel
- Rust
- Data analytics (pandas, numpy, etc.)

## DevContainer Networking to Host

When code running **inside the devcontainer** needs to access services on the **host machine** (e.g., Kubernetes cluster via Rancher Desktop):

### Host Gateway Addresses

**Recommended: `host.docker.internal`**
- Cross-platform DNS name (Mac, Windows, Linux)
- Automatically resolves to host machine
- Example: `http://host.docker.internal/v1/logs`

**Alternative: `172.17.0.1`**
- Docker bridge gateway IP
- Direct IP address
- May vary on different Docker setups

### Testing Connectivity

```bash
# From inside devcontainer
docker exec devcontainer-toolbox curl -H 'Host: grafana.localhost' http://host.docker.internal/

# Should return HTTP response from host's Traefik ingress
```

### Environment Configuration

Code should use environment variables for flexibility:

```typescript
const KUBE_HOST = process.env.KUBE_HOST || 'host.docker.internal';
const OTEL_ENDPOINT = `http://${KUBE_HOST}/v1/logs`;
```

See `typescript/.env.example` for complete configuration.

## Summary

**Key Rules:**
1. Read and write files on the host, execute code in the devcontainer
2. Use `host.docker.internal` to reach host services from devcontainer
3. Use environment variables for configuration flexibility

This ensures:
- Fast file operations
- Correct execution environment
- Consistent behavior across platforms
- Changes visible to both Claude and user
- Code works in both devcontainer and host environments
