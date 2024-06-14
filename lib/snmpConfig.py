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
    # Fetch snmp config from Bluecoat using SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(source_ip, port=source_port, username=source_username, password=source_password, timeout=10)
        
        # Run the command to get snmp config
        stdin, stdout, stderr = client.exec_command("show snmp")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        
        # Process the command output to capture the "listener ports", SNMP versions, and SNMPv3 users
        lines = command_output.splitlines()
        listener_ports = []
        snmp_versions = []
        snmpv3_users = []
        capture_listeners = False
        capture_users = False
        current_user = []
        
        for line in lines:
            if line.startswith("Destination IP"):
                capture_listeners = True
                continue  # Skip the "Destination IP" label line
            if capture_listeners:
                if line.startswith("SNMPv"):
                    snmp_versions = re.findall(r'SNMP(v[^\s]+) is (\w+)', line)
                    capture_listeners = False
                elif line.strip():  # Ensure the line is not empty
                    parts = re.split(r'\s+', line.strip())
                    if len(parts) >= 3:
                        listener_ports.append(parts[:3])
            
            if line.strip().startswith("SNMPv3 users:"):
                capture_users = True
                continue
            
            if capture_users:
                if re.match(r'\s*Trap:', line):
                    capture_users = False
                    continue
                
                if line.strip() and line.startswith(' '):
                    current_user.append(line.strip())
                elif current_user:
                    if len(current_user) == 4:
                        username = current_user[0].split(':')[0]
                        auth_algorithm = current_user[1].split(': ')[1].split(',')[0]
                        priv_algorithm = current_user[2].split(': ')[1].split(',')[0]
                        permission = current_user[3]
                        snmpv3_users.append([username, auth_algorithm, priv_algorithm, permission])
                    current_user = []
                    if line.strip():
                        current_user.append(line.strip())

        if current_user and len(current_user) == 4:
            username = current_user[0].split(':')[0]
            auth_algorithm = current_user[1].split(': ')[1].split(',')[0]
            priv_algorithm = current_user[2].split(': ')[1].split(',')[0]
            permission = current_user[3]
            snmpv3_users.append([username, auth_algorithm, priv_algorithm, permission])

        if not listener_ports:
            raise Exception("No listener ports found in the SNMP configuration.")
        if not snmp_versions:
            raise Exception("No SNMP versions found in the SNMP configuration.")
        if not snmpv3_users:
            raise Exception("No SNMPv3 users found in the SNMP configuration.")
        
        return listener_ports, snmp_versions, snmpv3_users

    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None, None, None
    finally:
        # Close the connection
        client.close()

def convert_snmp_config_to_skyhigh_format(bluecoat_snmp_config, dest_ip, dest_port, dest_user, dest_pass):
    # Convert Bluecoat snmp config to SkyHigh format
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass, dest_port)
    if not uuid:
        return  # Stop if UUID could not be retrieved
    
    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header, "Content-Type": "application/xml"}
    route_url = f"https://{dest_ip}:{dest_port}/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.appliance.snmp.configuration"
   
    if not route_url:
        messagebox.showerror("Error", "Unknown configuration.")
        return

    # Fetch existing configuration
    try:
        response = requests.get(route_url, headers=headers, verify=False)
        existing_xml = response.text
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch existing SNMP Configuration: {e}")
        return
    
    # Save the modified XML locally for testing
    with open(f'outputs/{dest_ip}_snmp_config.xml', 'w') as new_xml_file:
        new_xml_file.write(existing_xml)

    # Logout
    force_api_logout(dest_ip, dest_port)        

    return bluecoat_snmp_config

def migrate_snmp_config(source_ip, source_port, source_username, source_password, dest_ip, dest_port, dest_user, dest_pass, app_version):
    try:
        # Step 1: Fetch snmp config from Bluecoat
        bluecoat_snmp_config, snmp_versions, snmpv3_users = fetch_snmp_config_from_bluecoat(source_ip, source_port, source_username, source_password)
        if not bluecoat_snmp_config:
            return
        
        # Step 2: Convert fetched snmp config to SkyHigh format
        skyhigh_snmp_config = convert_snmp_config_to_skyhigh_format(bluecoat_snmp_config, dest_ip, dest_port, dest_user, dest_pass)

        # Step 3: Save converted snmp config to a temporary file
        outputs_dir = Path("outputs")
        outputs_dir.mkdir(exist_ok=True)
        temp_snmp_config_file = outputs_dir / f"{source_ip}_snmp_config.csv"
        with open(temp_snmp_config_file, "w") as file:
            for listener in bluecoat_snmp_config:
                file.write(','.join(listener) + '\n')
            for version, status in snmp_versions:
                file.write(f'SNMP{version},{status}\n')
            for user in snmpv3_users:
                file.write(','.join(user) + '\n')
            
        messagebox.showinfo("Success", f"SNMP Config has been fetched, converted, saved to {temp_snmp_config_file}, and uploaded to the Skyhigh Web Gateway.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to migrate SNMP Config: {e}")
