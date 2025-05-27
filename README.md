# pyStratus

**pyStratus** is a Python-based GUI application for managing data from the GTP Stratus API. It provides a user-friendly interface to interact with projects, packages, assemblies, attachments, activity logs, users, containers, tracking statuses, and API health data. Built with `ttkbootstrap` for a modern UI, it supports features like filtering, downloading/uploading attachments, and updating package properties.

## Features
- **Project Management**: View and filter projects from the GTP Stratus API.
- **Package and Assembly Management**: Browse, filter, and manage packages and their assemblies.
- **Attachment Handling**: Download and upload attachments for packages and assemblies.
- **Package Properties**: View and edit package properties with real-time change detection.
- **Activity Logs**: Display recent activity logs with detailed information.
- **Users and Containers**: View user and container details.
- **Tracking Statuses**: Display tracking status information, including name, description, and sequence.
- **API Health Monitoring**: Check the health status of the GTP Stratus API.
- **Error Handling**: Robust handling of API errors, including rate limits and connection issues.
- **Responsive UI**: Modern, dark-themed interface with filtering and tabbed navigation.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Dependencies**:
  - `ttkbootstrap`: For the GUI framework.
  - `requests`: For making API calls.
  - `Pillow` (PIL): For handling the application logo.
- **GTP Stratus API Key**: Required to authenticate API requests.
- **Logo File** (optional): Place an `app.png` file in the same directory as the script for the application logo.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/pyStratus.git
   cd pyStratus
