import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess
import requests
import webbrowser
from base64 import b64encode
import configparser
from xml.etree import ElementTree as ET
import re
import paramiko
import os
import sys
from pathlib import Path
from datetime import datetime

def test_bc_connection(source_ip, username, password, port=22):
    # Attempt to fetch identifier via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(source_ip, port=port, username=username, password=password, timeout=10)
        
        # Run the command to get appliance identifier
        stdin, stdout, stderr = client.exec_command("show appliance-identifier")
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        # Extract the appliance ID using regex
        match = re.search(r"Appliance Identifier\s*:\s*(\S+)", output)
        if match:
            bcid = match.group(1)
            messagebox.showinfo("BlueCoat Connection Test", f"Successfully connected to BlueCoat and retrieved Identifier:\n{bcid}")
        else:
            messagebox.showerror("BlueCoat Connection Test", "Failed to retrieve Identifier.")
    except Exception as e:
        messagebox.showerror("BlueCoat Connection Test", f"Failed to connect to BlueCoat: {e}")
    finally:
        client.close()

def test_swg_connection(dest_ip, dest_user, dest_pass, port=4712):
    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header}
    url = f"https://{dest_ip}:{port}/Konfigurator/REST/appliances"
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        # Log the raw XML for debugging
        print("Raw XML Response:", response.text)

        # Parsing XML to get UUID, assuming response is XML and contains <entry><id>UUID</id></entry>
        root = ET.fromstring(response.content)
        uuid = root.find('.//entry/id').text

        messagebox.showinfo("SWG Connection Test", f"Successfully connected to SWG and retrieved UUID:\n{uuid}")
    except Exception as e:
        messagebox.showerror("SWG Connection Test", f"Failed to connect to SWG: {e}")
