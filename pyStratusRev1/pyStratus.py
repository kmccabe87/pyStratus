# pyStratus - A GUI application for managing GTP Stratus API data
# Copyright (C) 2025 Your Name
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import requests
import ttkbootstrap as tb
from datetime import datetime
from PIL import Image, ImageTk
from requests.exceptions import RequestException, HTTPError
from tkinter import Toplevel, messagebox, filedialog, StringVar
import time
import random

# API configuration
BASE_URL = "https://api.gtpstratus.com"
APPKEY_FILE = "appkey.txt"
PROJECT_ENDPOINT = "/v2/project"
PACKAGE_ENDPOINT = "/v1/package"

def get_api_key(root):
    """Retrieve or prompt for API key and save it to appkey.txt."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    appkey_path = os.path.join(root_dir, APPKEY_FILE)
    if os.path.exists(appkey_path):
        try:
            with open(appkey_path, "r") as f:
                api_key = f.read().strip()
                if api_key:
                    return api_key
        except OSError as e:
            messagebox.showerror("Error", f"Failed to read appkey.txt: {e}")
    dialog = Toplevel(root)
    dialog.title("Enter App Key")
    dialog_width = 400
    dialog_height = 200
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - dialog_width) // 2
    y = (screen_height - dialog_height) // 2
    dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    dialog.resizable(False, False)
    tb.Label(dialog, text="Please enter app key:").pack(pady=10)
    api_key_var = StringVar()
    entry = tb.Entry(dialog, textvariable=api_key_var, width=40, show="*")
    entry.pack(pady=5)
    entry.focus_set()
    def save_key():
        key = api_key_var.get().strip()
        if not key:
            messagebox.showerror("Error", "App key cannot be empty.")
            return
        try:
            with open(appkey_path, "w") as f:
                f.write(key)
            dialog.destroy()
        except OSError as e:
            messagebox.showerror("Error", f"Failed to save appkey.txt: {e}")
            dialog.destroy()
    tb.Button(dialog, text="Save", command=save_key, bootstyle="primary").pack(pady=10)
    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)
    if os.path.exists(appkey_path):
        try:
            with open(appkey_path, "r") as f:
                api_key = f.read().strip()
                if api_key:
                    return api_key
        except OSError as e:
            messagebox.showerror("Error", f"Failed to read appkey.txt: {e}")
    messagebox.showerror("Error", "No app key provided. Exiting.")
    exit(1)

def handle_request_error(e, action):
    """Centralized error handling for HTTP requests."""
    if isinstance(e, HTTPError) and e.response.status_code == 429:
        retry_after = int(e.response.headers.get("Retry-After", 60))
        messagebox.showwarning("Rate Limit", f"Rate limit exceeded for {action}. Retry after {retry_after} seconds.")
        return retry_after
    elif isinstance(e, HTTPError):
        messagebox.showerror("Error", f"{action}: {e}\nResponse: {e.response.text}")
    elif isinstance(e, requests.exceptions.ConnectionError):
        messagebox.showerror("Error", "Connection failed. Check internet, VPN, or proxy settings.")
    else:
        messagebox.showerror("Error", f"{action}: {e}")
    return None

def make_api_request(url, headers, params, action, retries=3, backoff_factor=1):
    """Make an API request with retry logic for transient errors."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response
        except RequestException as e:
            retry_after = handle_request_error(e, action)
            if retry_after is not None:  # 429 Rate Limit
                time.sleep(retry_after + random.uniform(0, 0.1))  # Jitter
                continue
            elif isinstance(e, HTTPError) and e.response.status_code in (500, 503):  # Transient errors
                if attempt < retries - 1:
                    delay = backoff_factor * (2 ** attempt) + random.uniform(0, 0.1)
                    time.sleep(delay)
                    continue
            raise e
    raise RequestException(f"Failed to complete {action} after {retries} attempts")

class StratusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("pyStratus")
        self.projects = []
        self.all_projects = []
        self.packages = []
        self.all_packages = []
        self.package_attachments = []
        self.assemblies = []
        self.all_assemblies = []
        self.assembly_attachments = []
        self.activity_logs = []
        self.users = []
        self.containers = []
        self.health_data = []
        self.selected_package_id = None
        self.selected_assembly_id = None
        self.package_data = {}
        self.property_fields = {}
        self.initial_field_values = {}

        # Main frame
        self.main_frame = tb.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left frame for project selection
        self.left_frame = tb.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky="ns", padx=5)

        # Project dropdown and filter
        self.project_label = tb.Label(self.left_frame, text="Select Project:")
        self.project_label.grid(row=0, column=0, pady=5, sticky="w")
        self.project_var = StringVar()
        self.project_dropdown = tb.Combobox(self.left_frame, textvariable=self.project_var,
                                           state="readonly", width=30)
        self.project_dropdown.grid(row=1, column=0, pady=5, sticky="w")
        self.project_dropdown.bind("<<ComboboxSelected>>", self.fetch_packages)

        # Project filter
        self.project_filter = tb.Entry(self.left_frame, width=30, justify="center",
                                      foreground="gray", font=("Arial", 10, ""))
        self.project_filter.grid(row=3, column=0, pady=5, sticky="w")
        self.project_filter.insert(0, "Filter Projects")
        self.project_filter.bind("<FocusIn>", lambda e: self._clear_placeholder(e, "Filter Projects"))
        self.project_filter.bind("<FocusOut>", lambda e: self._restore_placeholder(e, "Filter Projects"))
        self.project_filter.bind("<KeyRelease>", lambda e: self._on_filter_keyrelease(e, "projects"))
        self.project_filter.bind("<Button-1>", lambda e: self.project_filter.focus_set())

        # Package filter
        self.package_filter = tb.Entry(self.left_frame, width=30, justify="center",
                                      foreground="gray", font=("Arial", 10, ""))
        self.package_filter.grid(row=5, column=0, pady=5, sticky="w")
        self.package_filter.insert(0, "Filter Packages")
        self.package_filter.bind("<FocusIn>", lambda e: self._clear_placeholder(e, "Filter Packages"))
        self.project_filter.bind("<FocusOut>", lambda e: self._restore_placeholder(e, "Filter Packages"))
        self.package_filter.bind("<KeyRelease>", lambda e: self._on_filter_keyrelease(e, "packages"))
        self.package_filter.bind("<Button-1>", lambda e: self.package_filter.focus_set())

        # Assembly filter
        self.assembly_filter = tb.Entry(self.left_frame, width=30, justify="center",
                                       foreground="gray", font=("Arial", 10, ""))
        self.assembly_filter.grid(row=7, column=0, pady=5, sticky="w")
        self.assembly_filter.insert(0, "Filter Assemblies")
        self.assembly_filter.bind("<FocusIn>", lambda e: self._clear_placeholder(e, "Filter Assemblies"))
        self.assembly_filter.bind("<FocusOut>", lambda e: self._restore_placeholder(e, "Filter Assemblies"))
        self.assembly_filter.bind("<KeyRelease>", lambda e: self._on_filter_keyrelease(e, "assemblies"))
        self.assembly_filter.bind("<Button-1>", lambda e: self.assembly_filter.focus_set())

        # Refresh and Close buttons
        self.refresh_button = tb.Button(self.left_frame, text="Refresh", command=self.refresh_tables,
                                       width=10, bootstyle="primary")
        self.refresh_button.grid(row=8, column=0, padx=5, pady=5, sticky="w")
        self.close_button = tb.Button(self.left_frame, text="Close", command=self.root.quit,
                                      width=10, bootstyle="primary")
        self.close_button.grid(row=9, column=0, padx=5, pady=5, sticky="w")

        # Load app logo
        self.app_photo = None
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.png")
            if os.path.exists(logo_path):
                app_image = Image.open(logo_path).resize((410, 150), Image.LANCZOS)
                self.app_photo = ImageTk.PhotoImage(app_image)
                self.app_image_ref = app_image
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load logo: {e}")
        self.app_logo = tb.Label(self.left_frame, image=self.app_photo or "Logo Unavailable")
        self.app_logo.grid(row=14, column=0, columnspan=2, padx=10, pady=10, sticky="sw")
        self.left_frame.rowconfigure(14, weight=1)

        # Notebook for tabs
        self.notebook = tb.Notebook(self.main_frame, bootstyle="dark")
        self.notebook.grid(row=0, column=1, sticky="nsew")
        self.main_frame.columnconfigure(1, weight=1)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # Attachments tab
        self.attachments_frame = tb.Frame(self.notebook)
        self.notebook.add(self.attachments_frame, text="Attachments")
        self.package_frame = tb.Frame(self.attachments_frame)
        self.package_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.package_table = tb.Treeview(self.package_frame, columns=("name", "description", "assembly_count"),
                                         show="headings", selectmode="extended", bootstyle="dark")
        self.package_table.heading("name", text="Name")
        self.package_table.heading("description", text="Description")
        self.package_table.heading("assembly_count", text="Assembly Count")
        self.package_table.column("name", width=150)
        self.package_table.column("description", width=200)
        self.package_table.column("assembly_count", width=100)
        self.package_table.grid(row=0, column=0, sticky="nsew")
        self.package_table.bind("<<TreeviewSelect>>", self.on_package_select)
        package_scrollbar = tb.Scrollbar(self.package_frame, orient="vertical",
                                         command=self.package_table.yview, bootstyle="dark")
        package_scrollbar.grid(row=0, column=1, sticky="ns")
        self.package_table.configure(yscrollcommand=package_scrollbar.set)
        self.package_frame.columnconfigure(0, weight=1)
        self.package_frame.rowconfigure(0, weight=1)
        self.package_attachment_frame = tb.Frame(self.attachments_frame)
        self.package_attachment_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.package_attachment_table = tb.Treeview(self.package_attachment_frame,
                                                   columns=("fileName", "createdDT"), show="headings",
                                                   selectmode="extended", bootstyle="dark")
        self.package_attachment_table.heading("fileName", text="File Name")
        self.package_attachment_table.heading("createdDT", text="Created Date")
        self.package_attachment_table.column("fileName", width=400)
        self.package_attachment_table.column("createdDT", width=150)
        self.package_attachment_table.grid(row=0, column=0, sticky="nsew")
        self.package_no_attachments_label = tb.Label(self.package_attachment_frame,
                                                    text="NO ATTACHMENTS", font=("Arial", 14, "bold"),
                                                    foreground="red", background="#2f2f2f")
        self.package_no_attachments_label.place(relx=0.5, rely=0.5, anchor="center")
        self.package_no_attachments_label.place_forget()
        package_attachment_scrollbar = tb.Scrollbar(self.package_attachment_frame, orient="vertical",
                                                   command=self.package_attachment_table.yview, bootstyle="dark")
        package_attachment_scrollbar.grid(row=0, column=1, sticky="ns")
        self.package_attachment_table.configure(yscrollcommand=package_attachment_scrollbar.set)
        self.package_attachment_frame.columnconfigure(0, weight=1)
        self.package_attachment_frame.rowconfigure(0, weight=1)
        self.package_button_frame = tb.Frame(self.package_attachment_frame)
        self.package_button_frame.grid(row=1, column=0, sticky="e", pady=5)
        self.package_download_selected_button = tb.Button(self.package_button_frame, text="Download Selected",
                                                         command=self.download_selected_package_attachments,
                                                         width=20, bootstyle="primary")
        self.package_download_selected_button.grid(row=0, column=0, padx=5, pady=5)
        self.package_download_all_button = tb.Button(self.package_button_frame, text="Download All",
                                                    command=self.download_all_package_attachments,
                                                    width=20, bootstyle="primary")
        self.package_download_all_button.grid(row=1, column=0, padx=5, pady=5)
        self.package_upload_frame = tb.Frame(self.package_attachment_frame)
        self.package_upload_frame.grid(row=2, column=0, sticky="e", pady=5)
        self.package_upload_var = StringVar()
        self.package_upload_entry = tb.Entry(self.package_upload_frame, textvariable=self.package_upload_var,
                                             width=30, state="readonly")
        self.package_upload_entry.grid(row=0, column=0, padx=5)
        self.package_browse_button = tb.Button(self.package_upload_frame, text="Browse File",
                                               command=self.browse_package_file, bootstyle="primary")
        self.package_browse_button.grid(row=0, column=1, padx=5)
        self.package_upload_button = tb.Button(self.package_upload_frame, text="Upload File",
                                               command=self.upload_package_attachment, bootstyle="primary")
        self.package_upload_button.grid(row=0, column=2, padx=5)
        self.assembly_frame = tb.Frame(self.attachments_frame)
        self.assembly_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.assembly_table = tb.Treeview(self.assembly_frame, columns=("name", "description"),
                                          show="headings", selectmode="extended", bootstyle="dark")
        self.assembly_table.heading("name", text="Name")
        self.assembly_table.heading("description", text="Description")
        self.assembly_table.column("name", width=150)
        self.assembly_table.column("description", width=200)
        self.assembly_table.grid(row=0, column=0, sticky="nsew")
        self.assembly_table.bind("<<TreeviewSelect>>", self.fetch_assembly_attachments)
        assembly_scrollbar = tb.Scrollbar(self.assembly_frame, orient="vertical",
                                          command=self.assembly_table.yview, bootstyle="dark")
        assembly_scrollbar.grid(row=0, column=1, sticky="ns")
        self.assembly_table.configure(yscrollcommand=assembly_scrollbar.set)
        self.assembly_frame.columnconfigure(0, weight=1)
        self.assembly_frame.rowconfigure(0, weight=1)
        self.assembly_attachment_frame = tb.Frame(self.attachments_frame)
        self.assembly_attachment_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.assembly_attachment_table = tb.Treeview(self.assembly_attachment_frame,
                                                    columns=("fileName", "createdDT"), show="headings",
                                                    selectmode="extended", bootstyle="dark")
        self.assembly_attachment_table.heading("fileName", text="File Name")
        self.assembly_attachment_table.heading("createdDT", text="Created Date")
        self.assembly_attachment_table.column("fileName", width=400)
        self.assembly_attachment_table.column("createdDT", width=150)
        self.assembly_attachment_table.grid(row=0, column=0, sticky="nsew")
        self.assembly_no_attachments_label = tb.Label(self.assembly_attachment_frame,
                                                     text="NO ATTACHMENTS", font=("Arial", 14, "bold"),
                                                     foreground="red", background="#2f2f2f")
        self.assembly_no_attachments_label.place(relx=0.5, rely=0.5, anchor="center")
        self.assembly_no_attachments_label.place_forget()
        assembly_attachment_scrollbar = tb.Scrollbar(self.assembly_attachment_frame, orient="vertical",
                                                    command=self.assembly_attachment_table.yview, bootstyle="dark")
        assembly_attachment_scrollbar.grid(row=0, column=1, sticky="ns")
        self.assembly_attachment_table.configure(yscrollcommand=assembly_attachment_scrollbar.set)
        self.assembly_attachment_frame.columnconfigure(0, weight=1)
        self.assembly_attachment_frame.rowconfigure(0, weight=1)
        self.assembly_button_frame = tb.Frame(self.assembly_attachment_frame)
        self.assembly_button_frame.grid(row=1, column=0, sticky="e", pady=5)
        self.assembly_download_selected_button = tb.Button(self.assembly_button_frame, text="Download Selected",
                                                          command=self.download_selected_assembly_attachments,
                                                          width=20, bootstyle="primary")
        self.assembly_download_selected_button.grid(row=0, column=0, padx=5, pady=5)
        self.assembly_download_all_button = tb.Button(self.assembly_button_frame, text="Download All",
                                                     command=self.download_all_assembly_attachments,
                                                     width=20, bootstyle="primary")
        self.assembly_download_all_button.grid(row=1, column=0, padx=5, pady=5)
        self.assembly_upload_frame = tb.Frame(self.assembly_attachment_frame)
        self.assembly_upload_frame.grid(row=2, column=0, sticky="e", pady=5)
        self.assembly_upload_var = StringVar()
        self.assembly_upload_entry = tb.Entry(self.assembly_upload_frame, textvariable=self.assembly_upload_var,
                                              width=30, state="readonly")
        self.assembly_upload_entry.grid(row=0, column=0, padx=5)
        self.assembly_browse_button = tb.Button(self.assembly_upload_frame, text="Browse File",
                                                command=self.browse_assembly_file, bootstyle="primary")
        self.assembly_browse_button.grid(row=0, column=1, padx=5)
        self.assembly_upload_button = tb.Button(self.assembly_upload_frame, text="Upload File",
                                                command=self.upload_assembly_attachment, bootstyle="primary")
        self.assembly_upload_button.grid(row=0, column=2, padx=5)

        # Package Properties tab
        self.properties_frame = tb.Frame(self.notebook)
        self.notebook.add(self.properties_frame, text="Package Properties")
        self.properties_fields_frame = tb.Frame(self.properties_frame)
        self.properties_fields_frame.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        package_fields = [
            ("Name", "name"), ("Description", "description"), ("Number", "number"),
            ("Category ID", "categoryId"), ("Hours Estimated Field", "hoursEstimatedField"),
            ("Hours Estimated Office", "hoursEstimatedOffice"),
            ("Hours Estimated Purchasing", "hoursEstimatedPurchasing"),
            ("Hours Estimated Shop", "hoursEstimatedShop"),
            ("Office Duration", "officeDuration"), ("Purchasing Duration", "purchasingDuration"),
            ("Shop Duration", "shopDuration"), ("Installed Date", "installedDT"),
            ("Office Start Date", "officeStartDT"), ("Purchasing Start Date", "purchasingStartDT"),
            ("Required Date", "requiredDT"), ("Start Date", "startDT")
        ]
        for i, (label, key) in enumerate(package_fields):
            tb.Label(self.properties_fields_frame, text=f"{label}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            var = StringVar()
            entry = tb.Entry(self.properties_fields_frame, textvariable=var, width=50)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            entry.bind("<KeyRelease>", self.check_property_changes)
            entry.bind("<Button-1>", lambda e: entry.focus_set())
            self.property_fields[key] = var
        self.status_var = StringVar()
        tb.Label(self.properties_fields_frame, text="Status:").grid(row=len(package_fields), column=0, sticky="w", padx=5, pady=2)
        self.status_dropdown = tb.Combobox(self.properties_fields_frame, textvariable=self.status_var,
                                           values=["Active (0)", "Archived (1)"], state="readonly", width=20)
        self.status_dropdown.grid(row=len(package_fields), column=1, sticky="w", padx=5, pady=2)
        self.status_dropdown.bind("<<ComboboxSelected>>", self.check_property_changes)
        self.property_fields["status"] = self.status_var
        self.properties_button_frame = tb.Frame(self.properties_frame)
        self.properties_button_frame.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.apply_button = tb.Button(self.properties_button_frame, text="Apply Changes",
                                      command=self.apply_property_changes, width=20, bootstyle="primary")
        self.apply_button.grid(row=0, column=0, pady=10)
        self.unsaved_alert = tb.Label(self.properties_button_frame, text="Changes need to be applied",
                                      foreground="red")
        self.unsaved_alert.grid(row=1, column=0, pady=5)
        self.unsaved_alert.grid_remove()

        # Activity Logs tab
        self.activity_frame = tb.Frame(self.notebook)
        self.notebook.add(self.activity_frame, text="Activity Logs")
        self.activity_table = tb.Treeview(self.activity_frame,
                                         columns=("createdDT", "referenceName"),
                                         show="headings", bootstyle="dark")
        self.activity_table.heading("createdDT", text="Created Date")
        self.activity_table.heading("referenceName", text="Reference Name")
        self.activity_table.column("createdDT", width=150)
        self.activity_table.column("referenceName", width=150)
        self.activity_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = tb.Scrollbar(self.activity_frame, orient="vertical",
                                 command=self.activity_table.yview, bootstyle="dark")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.activity_table.configure(yscrollcommand=scrollbar.set)
        self.activity_frame.columnconfigure(0, weight=1)
        self.activity_frame.rowconfigure(0, weight=1)

        # Users tab
        self.users_frame = tb.Frame(self.notebook)
        self.notebook.add(self.users_frame, text="Users")
        self.users_table = tb.Treeview(self.users_frame,
                                       columns=("firstName", "lastName", "email", "status"),
                                       show="headings", bootstyle="dark")
        self.users_table.heading("firstName", text="First Name")
        self.users_table.heading("lastName", text="Last Name")
        self.users_table.heading("email", text="Email")
        self.users_table.heading("status", text="Status")
        self.users_table.column("firstName", width=150)
        self.users_table.column("lastName", width=150)
        self.users_table.column("email", width=200)
        self.users_table.column("status", width=100)
        self.users_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = tb.Scrollbar(self.users_frame, orient="vertical",
                                 command=self.users_table.yview, bootstyle="dark")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.users_table.configure(yscrollcommand=scrollbar.set)
        self.users_frame.columnconfigure(0, weight=1)
        self.users_frame.rowconfigure(0, weight=1)

        # Containers tab
        self.containers_frame = tb.Frame(self.notebook)
        self.notebook.add(self.containers_frame, text="Containers")
        self.containers_table = tb.Treeview(self.containers_frame,
                                           columns=("name", "description"),
                                           show="headings", bootstyle="dark")
        self.containers_table.heading("name", text="Name")
        self.containers_table.heading("description", text="Description")
        self.containers_table.column("name", width=150)
        self.containers_table.column("description", width=300)
        self.containers_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = tb.Scrollbar(self.containers_frame, orient="vertical",
                                 command=self.containers_table.yview, bootstyle="dark")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.containers_table.configure(yscrollcommand=scrollbar.set)
        self.containers_frame.columnconfigure(0, weight=1)
        self.containers_frame.rowconfigure(0, weight=1)

        # API Health tab
        self.health_frame = tb.Frame(self.notebook)
        self.notebook.add(self.health_frame, text="API Health")
        self.health_table = tb.Treeview(self.health_frame,
                                        columns=("key", "value"),
                                        show="headings", bootstyle="dark")
        self.health_table.heading("key", text="Key")
        self.health_table.heading("value", text="Value")
        self.health_table.column("key", width=200)
        self.health_table.column("value", width=300)
        self.health_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scrollbar = tb.Scrollbar(self.health_frame, orient="vertical",
                                 command=self.health_table.yview, bootstyle="dark")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.health_table.configure(yscrollcommand=scrollbar.set)
        self.health_frame.columnconfigure(0, weight=1)
        self.health_frame.rowconfigure(0, weight=1)

        # Fetch initial data
        self.fetch_projects()
        self.tab_data_fetched = {
            "activity_logs": False,
            "users": False,
            "containers": False,
            "health": False
        }

    def on_tab_changed(self, event):
        """Fetch data for new tabs when selected."""
        selected_tab = self.notebook.index(self.notebook.select())
        tab_name = self.notebook.tab(selected_tab, "text")
        if tab_name == "Activity Logs" and not self.tab_data_fetched["activity_logs"]:
            self.fetch_activity_logs()
            self.tab_data_fetched["activity_logs"] = True
        elif tab_name == "Users" and not self.tab_data_fetched["users"]:
            self.fetch_users()
            self.tab_data_fetched["users"] = True
        elif tab_name == "Containers" and not self.tab_data_fetched["containers"]:
            self.fetch_containers()
            self.tab_data_fetched["containers"] = True
        elif tab_name == "API Health" and not self.tab_data_fetched["health"]:
            self.fetch_health()
            self.tab_data_fetched["health"] = True

    def _clear_placeholder(self, event, placeholder):
        entry = event.widget
        if entry.get() == placeholder:
            entry.delete(0, tb.END)
            entry.configure(foreground="white", font=("Arial", 10, "normal"))

    def _restore_placeholder(self, event, placeholder):
        entry = event.widget
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(foreground="gray", font=("Arial", 10, ""))

    def _on_filter_keyrelease(self, event, item_type):
        entry = event.widget
        filter_text = entry.get().strip().lower()
        placeholder = {"projects": "Filter Projects", "packages": "Filter Packages",
                       "assemblies": "Filter Assemblies"}[item_type]
        if filter_text == placeholder.lower():
            filter_text = ""
        self.filter_items(item_type, filter_text)

    def filter_items(self, item_type, filter_text=""):
        source = (self.all_projects if item_type == "projects" else
                  self.all_packages if item_type == "packages" else self.all_assemblies)
        filtered = source if not filter_text else [
            item for item in source if filter_text in item.get("name", "").lower()
        ]
        setattr(self, item_type, filtered)
        if item_type == "projects":
            current_selection = self.project_var.get()
            project_names = ["Choose Project"] + [p.get("name", "Unnamed") for p in self.projects]
            self.project_dropdown["values"] = project_names
            if current_selection in project_names:
                self.project_dropdown.set(current_selection)
            else:
                self.project_dropdown.current(0)
            selected_index = self.project_dropdown.current()
            if selected_index > 0 and self.projects:
                project_id = self.projects[selected_index - 1].get("id")
                self.fetch_packages_by_id(project_id)
            else:
                self.clear_tables_and_fields()
                self.selected_package_id = None
        elif item_type == "packages":
            self.update_table("packages")
            if self.selected_package_id:
                for item in self.package_table.get_children():
                    if self.package_table.item(item)["tags"][0] == self.selected_package_id:
                        self.package_table.selection_set(item)
                        self.on_package_select(None)
                        break
                else:
                    self.package_table.selection_remove(self.package_table.selection())
                    self.clear_tables_and_fields()
                    self.selected_package_id = None
        else:  # assemblies
            self.update_table("assemblies")
            if self.selected_assembly_id:
                for item in self.assembly_table.get_children():
                    if self.assembly_table.item(item)["tags"][0] == self.selected_assembly_id:
                        self.assembly_table.selection_set(item)
                        self.fetch_assembly_attachments(None)
                        break
                else:
                    self.assembly_table.selection_remove(self.assembly_table.selection())
                    self.assembly_attachment_table.delete(*self.assembly_attachment_table.get_children())
                    self.assembly_no_attachments_label.place_forget()
                    self.selected_assembly_id = None

    def update_table(self, item_type):
        table = self.package_table if item_type == "packages" else self.assembly_table
        items = self.packages if item_type == "packages" else self.assemblies
        attachment_table = self.package_attachment_table if item_type == "packages" else self.assembly_attachment_table
        no_attachments_label = self.package_no_attachments_label if item_type == "packages" else self.assembly_no_attachments_label
        for item in table.get_children():
            table.delete(item)
        if item_type == "packages":
            for item in items:
                table.insert("", "end", values=(item.get("name", ""), item.get("description", ""), item.get("assembly_count", 0)),
                             tags=(item.get("id", ""),))
        else:
            for item in items:
                table.insert("", "end", values=(item.get("name", ""), item.get("description", "")),
                             tags=(item.get("id", ""),))
        if not items:
            for item in attachment_table.get_children():
                attachment_table.delete(item)
            no_attachments_label.place_forget()
            if item_type == "packages":
                for var in self.property_fields.values():
                    var.set("")
                self.unsaved_alert.grid_remove()

    def clear_tables_and_fields(self):
        for table in [self.package_table, self.package_attachment_table, self.assembly_table, self.assembly_attachment_table]:
            for item in table.get_children():
                table.delete(item)
        for var in self.property_fields.values():
            var.set("")
        self.unsaved_alert.grid_remove()
        self.package_no_attachments_label.place_forget()
        self.assembly_no_attachments_label.place_forget()

    def fetch_projects(self):
        params = {"include": "id,name", "pagesize": 1000, "disabletotal": True}
        try:
            response = make_api_request(f"{BASE_URL}{PROJECT_ENDPOINT}", HEADERS, params, "Fetch projects")
            self.all_projects = response.json().get("data", [])
            if not self.all_projects:
                messagebox.showwarning("No Projects", "No projects found.")
                self.project_dropdown.configure(state="disabled")
                return
            self.projects = self.all_projects
            project_names = ["Choose Project"] + [p.get("name", "Unnamed") for p in self.projects]
            self.project_dropdown["values"] = project_names
            self.project_dropdown.current(0)
        except RequestException:
            self.project_dropdown.configure(state="disabled")

    def fetch_packages(self, event):
        selected_index = self.project_dropdown.current()
        if selected_index <= 0 or not self.projects:
            self.clear_tables_and_fields()
            self.selected_package_id = None
            return
        project_id = self.projects[selected_index - 1].get("id")
        if not project_id:
            messagebox.showerror("Error", "Selected project has no ID.")
            return
        self.fetch_packages_by_id(project_id)

    def fetch_packages_by_id(self, project_id):
        self.clear_tables_and_fields()
        params = {
            "include": ("id,name,description,number,categoryId,hoursEstimatedField,"
                        "hoursEstimatedOffice,hoursEstimatedPurchasing,hoursEstimatedShop,"
                        "officeDuration,purchasingDuration,shopDuration,installedDT,"
                        "officeStartDT,purchasingStartDT,requiredDT,startDT,status"),
            "where": f"projectId eq '{project_id}'",
            "page": 0,
            "pagesize": 1000,
            "disabletotal": True
        }
        self.all_packages = []
        page = 0
        while True:
            params["page"] = page
            try:
                response = make_api_request(f"{BASE_URL}{PACKAGE_ENDPOINT}", HEADERS, params, "Fetch packages")
                data = response.json()
                packages = data.get("data", [])
                for pkg in packages:
                    pkg["assembly_count"] = self.get_assembly_count(pkg.get("id"))
                self.all_packages.extend(packages)
                if not packages or len(packages) < params["pagesize"] or data.get("truncatedResults", False):
                    break
                page += 1
            except RequestException:
                return
        self.packages = self.all_packages
        self.update_table("packages")
        if not self.packages:
            messagebox.showinfo("No Packages", f"No packages found for Project ID {project_id}.")

    def get_assembly_count(self, package_id):
        if not package_id:
            return 0
        params = {"include": "id", "page": 0, "pagesize": 1000, "disabletotal": True}
        total_count = 0
        page = 0
        while True:
            params["page"] = page
            try:
                response = make_api_request(f"{BASE_URL}/v2/package/{package_id}/assemblies",
                                            HEADERS, params, f"Fetch assembly count for package {package_id}")
                data = response.json()
                assemblies = data.get("data", [])
                total_count += len(assemblies)
                if not assemblies or len(assemblies) < params["pagesize"] or data.get("truncatedResults", False):
                    break
                page += 1
            except RequestException:
                return 0
        return total_count

    def fetch_activity_logs(self):
        """Fetch activity logs."""
        params = {
            "include": "createdDT,referenceName",
            "pagesize": 1000,
            "disabletotal": True,
            "where": "createdDT ge DateTime.Now.AddDays(-30)"
        }
        try:
            response = make_api_request(f"{BASE_URL}/v1/activity", HEADERS, params, "Fetch activity logs")
            self.activity_logs = response.json().get("data", [])
            for item in self.activity_table.get_children():
                self.activity_table.delete(item)
            for log in self.activity_logs:
                created_dt = log.get("createdDT", "")
                if created_dt:
                    try:
                        created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                self.activity_table.insert("", "end",
                                          values=(created_dt,
                                                  log.get("referenceName", "")))
            if not self.activity_logs:
                messagebox.showinfo("No Activity Logs", "No activity logs found.")
        except RequestException:
            pass

    def fetch_users(self):
        params = {"include": "id,firstName,lastName,email,status", "pagesize": 1000, "disabletotal": True}
        try:
            response = make_api_request(f"{BASE_URL}/v2/user", HEADERS, params, "Fetch users")
            self.users = response.json().get("data", [])
            for item in self.users_table.get_children():
                self.users_table.delete(item)
            for user in self.users:
                status = "Active" if user.get("status") == 1 else "Disabled"
                self.users_table.insert("", "end",
                                        values=(user.get("firstName", ""),
                                                user.get("lastName", ""),
                                                user.get("email", ""),
                                                status))
            if not self.users:
                messagebox.showinfo("No Users", "No users found.")
        except RequestException:
            pass

    def fetch_containers(self):
        params = {"include": "id,name,description", "pagesize": 1000, "disabletotal": True}
        try:
            response = make_api_request(f"{BASE_URL}/v1/container", HEADERS, params, "Fetch containers")
            self.containers = response.json().get("data", [])
            for item in self.containers_table.get_children():
                self.containers_table.delete(item)
            for container in self.containers:
                self.containers_table.insert("", "end",
                                             values=(container.get("name", ""),
                                                     container.get("description", "")))
            if not self.containers:
                messagebox.showinfo("No Containers", "No containers found.")
        except RequestException:
            pass

    def fetch_health(self):
        """Fetch API health data from the /health endpoint."""
        try:
            response = make_api_request(f"{BASE_URL}/health", HEADERS, {}, "Fetch API health")
            data = response.json()

            # Clear existing table data
            for item in self.health_table.get_children():
                self.health_table.delete(item)

            # Handle different response types
            if isinstance(data, dict):
                # Single object: display as key-value pairs
                self.health_table["columns"] = ("key", "value")
                self.health_table.heading("key", text="Key")
                self.health_table.heading("value", text="Value")
                self.health_table.column("key", width=200)
                self.health_table.column("value", width=300)
                self.health_data = [{"key": k, "value": str(v)} for k, v in data.items()]
                for item in self.health_data:
                    self.health_table.insert("", "end", values=(item["key"], item["value"]))
            elif isinstance(data, list) and data:
                # List of objects: use keys from the first object as columns
                columns = list(data[0].keys())
                self.health_table["columns"] = columns
                for col in columns:
                    self.health_table.heading(col, text=col.replace("_", " ").title())
                    self.health_table.column(col, width=150)  # Default width
                self.health_data = data
                for item in self.health_data:
                    values = [str(item.get(col, "")) for col in columns]
                    self.health_table.insert("", "end", values=values)
            else:
                messagebox.showinfo("No Health Data", "No health data found.")
                self.health_data = []

            if not self.health_data:
                messagebox.showinfo("No Health Data", "No health data found.")

        except RequestException:
            for item in self.health_table.get_children():
                self.health_table.delete(item)
            self.health_data = []
            messagebox.showerror("Error", "Failed to fetch API health data.")

    def on_package_select(self, event):
        selected = self.package_table.selection()
        if not selected:
            self.clear_tables_and_fields()
            self.selected_package_id = None
            return
        self.selected_package_id = self.package_table.item(selected[0])["tags"][0]
        for pkg in self.packages:
            if pkg.get("id") == self.selected_package_id:
                self.package_data = pkg
                break
        self.update_properties_fields()
        self.fetch_package_attachments()
        self.fetch_assemblies()

    def update_properties_fields(self):
        self.initial_field_values = {}
        for key, var in self.property_fields.items():
            if key == "status":
                value = self.package_data.get(key, 0)
                var.set(f"Active (0)" if value == 0 else "Archived (1)")
            else:
                var.set(self.package_data.get(key, "") or "")
            self.initial_field_values[key] = var.get()
        self.unsaved_alert.grid_remove()

    def fetch_package_attachments(self):
        if not self.selected_package_id:
            for item in self.package_attachment_table.get_children():
                self.package_attachment_table.delete(item)
            self.package_no_attachments_label.place_forget()
            return
        params = {"include": "id,fileName,createdDT", "page": 0, "pagesize": 1000, "disabletotal": True}
        try:
            response = make_api_request(f"{BASE_URL}/v1/package/{self.selected_package_id}/attachments",
                                        HEADERS, params, "Fetch package attachments")
            self.package_attachments = response.json().get("data", [])
            for item in self.package_attachment_table.get_children():
                self.package_attachment_table.delete(item)
            for att in self.package_attachments:
                created_dt = att.get("createdDT", "")
                if created_dt:
                    try:
                        created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                self.package_attachment_table.insert("", "end", values=(att.get("fileName", ""), created_dt),
                                                     tags=(att.get("id", ""),))
            self.package_no_attachments_label.place(relx=0.5, rely=0.5, anchor="center") if not self.package_attachments else self.package_no_attachments_label.place_forget()
        except RequestException:
            for item in self.package_attachment_table.get_children():
                self.package_attachment_table.delete(item)
            self.package_no_attachments_label.place_forget()

    def fetch_assemblies(self):
        if not self.selected_package_id:
            for item in self.assembly_table.get_children():
                self.assembly_table.delete(item)
            for item in self.assembly_attachment_table.get_children():
                self.assembly_attachment_table.delete(item)
            self.assembly_no_attachments_label.place_forget()
            return
        params = {"include": "id,name,description", "page": 0, "pagesize": 1000, "disabletotal": True}
        self.all_assemblies = []
        page = 0
        while True:
            params["page"] = page
            try:
                response = make_api_request(f"{BASE_URL}/v2/package/{self.selected_package_id}/assemblies",
                                            HEADERS, params, "Fetch assemblies")
                data = response.json()
                assemblies = data.get("data", [])
                self.all_assemblies.extend(assemblies)
                if not assemblies or len(assemblies) < params["pagesize"] or data.get("truncatedResults", False):
                    break
                page += 1
            except RequestException:
                for item in self.assembly_table.get_children():
                    self.assembly_table.delete(item)
                for item in self.assembly_attachment_table.get_children():
                    self.assembly_attachment_table.delete(item)
                self.assembly_no_attachments_label.place_forget()
                return
        self.assemblies = self.all_assemblies
        self.update_table("assemblies")
        if not self.assemblies:
            messagebox.showinfo("No Assemblies", f"No assemblies found for Package ID {self.selected_package_id}.")

    def fetch_assembly_attachments(self, event):
        """Fetch attachments for the selected assembly."""
        selected = self.assembly_table.selection()
        if not selected:
            for item in self.assembly_attachment_table.get_children():
                self.assembly_attachment_table.delete(item)
            self.selected_assembly_id = None
            self.assembly_no_attachments_label.place_forget()
            return
        self.selected_assembly_id = self.assembly_table.item(selected[0])["tags"][0]
        params = {"include": "id,fileName,createdDT", "page": 0, "pagesize": 1000, "disabletotal": True}
        try:
            response = make_api_request(f"{BASE_URL}/v1/assembly/{self.selected_assembly_id}/attachments",
                                        HEADERS, params, "Fetch assembly attachments")
            self.assembly_attachments = response.json().get("data", [])
            for item in self.assembly_attachment_table.get_children():
                self.assembly_attachment_table.delete(item)
            for att in self.assembly_attachments:
                created_dt = att.get("createdDT", "")
                if created_dt:
                    try:
                        created_dt = datetime.fromisoformat(created_dt.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                self.assembly_attachment_table.insert("", "end", values=(att.get("fileName", ""), created_dt),
                                                      tags=(att.get("id", ""),))
            self.assembly_no_attachments_label.place(relx=0.5, rely=0.5, anchor="center") if not self.assembly_attachments else self.assembly_no_attachments_label.place_forget()
        except RequestException:
            for item in self.assembly_attachment_table.get_children():
                self.assembly_attachment_table.delete(item)
            self.assembly_no_attachments_label.place_forget()

    def check_property_changes(self, event=None):
        changed = any(var.get() != self.initial_field_values.get(key, "") for key, var in self.property_fields.items())
        self.unsaved_alert.grid() if changed else self.unsaved_alert.grid_remove()

    def apply_property_changes(self):
        if not self.selected_package_id:
            messagebox.showwarning("No Package Selected", "Please select a package to apply changes.")
            return
        package_patch_data = {"id": self.selected_package_id}
        package_changed = False
        for key, var in self.property_fields.items():
            current_value = var.get()
            initial_value = self.initial_field_values.get(key, "")
            if current_value != initial_value:
                if key == "status":
                    try:
                        package_patch_data[key] = 0 if current_value == "Active (0)" else 1
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid status value: {current_value}")
                        return
                elif key in ["hoursEstimatedField", "hoursEstimatedOffice", "hoursEstimatedPurchasing",
                             "hoursEstimatedShop", "officeDuration", "purchasingDuration", "shopDuration"]:
                    try:
                        package_patch_data[key] = int(current_value) if current_value else 0
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid value for {key}: must be an integer.")
                        return
                elif key in ["installedDT", "officeStartDT", "purchasingStartDT", "requiredDT", "startDT"]:
                    if current_value:
                        try:
                            datetime.fromisoformat(current_value.replace("Z", "+00:00"))
                            package_patch_data[key] = current_value
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid date format for {key}: use YYYY-MM-DDTHH:MM:SSZ.")
                            return
                    else:
                        package_patch_data[key] = None
                else:
                    package_patch_data[key] = current_value if current_value else None
                package_changed = True
        if not package_changed:
            messagebox.showinfo("No Changes", "No changes to apply.")
            return
        try:
            response = requests.patch(f"{BASE_URL}/v2/package/properties", headers=HEADERS,
                                     json=package_patch_data, timeout=10)
            response.raise_for_status()
            for key, value in package_patch_data.items():
                if key != "id":
                    self.package_data[key] = value
            messagebox.showinfo("Success", "Package properties updated successfully.")
            project_id = self.projects[self.project_dropdown.current() - 1]["id"] if self.project_dropdown.current() > 0 else None
            if project_id:
                self.fetch_packages_by_id(project_id)
                for item in self.package_table.get_children():
                    if self.package_table.item(item)["tags"][0] == self.selected_package_id:
                        self.package_table.selection_set(item)
                        break
            self.update_properties_fields()
            self.check_property_changes()
        except RequestException as e:
            handle_request_error(e, "Failed to apply properties")

    def download_selected_package_attachments(self):
        selected = self.package_attachment_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one package attachment to download.")
            return
        save_dir = filedialog.askdirectory(title="Select Download Directory")
        if not save_dir:
            return
        for item in selected:
            att_id = self.package_attachment_table.item(item)["tags"][0]
            file_name = self.package_attachment_table.item(item)["values"][0] or f"attachment_{att_id}"
            self.download_attachment(att_id, file_name, save_dir)

    def download_all_package_attachments(self):
        if not self.package_attachments:
            messagebox.showwarning("No Package Attachments", "No package attachments available to download.")
            return
        save_dir = filedialog.askdirectory(title="Select Download Directory")
        if not save_dir:
            return
        for att in self.package_attachments:
            att_id = att.get("id", "")
            file_name = att.get("fileName", f"attachment_{att_id}")
            self.download_attachment(att_id, file_name, save_dir)

    def download_selected_assembly_attachments(self):
        selected = self.assembly_attachment_table.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one assembly attachment to download.")
            return
        save_dir = filedialog.askdirectory(title="Select Download Directory")
        if not save_dir:
            return
        for item in selected:
            att_id = self.assembly_attachment_table.item(item)["tags"][0]
            file_name = self.assembly_attachment_table.item(item)["values"][0] or f"attachment_{att_id}"
            self.download_attachment(att_id, file_name, save_dir)

    def download_all_assembly_attachments(self):
        if not self.assembly_attachments:
            messagebox.showwarning("No Assembly Attachments", "No assembly attachments available to download.")
            return
        save_dir = filedialog.askdirectory(title="Select Download Directory")
        if not save_dir:
            return
        for att in self.assembly_attachments:
            att_id = att.get("id", "")
            file_name = att.get("fileName", f"attachment_{att_id}")
            self.download_attachment(att_id, file_name, save_dir)

    def download_attachment(self, att_id, file_name, save_dir):
        try:
            response = make_api_request(f"{BASE_URL}/v1/attachment/{att_id}/download",
                                       HEADERS, {}, f"Download attachment {file_name}", stream=True)
            save_path = os.path.join(save_dir, file_name)
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except (RequestException, OSError) as e:
            messagebox.showerror("Error", f"Failed to download/save attachment {file_name}: {e}")

    def browse_package_file(self):
        file_path = filedialog.askopenfilename(title="Select File to Upload")
        if file_path:
            self.package_upload_var.set(file_path)

    def browse_assembly_file(self):
        file_path = filedialog.askopenfilename(title="Select File to Upload")
        if file_path:
            self.assembly_upload_var.set(file_path)

    def upload_package_attachment(self):
        if not self.selected_package_id:
            messagebox.showwarning("No Package Selected", "Please select a package to upload an attachment.")
            return
        file_path = self.package_upload_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("No File Selected", "Please select a valid file to upload.")
            return
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                response = requests.post(f"{BASE_URL}/v1/package/{self.selected_package_id}/attachment",
                                        headers=HEADERS, files=files, timeout=10)
                response.raise_for_status()
                messagebox.showinfo("Success", f"Successfully uploaded {os.path.basename(file_path)}")
                self.package_upload_var.set("")
                self.fetch_package_attachments()
        except (RequestException, OSError) as e:
            messagebox.showerror("Error", f"Failed to upload package attachment: {e}")

    def upload_assembly_attachment(self):
        selected = self.assembly_table.selection()
        if not selected:
            messagebox.showwarning("No Assembly Selected", "Please select an assembly to upload an attachment.")
            return
        assembly_id = self.assembly_table.item(selected[0])["tags"][0]
        file_path = self.assembly_upload_var.get()
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("No File Selected", "Please select a valid file to upload.")
            return
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f)}
                response = requests.post(f"{BASE_URL}/v1/assembly/{assembly_id}/attachment",
                                        headers=HEADERS, files=files, timeout=10)
                response.raise_for_status()
                messagebox.showinfo("Success", f"Successfully uploaded {os.path.basename(file_path)}")
                self.assembly_upload_var.set("")
                self.fetch_assembly_attachments(None)
        except (RequestException, OSError) as e:
            messagebox.showerror("Error", f"Failed to upload assembly attachment: {e}")

    def refresh_tables(self):
        project_index = self.project_dropdown.current()
        project_filter_text = self.project_filter.get()
        package_filter_text = self.package_filter.get()
        selected_package_id = self.selected_package_id
        assembly_filter_text = self.assembly_filter.get()
        selected_assembly_id = self.selected_assembly_id
        current_tab = self.notebook.index(self.notebook.select())
        self.fetch_projects()
        self.project_filter.delete(0, tb.END)
        self.project_filter.insert(0, project_filter_text)
        self.filter_items("projects")
        if project_index >= 0 and project_index < len(self.project_dropdown["values"]):
            self.project_dropdown.current(project_index)
            if project_index > 0:
                project_id = self.projects[project_index - 1].get("id")
                self.fetch_packages_by_id(project_id)
                self.package_filter.delete(0, tb.END)
                self.package_filter.insert(0, package_filter_text)
                self.filter_items("packages")
                if selected_package_id:
                    for item in self.package_table.get_children():
                        if self.package_table.item(item)["tags"][0] == selected_package_id:
                            self.package_table.selection_set(item)
                            self.selected_package_id = selected_package_id
                            self.fetch_package_attachments()
                            self.fetch_assemblies()
                            self.assembly_filter.delete(0, tb.END)
                            self.assembly_filter.insert(0, assembly_filter_text)
                            self.filter_items("assemblies")
                            self.update_properties_fields()
                            if selected_assembly_id:
                                for item in self.assembly_table.get_children():
                                    if self.assembly_table.item(item)["tags"][0] == selected_assembly_id:
                                        self.assembly_table.selection_set(item)
                                        self.fetch_assembly_attachments(None)
                                        break
        self.fetch_activity_logs()
        self.fetch_users()
        self.fetch_containers()
        self.fetch_health()
        self.notebook.select(current_tab)

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    window_width = 1980
    window_height = 1000
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    APP_KEY = get_api_key(root)
    HEADERS = {"app-key": APP_KEY, "Accept": "application/json"}
    app = StratusGUI(root)
    root.mainloop()
