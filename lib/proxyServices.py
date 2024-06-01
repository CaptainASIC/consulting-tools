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

def fetch_proxy_services_from_bluecoat(source_ip, source_port, source_username, source_password):
    # Fetch proxy services from Bluecoat using SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(source_ip, port=source_port, username=source_username, password=source_password, timeout=10)
        
        # Run the command to get proxy services
        stdin, stdout, stderr = client.exec_command("show proxy-services")
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

def convert_proxy_services_to_skyhigh_format(bluecoat_proxy_services):
    # Convert Bluecoat proxy services to SkyHigh format
    converted_lines = []
    current_service_lines = []
    service_type = ""

    bluecoat_lines = bluecoat_proxy_services.splitlines()

    for line in bluecoat_lines:
        if line.startswith("Service Name:"):
            if current_service_lines:
                # Process the current service
                process_service_block(current_service_lines, converted_lines, service_type)
                current_service_lines = []
            service_type = ""

        current_service_lines.append(line)

        if line.startswith("Proxy:"):
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

def process_service_block(service_lines, converted_lines, service_type):
    capture = False
    for line in service_lines:
        if line.startswith("Source IP"):
            capture = True
        elif capture and line.strip() and not line.strip().endswith("Bypass"):
            # Replace all whitespace (tabs and spaces) with commas
            parts = re.sub(r'\s+', ',', line.strip()).split(',')
            if len(parts) >= 3:
                # Replace the destination with 0.0.0.0 and remove source IP and mode
                converted_line = f"{service_type},0.0.0.0,{parts[2]}"
                converted_lines.append(converted_line)

def migrate_proxy_services(source_ip, source_port, source_username, source_password, dest_ip, dest_port, dest_user, dest_pass, app_version):
    try:
        # Step 1: Fetch proxy services from Bluecoat
        bluecoat_proxy_services = fetch_proxy_services_from_bluecoat(source_ip, source_port, source_username, source_password)
        if not bluecoat_proxy_services:
            return
        
        # Step 2: Convert fetched proxy services to SkyHigh format
        skyhigh_proxy_services = convert_proxy_services_to_skyhigh_format(bluecoat_proxy_services)

        # Step 3: Save converted proxy services to a temporary file
        temp_proxy_services_file = f"{source_ip}_proxy_services.csv"
        with open(temp_proxy_services_file, "w") as file:
            file.write(skyhigh_proxy_services)

        # Step 4: Upload to SWG
        post_proxy_services(app_version, dest_ip, dest_user, dest_pass, temp_proxy_services_file, dest_port)

        messagebox.showinfo("Success", f"Proxy services have been fetched, converted, saved to {temp_proxy_services_file}, and uploaded to the Skyhigh Web Gateway.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to migrate proxy services: {e}")

def post_proxy_services(app_version, dest_ip, dest_user, dest_pass, filename, port=4712):
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass, port)
    if not uuid:
        return  # Stop if UUID could not be retrieved

    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header, "Content-Type": "application/xml"}

    route_url = f"https://{dest_ip}:{port}/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.proxy.configuration/property/HTTPListener"
    try:
        response = requests.get(route_url, headers=headers, verify=False)
        existing_xml = response.text
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch existing proxy services: {e}")
        return

    # Step 2: Modify the XML with new routes
    try:
        with open(filename, "r") as file:
            new_routes = file.readlines()
        new_entries = ''
        for line in new_routes:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                new_entries += f'''
                    &lt;listEntry&gt;
                        &lt;complexEntry&gt;
                            &lt;configurationProperties&gt;
                                &lt;configurationProperty key="interface" type="com.scur.type.string" encrypted="false" value="{parts[1]}:{parts[2]}"/&gt;
                                &lt;configurationProperty key="transparent_requests" type="com.scur.type.boolean" encrypted="false" value="true"/&gt;
                                &lt;configurationProperty key="transparent_cn_handling" type="com.scur.type.boolean" encrypted="false" value="false"/&gt;
                                &lt;configurationProperty key="serverPassiveConnection" type="com.scur.type.boolean" encrypted="false" value="true"/&gt;
                                &lt;configurationProperty key="proxy_protocol_header" type="com.scur.type.boolean" encrypted="false" value="false"/&gt;
                                &lt;configurationProperty key="sslPorts" type="com.scur.type.string" encrypted="false" value="443"/&gt;
                                &lt;configurationProperty key="mss" type="com.scur.type.number" encrypted="false" value="0"/&gt;
                            &lt;/configurationProperties&gt;
                        &lt;/complexEntry&gt;&lt;description&gt;Imported Using Bluecoat to SkyHigh Web Gateway Migration Assistant Utility Version: {app_version}&lt;/description&gt;&lt;/listEntry&gt;'''

        # Append XML       
        # Insert new entries before </content>
        modified_xml = existing_xml.replace('&lt;/content&gt;', f'{new_entries}&lt;/content&gt;')

        # Save the modified XML locally for testing
        with open('new_routes.xml', 'w') as new_xml_file:
            new_xml_file.write(modified_xml)

        # Step 3: Upload the modified XML
        result = subprocess.run(
            ['curl', '-k', '-c', 'cookies.txt', '-u', f'{dest_user}:{dest_pass}', '-X', 'PUT', '-d', f'@{new_xml_file.name}', f'{route_url}', '-H', 'Content-Type: application/xml'],
            capture_output=True,
            text=True
        )
        curl_output = result.stdout

        # Check if the last line contains </entry>
        if '</entry>' not in curl_output:
            messagebox.showerror("Error", f"Failed to update proxy services: {curl_output}")
            return
        

        # Add FTP and TCP here later

        # Commit changes
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:{port}/Konfigurator/REST/commit'
        subprocess.run(curl_command, shell=True)

        # Logout
        force_api_logout(dest_ip, port)

        messagebox.showinfo("Success", "Proxy Services have been updated, committed, and logout was successful.\nPlease log in to the GUI and verify the changes.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to update Proxy Services: {e}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to update Proxy Services: {e}")
