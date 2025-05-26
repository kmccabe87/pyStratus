pyStratus README
Overview
pyStratus is a Python-based GUI application built with ttkbootstrap that interfaces with the GTP Stratus API to manage projects, packages, assemblies, attachments, and related data. It provides a user-friendly interface for browsing, filtering, downloading, and uploading files, as well as viewing and editing package properties, activity logs, users, containers, and API health data.
Features
* Project and Package Management:
* Browse and filter projects, packages, and assemblies with real-time search.
* View detailed package properties and assembly counts.
* Attachment Handling:
* Download selected or all attachments for packages and assemblies.
* Upload new attachments with a simple file picker.
* Package Property Editing:
* Modify package details (e.g., name, description, dates, status) with input validation.
* Track unsaved changes with visual alerts.
* Tabbed Interface:
* Access Attachments, Package Properties, Activity Logs, Users, Containers, and API Health tabs.
* Lazy loading of data to optimize performance.
* Robust Error Handling:
* Handles API rate limits (429), transient errors (500, 503), and connection issues.
* User-friendly error messages for invalid inputs or API failures.
* Customizable UI:
* Modern darkly theme via ttkbootstrap.
* Optional custom logo support (app.png).
* Data Filtering:
* Filter projects, packages, and assemblies by name using intuitive text input.
Prerequisites
* Python 3.8+
* Required Python packages:
* requests
* ttkbootstrap
* pillow
* A valid GTP Stratus API key (stored in appkey.txt or entered via prompt).
* An internet connection to access https://api.gtpstratus.com.
* Optional: A logo image (app.png) for branding.
Installation
* Clone or download the script: Download pyStratus.py or clone the repository (if hosted).
* Install dependencies: Open a terminal in the script’s directory and run:
bash
pip install requests ttkbootstrap pillow
* Set up the API key:
* Create a file named appkey.txt in the same directory as pyStratus.py and add your GTP Stratus API key, or
* Run the script, and a dialog will prompt you to enter the API key, which will be saved to appkey.txt.
* Optional: Add a logo: Place an app.png image (recommended size: 410x150 pixels) in the script’s directory for a custom logo in the GUI.
Usage
* Launch the application:
bash
python pyStratus.py
* Key Actions:
* Select a Project: Use the dropdown to choose a project and filter using the "Filter Projects" field.
* Manage Packages/Assemblies: View, filter, and select packages or assemblies to see attachments or properties.
* Handle Attachments: Download or upload files for packages/assemblies using the respective buttons.
* Edit Properties: Modify package details in the "Package Properties" tab and apply changes.
* Explore Tabs: Switch between tabs to view activity logs, users, containers, or API health.
* Refresh Data: Click the "Refresh" button to reload all data while preserving filters and selections.
* Exit: Click the "Close" button to quit.
* Example Workflow:
* Select a project to list its packages.
* Choose a package to view its attachments and assemblies.
* Upload a new attachment or edit package properties (e.g., change status to "Archived").
* Check the "API Health" tab to ensure the API is operational.
Screenshots
Below are example screenshots of the pyStratus interface:
* Main Interface (Attachments Tab):
* Displays project selection, package/assembly tables, and attachment management.
* (Placeholder: Imagine a dark-themed UI with a project dropdown, package table, and attachment upload/download buttons.)
* Package Properties Tab:
* Shows editable fields for package details with an "Apply Changes" button.
* (Placeholder: Visualize a form with fields like Name, Description, Status, and a red "Changes need to be applied" alert.)
* API Health Tab:
* Lists key-value pairs or tabular data from the /health endpoint.
* (Placeholder: Picture a table with columns like "Key" and "Value" showing API status metrics.)
Note: Actual screenshots are not included here. To generate screenshots, run the application and capture the GUI using a tool like Snipping Tool or a screenshot utility.
Documentation
* API Reference:
* The application interacts with the GTP Stratus API at https://api.gtpstratus.com.
* Key endpoints include:
* /v2/project: List projects.
* /v1/package: List packages for a project.
* /v1/package/{id}/attachments: Manage package attachments.
* /v2/package/{id}/assemblies: List assemblies.
* /v1/assembly/{id}/attachments: Manage assembly attachments.
* /v1/activity: Retrieve activity logs.
* /v2/user: List users.
* /v1/container: List containers.
* /health: Check API health.
* Refer to the official GTP Stratus API documentation (if available) for detailed endpoint specifications.
* Code Structure:
* API Key Management: get_api_key() handles API key retrieval and storage.
* Error Handling: handle_request_error() and make_api_request() manage API errors with retries.
* GUI Class (StratusGUI): Organizes the UI with methods for fetching data, updating tables, and handling user actions.
* Key Methods:
* fetch_projects(): Retrieves project list.
* fetch_packages_by_id(): Loads packages for a project.
* fetch_package_attachments(): Fetches package attachments.
* apply_property_changes(): Updates package properties.
* download_attachment(): Downloads files.
* upload_package_attachment(): Uploads files.
* Local Documentation:
* Inline comments in pyStratus.py explain key functions and logic.
* For detailed code exploration, open pyStratus.py in an IDE with Python support (e.g., VS Code, PyCharm).
Contributing
Contributions are welcome to enhance pyStratus. To contribute:
* Fork the Repository (if hosted on GitHub or similar): Create a fork of the project.
* Clone Locally:
bash
git clone https://github.com/your-username/pyStratus.git
cd pyStratus
* Create a Branch:
bash
git checkout -b feature/your-feature-name
* Make Changes:
* Add features (e.g., new tabs, enhanced filtering).
* Fix bugs (e.g., edge cases in API responses).
* Improve documentation or UI.
* Test Changes:
* Ensure the application runs without errors.
* Test with a valid GTP Stratus API key.
* Verify new features work as expected.
* Commit and Push:
bash
git commit -m "Add your descriptive commit message"
git push origin feature/your-feature-name
* Submit a Pull Request:
* Open a PR with a clear description of changes and their purpose.
* Reference any related issues.
* Code Guidelines:
* Follow PEP 8 for Python code style.
* Add comments for complex logic.
* Ensure backward compatibility with existing features.
* Issues:
* Check for open issues or create new ones for bugs or feature requests.
* Provide detailed reproduction steps for bug reports.
Support
For assistance with pyStratus:
* GitHub Issues (if hosted):
* Open an issue on the project’s GitHub repository for bugs or questions.
* Email:
* Contact the developer at [your-email@example.com (mailto:your-email@example.com)] (replace with actual contact if available).
* Community:
* Check for community discussions on platforms like Stack Overflow or relevant forums (tag with pyStratus or GTP Stratus).
* API Support:
* For API-related issues, contact the GTP Stratus API support team or refer to their official documentation.
If you encounter errors, include:
* The error message.
* Steps to reproduce the issue.
* Your Python version and OS.
* A sample of appkey.txt (redact sensitive parts).
License
This project is licensed under the MIT License (or specify another license if applicable). You are free to use, modify, and distribute pyStratus in accordance with the license terms, provided you comply with the GTP Stratus API terms of service.
Note: The API key stored in appkey.txt is sensitive. Secure it appropriately and avoid sharing it publicly.
Troubleshooting
* API Connection Failed:
* Verify internet connectivity.
* Confirm the API key in appkey.txt is valid.
* Ensure https://api.gtpstratus.com is accessible.
* No Data in Tables:
* Check if projects exist in the API.
* Wait if rate-limited (see error messages).
* Logo Not Displaying:
* Verify app.png exists and is a valid image.
* Upload/Download Failures:
* Confirm file paths and permissions.
* Ensure sufficient disk space.
Notes
* The UI uses ttkbootstrap’s darkly theme for a sleek, modern look.
* The window is fixed at 1980x1000 pixels, centered on the screen.
* Data fetching is optimized with lazy loading for non-critical tabs.
* Secure appkey.txt or consider environment variables for production use.

