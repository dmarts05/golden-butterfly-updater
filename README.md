# Golden Butterfly Updater

**Golden Butterfly Updater** is a robust automation utility designed to streamline portfolio tracking. It autonomously scrapes account balances from supported financial institutions and synchronizes the consolidated data into a _Golden Butterfly_ portfolio model on Google Sheets.

Designed with modularity in mind, it supports headless browser execution, Docker containerization, and configuration-driven workflows.

---

## Key Features

-   **Automated Scraping:** Browser-based data extraction for supported banks and exchanges (e.g. Trade Republic, MyInvestor).
-   **Google Sheets Integration:** Seamless two-way synchronization that updates portfolio values while preserving existing formulas (such as automatic cash deductions).
-   **Secure Configuration:** Sensitive credentials and settings are managed via YAML configuration and environment isolation.
-   **Container Ready:** Fully Dockerized for scheduled execution on servers or NAS systems.
-   **Modern Tooling:** Built on Python 3.13 and managed with `uv` for fast, reproducible environments.

---

## Requirements

-   **Python:** ≥ 3.13
-   **Package Manager:** [`uv`](https://github.com/astral-sh/uv)
-   **Google Cloud:** Service Account with _Editor_ access to the target Google Sheet
-   **Docker:** Optional, for containerized execution

---

## Installation (Local)

This project uses `uv` for dependency management and environment isolation.

### 1. Install `uv`

If you don’t already have `uv` installed, follow the official installation guide:

https://docs.astral.sh/uv/getting-started/installation/

### 2. Sync Dependencies

From the project root, create and sync the virtual environment using the locked dependencies:

```bash
uv sync --frozen
```

---

## Configuration

### 1. Application Configuration

```bash
cp config.example.yml config.yml
```

Edit `config.yml` to define browser settings, Google Sheets details, and bank accounts.

---

### 2. Google Cloud Credentials

1. Create a Service Account in Google Cloud
2. Download the JSON key file (e.g. `credentials.json`)
3. Share your Google Sheet with the `client_email` from the JSON file
4. Grant **Editor** access

---

## Usage

### Local

```bash
uv run python -m golden_butterfly_updater
```

### Docker

```bash
docker compose run --rm golden-butterfly-updater
```

---

## Disclaimer

Use at your own risk. This software performs automated scraping of financial institutions. The authors accept no responsibility for account restrictions, data inaccuracies, or compliance issues.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
