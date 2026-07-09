---
title: "UIS (local)"
sidebar_label: "UIS (local)"
sidebar_position: 1
description: "Set up Urbalurba Infrastructure Stack locally via Rancher Desktop, and point a language's E2E test at it."
---

# Testing against UIS

[UIS (Urbalurba Infrastructure Stack)](https://uis.sovereignsky.no/) is "a complete datacenter on your laptop" — a Kubernetes-based local infrastructure platform, installed via a small CLI that provisions services (including a full observability stack) onto a local cluster. This page documents standing it up and pointing a language's E2E test at it — the process is the same shape for any future backend documented under [Testing backends](index.md). Steps 1–3 are shared; step 4 covers TypeScript and step 6 covers Python — both have been verified end-to-end against a live UIS stack.

## 1. Prerequisite: Kubernetes enabled in Rancher Desktop

UIS needs a local Kubernetes cluster. In Rancher Desktop's settings, enable Kubernetes (off by default). Confirm it's up:

```bash
kubectl config current-context   # should print: rancher-desktop
kubectl get nodes                # should show one Ready control-plane node
```

## 2. Install the UIS CLI and start it

From any directory outside this repo (UIS is a general-purpose local infrastructure tool, not part of sovdev-logger itself):

```bash
curl -fsSL https://raw.githubusercontent.com/helpers-no/urbalurba-infrastructure/main/uis -o uis
chmod +x uis
./uis start
```

`./uis start` pulls a provisioning container (`ghcr.io/helpers-no/uis-provision-host`), initializes `.uis.extend/` (config, safe to commit) and `.uis.secrets/` (gitignored), and applies a base set of Kubernetes secrets and namespaces — including `monitoring`, which is what the rest of this page uses.

## 3. Install the observability stack

```bash
./uis stack install observability
```

This deploys **Prometheus, Tempo, Loki, an OpenTelemetry Collector, and Grafana** into the `monitoring` namespace via Ansible + Helm, and — notably — the installer itself runs a full end-to-end validation before declaring success: it sends real test logs/traces/metrics through the OTel Collector and queries each backend to confirm they arrived. Confirmed on a real run: all three pipelines (logs→Loki, traces→Tempo, metrics→Prometheus) reported `PASS`, and Grafana's datasource connectivity to all three was verified the same way.

**Endpoints this leaves you with** (from the installer's own output, all routed through Traefik on `localhost`, no port needed):

| What | URL | Notes |
|---|---|---|
| OTLP HTTP (logs/traces/metrics) | `http://otel.localhost/v1/logs`, `/v1/traces`, `/v1/metrics` | IngressRoute matches `HostRegexp: otel\..+` — the `Host` header is what routes the request, not the domain name resolving to a specific IP |
| Grafana UI | `http://grafana.localhost` | `admin` / `SecretPassword1` |

UIS also deploys a **"Sovdev Logger - Overview"** Grafana dashboard by default as part of this stack — it's built with this project specifically in mind.

## 4. Point the TypeScript E2E test at it

The sovdev-logger devcontainer can't resolve `otel.localhost` directly (it's a hostname Traefik matches on the host's network, not a name any DNS resolves) — from inside the devcontainer, reach it via `host.docker.internal` with an explicit `Host` header instead. Copy `typescript/test/e2e/company-lookup/.env.example` to `.env` in the same directory — it already has the right values:

```bash
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://host.docker.internal/v1/logs
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://host.docker.internal/v1/metrics
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://host.docker.internal/v1/traces
OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}'
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
```

**The single quotes around `OTEL_EXPORTER_OTLP_HEADERS`'s value are load-bearing.** `run-test.sh` loads `.env` with `source`, and bash strips unquoted/double-quoted `"` characters during word-splitting — an unquoted `{"Host":"otel.localhost"}` becomes the invalid JSON `{Host:otel.localhost}` by the time the SDK sees it. This doesn't fail loudly: `JSON.parse` throws inside `configure_opentelemetry()`, which is caught and logged as a warning, so the app keeps running — but the `TracerProvider` never initializes, and every `sovdev_start_span()` call downstream fails with `"TracerProvider not initialized. Call sovdev_initialize() first."` This is exactly what happened the first time — all 4 company lookups failed, not just the one that's supposed to fail. Fixing the quoting fixed all of it in one move.

## 5. Run the TypeScript test and verify data actually arrived

```bash
dct-exec bash -c "cd /workspace/typescript/test/e2e/company-lookup && bash run-test.sh"
```

(`dct-exec` is this repo's devcontainer-toolbox host helper — it finds the running devcontainer via a Docker label instead of a fixed name. Install it via `curl -fsSL https://raw.githubusercontent.com/helpers-no/devcontainer-toolbox/main/install.sh | bash` if it's not already on your `PATH`. The older `specification/tools/in-devcontainer.sh` wrapper hardcoded a container name that no longer matches how the devcontainer actually runs — it's been deleted in favor of `dct-exec`.)

Expected result: **17 log entries** (matching `08-testprogram-company-lookup.md`'s documented scenario — 3 successful lookups, 1 intentional failure), schema validation passing with real trace/span IDs found, and a clean OTLP flush/shutdown.

Passing schema validation only proves the file log is well-formed — it doesn't prove the data reached the backend. Confirm that separately:

```bash
dct-exec bash -c "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-typescript"
dct-exec bash -c "cd /workspace/specification/tools && ./query-tempo.sh sovdev-test-company-lookup-typescript"
dct-exec bash -c "cd /workspace/specification/tools && ./query-prometheus.sh sovdev-test-company-lookup-typescript"
```

All three should report the service found with data present. Confirmed working end-to-end this way before writing this page.

## 6. Point the Python E2E test at it — and the quoting difference

Python's E2E test (`python/test/e2e/company-lookup/`) uses the exact same UIS endpoints and headers, and works the same way: copy `.env.example` to `.env` in that directory, then run it via `dct-exec`:

```bash
dct-exec bash -c "cd /workspace/python/test/e2e/company-lookup && bash run-test.sh"
```

**The single-quoting requirement from step 4 does not apply here.** TypeScript's `run-test.sh` loads `.env` with bash's `source`, which needs the quotes to protect the JSON in `OTEL_EXPORTER_OTLP_HEADERS` from word-splitting. Python's test loads `.env` with `python-dotenv`'s `load_dotenv()` (in `company-lookup.py`), which doesn't do shell-style parsing — the unquoted value works as-is:

```bash
OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}
```

Confirmed empirically, not assumed: this exact unquoted value was tested first (before trying a quoted one), and it worked on the first run — 17 log entries, correct 3-success/1-failure pattern, `TracerProvider` initialized correctly. Verified the data landed the same way as TypeScript:

```bash
dct-exec bash -c "cd /workspace/specification/tools && ./query-loki.sh sovdev-test-company-lookup-python"
dct-exec bash -c "cd /workspace/specification/tools && ./query-tempo.sh sovdev-test-company-lookup-python"
dct-exec bash -c "cd /workspace/specification/tools && ./query-prometheus.sh sovdev-test-company-lookup-python"
```

All three reported the service found with data present, and a subsequent `compare-with-master.sh python` run still reported a clean match against TypeScript's output — testing against a live backend didn't change Python's behavior relative to the reference implementation.
