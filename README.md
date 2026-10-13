# Labzs Demo Environment

This repository contains a collection of Docker-based demo and lab services designed to run behind a shared Traefik reverse proxy. The environment is set up for local experimentation and proof-of-concept deployments, with apps exposed through hostnames under the `labzs.com` domain.

> This setup is intentionally convenience-focused. Many container defaults are sample credentials or placeholder values and should be changed before using the stack in a real or shared environment.

## Overview

The repo is organized as independent service folders, each with its own Compose file and app-specific configuration. Traefik sits in front of the stack and provides routing, TLS termination, and a shared Docker network.

### Included services

| Service | Directory | URL / Access | Notes |
| --- | --- | --- | --- |
| Traefik | `traefik/` | `https://traefik.labzs.com` | Reverse proxy and dashboard |
| Jenkins | `jenkins/` | `https://jenkins.labzs.com` | CI/CD server |
| GitLab | `gitlab/` | `https://gitlab.labzs.com` | Self-hosted Git platform |
| Confluence | `confluence/` | `https://confluence.labzs.com` | Atlassian collaboration app |
| SuiteCRM | `suitecrm/` | `https://suitecrm.labzs.com` | CRM application |
| Snipe-IT | `snipe-it/` | `https://snipe-it.labzs.com` | IT asset management |
| LibreNMS | `librenms/` | `https://librenms.labzs.com` | Network monitoring |
| Splunk | `splunk/` | `https://splunk.labzs.com` | Log analytics |
| Open WebUI / Ollama | `ollama/` | `https://chat.labzs.com` | Local AI chat stack |
| Messages app | `messages/` | `https://messages.labzs.com` | Demo service with UI + API |
| Moon tracker | `moon-tracker/` | `http://moon.labzs.com` | Demo app using plain HTTP |
| Uptime Kuma | `uptime-kuma/` | `https://uptime.labzs.com` | Status monitoring |
| IoT Dashboard | `iot-dashboard/` | `https://iot-dashboard.labzs.com` | Device check-in dashboard |

## Repository structure

- `traefik/` — shared reverse proxy, TLS cert folder, Traefik config
- `gitlab/`, `jenkins/`, `confluence/`, `suitecrm/`, `snipe-it/`, `librenms/`, `splunk/` — platform and monitoring services
- `ollama/` — local LLM stack via Ollama and Open WebUI
- `messages/`, `moon-tracker/` — lightweight demo apps
- `uptime-kuma/` — uptime monitoring
- `iot-dashboard/` — custom IoT device dashboard

## Prerequisites

- Docker Engine
- Docker Compose v2 (`docker compose`)
- A local resolver or hosts file mapping for the `*.labzs.com` names
- Wildcard certificate files for TLS termination

## Quick start

### 1) Create the shared Docker network

```bash
docker network create proxy
```

If the network already exists, Docker will report that it already exists and the command can be ignored.

### 2) Prepare TLS certificates

The Traefik proxy expects a wildcard cert and private key in the `traefik/certs` directory:

```text
traefik/certs/labzs.com.crt
traefik/certs/labzs.com.key
```

This is documented in [traefik/certs/README.md](traefik/certs/README.md).

### 3) Start Traefik

```bash
cd traefik
docker compose up -d
```

### 4) Start the services you need

Each app directory contains its own Compose file. For example:

```bash
cd jenkins
docker compose up -d
```

Or for multiple services:

```bash
cd gitlab
docker compose up -d
cd confluence
docker compose up -d
```

## Local hostnames

For local testing, add entries similar to the following to your hosts file:

```text
127.0.0.1 traefik.labzs.com jenkins.labzs.com gitlab.labzs.com confluence.labzs.com suitecrm.labzs.com snipe-it.labzs.com librenms.labzs.com splunk.labzs.com chat.labzs.com messages.labzs.com moon.labzs.com uptime.labzs.com iot-dashboard.labzs.com
```

On Linux/macOS, edit `/etc/hosts`.
On Windows, edit `C:\Windows\System32\drivers\etc\hosts` as Administrator.

## Notes and caveats

- Traefik is the public entry point for all services on the `proxy` network.
- Some services use `websecure` and expect TLS certificates at the reverse proxy layer.
- A few apps use demo credentials or placeholder values and should be updated before production-like usage.
- The project is intended for lab/demo usage rather than hardened production deployment.
- Services are not all started at once by default; each folder is meant to be launched independently.

## Example service health checks

Once the proxy is running, you can check the dashboard and app endpoints in a browser:

- `https://traefik.labzs.com`
- `https://jenkins.labzs.com`
- `https://gitlab.labzs.com`
- `https://chat.labzs.com`
- `https://uptime.labzs.com`

## Security reminder

This stack includes several internet-facing applications and user accounts. Before using it beyond a lab environment:

- rotate default credentials and API keys
- restrict network exposure
- review Docker volumes and backups
- replace placeholder SMTP and database settings
- consider using proper DNS and certificates instead of local wildcard certificate files

## Useful commands

```bash
# Check running containers
docker ps

# View logs for a service
docker compose logs -f

# Stop a service
docker compose down

# Restart a service
docker compose restart
```

This repo is a demo environment for experimenting with multiple self-hosted services behind a single Traefik gateway. Use it as a starting point for a larger hybrid lab or internal tooling stack.

