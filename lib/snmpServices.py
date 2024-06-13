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
from swgAPI import force_api_logout, get_appliance_uuid

def fetch_snmp_config_from_bluecoat(source_ip, source_port, source_username, source_password):
    # Fetch snmp services from Bluecoat using SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(source_ip, port=source_port, username=source_username, password=source_password, timeout=10)
        
        # Run the command to get snmp services
        stdin, stdout, stderr = client.exec_command("show snmp")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        return command_output
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None
    finally:
        # Close the connection
        client.close()

def convert_snmp_config_to_skyhigh_format(bluecoat_snmp_config):
    # Convert Bluecoat snmp services to SkyHigh format
    converted_lines = []
    current_service_lines = []
    service_type = ""

    bluecoat_lines = bluecoat_snmp_config.splitlines()

    for line in bluecoat_lines:
        if line.startswith("Service Name:"):
            if current_service_lines:
                # Process the current service
                process_service_block(current_service_lines, converted_lines, service_type)
                current_service_lines = []
            service_type = ""

        current_service_lines.append(line)

        if line.startswith("snmp:"):
            if "HTTP" in line:
                service_type = "HTTP"
            elif "TCP Tunnel" in line:
                service_type = "TCP"
            elif "FTP" in line:
                service_type = "FTP"
            elif "Telnet" in line:
                service_type = "TCP"

    if current_service_lines:
        process_service_block(current_service_lines, converted_lines, service_type)

    converted_data = "\n".join(converted_lines)
    return converted_data

def migrate_snmp_config(source_ip, source_port, source_username, source_password, dest_ip, dest_port, dest_user, dest_pass, app_version):
    try:
        # Step 1: Fetch snmp services from Bluecoat
        bluecoat_snmp_config = fetch_snmp_config_from_bluecoat(source_ip, source_port, source_username, source_password)
        if not bluecoat_snmp_config:
            return
        
        # Step 2: Convert fetched snmp services to SkyHigh format
        skyhigh_snmp_config = convert_snmp_config_to_skyhigh_format(bluecoat_snmp_config)

        # Step 3: Save converted snmp services to a temporary file
        temp_snmp_config_file = f"{source_ip}_snmp_config.csv"
        with open(temp_snmp_config_file, "w") as file:
            file.write(skyhigh_snmp_config)
            
        messagebox.showinfo("Success", f"SNMP Config has been fetched, converted, saved to {temp_snmp_config_file}, and uploaded to the Skyhigh Web Gateway.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to migrate SNMP Config: {e}")