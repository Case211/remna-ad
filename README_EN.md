# Remnawave Admin Bot

**Available languages:** [Русский](README.md)

Telegram bot for administering Remnawave: manage users, nodes, inbounds, and statistics. Optimised for mobile usage and production deployments.

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://github.com/Case211/remna-ad/pkgs/container/remna-ad)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

Contact points:
- [openode.xyz](https://openode.xyz)
- [neonode.cc](https://neonode.cc)
- [GitHub – Case211](https://github.com/Case211)
- [Telegram](https://t.me/ispanec_nn)

### Key Features
- **Users:** search (username/UUID/Telegram/email/tag), create/edit, enable/disable, traffic reset, HWID devices, statistics.
- **Nodes:** enable/disable/restart, certificate management, metrics, and online users.
- **Inbounds:** manage entry points, perform bulk actions for users and nodes.
- **Bulk actions:** reset traffic, remove inactive/expired items, batch updates.
- **Statistics:** aggregated and minute-level views with clear formatting and indicators.
- **Mobile-first UI:** pagination with 6–8 items, intuitive navigation, quick actions.

### What’s New
- Faster polling: `poll_interval` reduced to 0.5s.

eGames's script related Wiki: [`wiki.egam.es`](https://wiki.egam.es/)

### Cookie-based Authorisation (eGames)
1. Obtain cookies from the Remnawave panel using the guide: https://wiki.egam.es/configuration/external-api/#accessing-api-through-cookies.
2. Store them in "NAME=VALUE" JSON and set the string in `REMNAWAVE_COOKIES` (example: `{NAME:VALUE}`).
3. Optionally use the fallback `COOKIES` variable.

## Quick Start

### Roles and Permissions
- `Administrator` — full bot and panel access.
- `Operator` — read-only access to lists, statistics, and details.

### Docker (recommended)
1. Prepare the directory and download configs:
```bash
sudo mkdir -p /opt/remna-bot
cd /opt/remna-bot
curl -o .env https://raw.githubusercontent.com/Case211/remna-ad/main/.env.example
curl -o docker-compose.yml https://raw.githubusercontent.com/Case211/remna-ad/main/docker-compose-prod.yml
```
2. Configure environment variables:
```bash
nano .env
```
3. Launch:
```bash
docker compose up -d
```
4. Logs:
```bash
docker compose logs -f
```

### Manual Run
```bash
git clone https://github.com/Case211/remna-ad.git
cd remna-ad
pip install -r requirements.txt
cp .env.example .env
nano .env
python main.py
```

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `API_BASE_URL` — base Remnawave API URL (e.g. `https://panel.example.com/api`)
- `REMNAWAVE_API_TOKEN` — API token (when using token-based auth)
- `OPERATOR_USER_IDS` — list of operator IDs with read access (e.g. `789012345`)
- `ADMIN_USER_IDS` — comma-separated admin IDs (e.g. `123,456`)

Performance / UI tuning:
- `DASHBOARD_SHOW_SYSTEM_STATS` (true/false)
- `DASHBOARD_SHOW_SERVER_INFO` (true/false)
- `DASHBOARD_SHOW_USERS_COUNT` (true/false)
- `DASHBOARD_SHOW_NODES_COUNT` (true/false)
- `DASHBOARD_SHOW_TRAFFIC_STATS` (true/false)
- `DASHBOARD_SHOW_UPTIME` (true/false)
- `ENABLE_PARTIAL_SEARCH` (true/false)
- `SEARCH_MIN_LENGTH` (integer)

## Usage
- Start the bot and send `/start`.
- Navigate with inline buttons. Lists are paginated; quick actions are available from each card.
- Search across multiple fields for convenient detail viewing and management.

## Compatibility Notes
- Verified against Remnawave API v2.1.13.

## License
MIT — see [LICENSE](LICENSE).

Last updated: 29 September 2025
