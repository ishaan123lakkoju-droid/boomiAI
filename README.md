# Boomi Automation Framework

A manifest-driven Python automation framework for creating and managing Boomi integration components. This tool enables Infrastructure-as-Code (IaC) for Boomi through YAML manifests and automatically generates Boomi components via the REST API.

## Overview

The **Boomi Automation Framework** provides:

- ✅ **YAML-based manifests** for defining Boomi patterns (SFTP → Transform → MQ)
- ✅ **Automated component creation** via Boomi REST API
- ✅ **CSV component inventory** for auditing and reuse across environments
- ✅ **Live execution results** with real Boomi component IDs
- ✅ **Reusable connectors** to reduce duplicate component creation
- ✅ **Dry-run validation** before live Boomi deployments

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Boomi Credentials

Set environment variables (or update defaults in `boomi.py`):

```bash
export BOOMI_ACCOUNT_ID="your-account-id"
export BOOMI_USERNAME="your-email@domain.com"
export BOOMI_TOKEN="your-boomi-token"
```

### 3. Run Automation (Dry-run)

```bash
python boomi.py "boomi manifest file.txt" --csv boomi_component_ids.csv --dry-run
```

### 4. Run Live Component Creation

```bash
python boomi.py "boomi manifest file.txt" --csv boomi_component_ids.csv
```

### 5. Reuse Components in Next Deployment

```bash
python boomi.py "boomi manifest file.txt" --csv boomi_component_ids_v2.csv --load-ids boomi_component_ids.csv
```

## Project Structure

```
boomiAI/
├── boomi.py                                 # Main automation script (REST API client)
├── boomi manifest file.txt                  # Sample YAML manifest
├── boomi_component_ids.csv                  # Live component inventory
├── BOOMI_AUTOMATION_DETAILED_GUIDE.md       # Complete documentation (16+ sections)
├── BOOMI_AUTOMATION_DOCUMENTATION.md        # Architecture and API reference
├── AUTOMATION_RESULTS.md                    # Live execution results & IDs
├── GITHUB_SETUP.md                          # GitHub commit instructions
├── README.md                                # This file
├── requirements.txt                         # Python dependencies
├── .env                                     # Environment configuration (DO NOT COMMIT)
├── .gitignore                               # Git ignore rules
└── mq connector .xml                        # Example MQ connector XML
```

## Key Features

### 1. Manifest-Driven Design

Define all Boomi components in a single YAML file:

```yaml
pattern:
  name: "SFTPTRANSJMS"
  description: "SFTP{Get}- Transformation - MQ{Send}"

sftp:
  connector_name: "AxwaySFTP"
  host: "172.16.16.12demo"
  port: 8022
  # ... more config

source_profile:
  name: "[sftp]CUSTOMERMASTER DB"
  sql: "SELECT * FROM win_gcif_all_info_table"

# ... more sections
```

### 2. Component Reuse

First run creates components:
```bash
python boomi.py manifest.yaml --csv inventory.csv
```

Subsequent runs reuse existing components:
```bash
python boomi.py manifest_v2.yaml --csv inventory_v2.csv --load-ids inventory.csv
```

### 3. Live Execution Tracking

Successfully created **9 Boomi components** including:
- Process properties (`PP_CustomerMaster`)
- Data profiles (source DB, target XML)
- Connectors (SFTP, MQ)
- Transformation maps
- Operations and functions

See [AUTOMATION_RESULTS.md](AUTOMATION_RESULTS.md) for full details and IDs.

## CLI Usage

```bash
python boomi.py <manifest_file> --csv <output_csv> [--load-ids <existing_csv>] [--dry-run]
```

### Options

| Option | Required | Description |
|---|---|---|
| `manifest_file` | Yes | Path to YAML manifest |
| `--csv output_csv` | Yes | Output CSV file |
| `--load-ids existing_csv` | No | Load existing component IDs for reuse |
| `--dry-run` | No | Validate without creating |

## Documentation

- **[BOOMI_AUTOMATION_DETAILED_GUIDE.md](BOOMI_AUTOMATION_DETAILED_GUIDE.md)** — Complete guide with architecture, manifest structure, API methods, workflows, and troubleshooting
- **[BOOMI_AUTOMATION_DOCUMENTATION.md](BOOMI_AUTOMATION_DOCUMENTATION.md)** — Technical reference and component builders
- **[AUTOMATION_RESULTS.md](AUTOMATION_RESULTS.md)** — Live execution results with real component IDs
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** — How to commit this project to GitHub

## Live Execution Results

Last automation run (`2026-06-11`):

✅ **9 components created successfully:**
- `PP_CustomerMaster` (processproperty) — `778d3bce-e5a5-4ada-8991-1cf1a66ce757`
- `CurDate_to_YYYYMMDD` (transform.function) — `618d7fb7-79a1-4c62-b9b9-ecd80f6873a6`
- `[CGI] CustomerMaster XML` (profile.xml) — `3d5dbd78-8ccd-4dc4-ac1a-e548276e132f`
- `[sftp]CUSTOMERMASTER DB` (profile.db) — `8239d473-bd5d-4a2d-ab81-8b090ced72e7`
- `Map_Template` (transform.map) — `c1b26b1d-0608-44f2-826c-d32f3d45b1f1`
- `CON_HUB_INT-test` (connector-settings) — `4a47c382-bb87-43f0-a688-005d2de179b8`
- `OP_CGI_CUSTOMER_SEND` (connector-action) — `05b6cc4c-f20d-48a7-bd2a-f1be75d91229`
- `AxwaySFTP` (connector-settings) — `13c9c9fc-4d48-416c-b908-9d40cfcb92cd`
- `sftp read operation` (connector-action) — `2df9436d-f544-4bc1-9653-ff420b5c872e`

❌ **3 components failed** due to subprocess XML validation (HTTP 400)

## Requirements

- Python 3.7+
- PyYAML for manifest parsing
- urllib3 (built-in) for REST API calls

## Installation

```bash
pip install -r requirements.txt
```

## Environment Setup

Create `.env` file (template provided):

```
BOOMI_ACCOUNT_ID=techmahindranfrmaster-4WVRJM
BOOMI_USERNAME=BOOMI_TOKEN.UK00887178@techmahindra.com
BOOMI_TOKEN=your-token-here
BOOMI_BASE_URL=https://api.boomi.com/api/rest/v1/...
```

## Common Use Cases

### Create new integration pattern

```bash
python boomi.py new_pattern.yaml --csv new_pattern_ids.csv --dry-run
python boomi.py new_pattern.yaml --csv new_pattern_ids.csv
```

### Redeploy with component reuse

```bash
python boomi.py same_pattern_v2.yaml --csv v2_ids.csv --load-ids v1_ids.csv
```

### Audit component inventory

```
cat boomi_component_ids.csv | column -t -s,
```

## GitHub Setup

To commit this project to GitHub, see [GITHUB_SETUP.md](GITHUB_SETUP.md) for step-by-step instructions.

## Troubleshooting

| Issue | Solution |
|---|---|
| PyYAML not found | `pip install pyyaml` |
| Boomi API 400 error | Check XML structure and manifest values |
| CSV not created | Verify output path permissions |
| Reuse not working | Confirm component names match exactly |
| Authentication failed | Check BOOMI credentials in `.env` |

## Contributing

1. Test changes with `--dry-run` first
2. Update manifest examples if adding features
3. Run full automation before committing
4. Document changes in relevant guide files

## License

Proprietary - Boomi Integration Automation Framework

## Support

For issues or questions:
- See [BOOMI_AUTOMATION_DETAILED_GUIDE.md](BOOMI_AUTOMATION_DETAILED_GUIDE.md) troubleshooting section
- Check live execution results in [AUTOMATION_RESULTS.md](AUTOMATION_RESULTS.md)
- Review manifest structure examples
