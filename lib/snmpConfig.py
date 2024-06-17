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
        
        # Process the command output to capture the "listener ports", SNMP versions, SNMPv3 users, and traps
        lines = command_output.splitlines()
        listener_ports = []
        snmp_versions = []
        snmpv3_users = []
        traps = []
        capture_listeners = False
        capture_users = False
        capture_traps = False
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
                    capture_traps = True
                    continue
                
                if line.strip() and line.startswith(' '):
                    current_user.append(line.strip())
                    if len(current_user) == 4:
                        username = current_user[0].split(':')[0].strip()
                        auth_algorithm = current_user[1].split(': ')[1].split(',')[0].strip()
                        priv_algorithm = current_user[2].split(': ')[1].split(',')[0].strip()
                        permission = current_user[3].strip()
                        snmpv3_users.append([username, auth_algorithm, priv_algorithm, permission])
                        current_user = []

            if capture_traps:
                trap_match = re.match(r'\s*Trap: (\S+) (\d+\.\d+\.\d+\.\d+), port (\d+)', line)
                if trap_match:
                    protocol = trap_match.group(1)
                    ip_address = trap_match.group(2)
                    port_number = trap_match.group(3)
                    trap_number = len(traps) + 1
                    traps.append([f'trap{trap_number}', protocol, ip_address, port_number])

        if current_user and len(current_user) == 4:
            username = current_user[0].split(':')[0].strip()
            auth_algorithm = current_user[1].split(': ')[1].split(',')[0].strip()
            priv_algorithm = current_user[2].split(': ')[1].split(',')[0].strip()
            permission = current_user[3].strip()
            snmpv3_users.append([username, auth_algorithm, priv_algorithm, permission])

        if not listener_ports:
            raise Exception("No listener ports found in the SNMP configuration.")
        if not snmp_versions:
            raise Exception("No SNMP versions found in the SNMP configuration.")
        if not snmpv3_users:
            raise Exception("No SNMPv3 users found in the SNMP configuration.")
        if not traps:
            raise Exception("No traps found in the SNMP configuration.")
        
        return listener_ports, snmp_versions, snmpv3_users, traps

    except Exception as e:
        messagebox.showerror("Error", str(e))
        return None, None, None, None
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

    # Modify the XML based on user input
    root = ET.fromstring(existing_xml)

    def prompt_for_protocol(protocol):
        return messagebox.askquestion(f"Enable {protocol}", f"Do you want to enable {protocol}?", icon='question', type='yesno', default='yes')

    snmp_v1_status = prompt_for_protocol("SNMP v1")
    snmp_v2c_status = prompt_for_protocol("SNMP v2c")
    snmp_v3_status = prompt_for_protocol("SNMP v3")

    protocol_map = {
        "snmp.agent.allowprotocolv1": snmp_v1_status,
        "snmp.agent.allowprotocolv2c": snmp_v2c_status,
        "snmp.agent.allowprotocolv3": snmp_v3_status
    }

    for key, status in protocol_map.items():
        value = "true" if status == 'yes' else "false"
        prop = root.find(f".//configurationProperty[@key='{key}']")
        if prop is not None:
            prop.set("value", value)
        else:
            new_prop = ET.SubElement(root, "configurationProperty", {
                "key": key,
                "type": "com.scur.type.boolean",
                "encrypted": "false",
                "value": value
            })

    # Save the modified XML locally for testing
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)
    modified_xml_file = outputs_dir / f'{dest_ip}_modified_snmp_config.xml'
    with open(modified_xml_file, 'w') as file:
        file.write(ET.tostring(root, encoding='unicode'))

    # Upload the modified XML
    try:
        response = subprocess.run(
            ['curl', '-k', '-c', 'cookies.txt', '-u', f'{dest_user}:{dest_pass}', '-X', 'PUT', '-d', f'@{modified_xml_file}', f'{route_url}', '-H', 'Content-Type: application/xml'],
            capture_output=True,
            text=True
        )
        curl_output = response.stdout
        if response.returncode != 0:
            raise Exception(f"Failed to upload modified SNMP Configuration. {curl_output}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to upload modified SNMP Configuration: {e}")
        return

    return bluecoat_snmp_config

def migrate_snmp_config(source_ip, source_port, source_username, source_password, dest_ip, dest_port, dest_user, dest_pass, app_version):
    try:
        # Step 1: Fetch snmp config from Bluecoat
        bluecoat_snmp_config, snmp_versions, snmpv3_users, traps = fetch_snmp_config_from_bluecoat(source_ip, source_port, source_username, source_password)
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
            for trap in traps:
                file.write(','.join(trap) + '\n')
    
        # Commit changes
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:{port}/Konfigurator/REST/commit'
        subprocess.run(curl_command, shell=True)
        # Logout
        force_api_logout(dest_ip, dest_port)

        messagebox.showinfo("Success", f"SNMP Config has been fetched, converted, saved to {temp_snmp_config_file}, and uploaded to the Skyhigh Web Gateway.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to migrate SNMP Config: {e}")
