# pyStratus

A Python GUI application for managing data from the **GTP Stratus API**. It provides a user-friendly interface to work with projects, packages, assemblies, attachments, activity logs, users, containers, tracking statuses, and API health data.

Built with [`ttkbootstrap`](https://pypi.org/project/ttkbootstrap/) for a modern, dark-themed UI, it supports filtering, downloading/uploading attachments, and updating package properties.

## Features

- **Project Management** — view and filter projects from the GTP Stratus API.
- **Package & Assembly Management** — browse, filter, and manage packages and their assemblies.
- **Attachment Handling** — download and upload attachments for packages and assemblies.
- **Package Properties** — view and edit package properties with real-time change detection.
- **Activity Logs** — display recent activity logs with detailed information.
- **Users & Containers** — view user and container details.
- **Tracking Statuses** — display tracking status info (name, description, sequence).
- **API Health Monitoring** — check the health status of the GTP Stratus API.
- **Error Handling** — robust handling of API errors, including rate limits and connection issues.
- **Responsive UI** — modern, dark-themed interface with filtering and tabbed navigation.

## Project layout

| Path | Description |
| --- | --- |
| `pyStratus/pyStratus.py` | Application entry point |
| `pyStratus/app.PNG` | Screenshot of the running app |

![Screenshot](pyStratus/app.PNG)

## Prerequisites

- **Python 3.8+**
- **Dependencies**:
  - `ttkbootstrap` — GUI framework
  - `requests` — API calls
  - `Pillow` — logo handling
- **GTP Stratus API key** — required to authenticate API requests.

## Installation

```bash
# Clone
git clone https://github.com/kmccabe87/pyStratus.git
cd pyStratus

# Install dependencies
pip install ttkbootstrap requests pillow
```

## Usage

```bash
python pyStratus/pyStratus.py
```

Provide your GTP Stratus API key when the app asks for it, then use the tabs to browse and manage your data.

## License

GPL-3.0 — see [LICENSE](LICENSE).
