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

def fetch_static_routes(source_ip, username, password, filename, port=22):
    # Attempt to fetch static routes via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(source_ip, port=port, username=username, password=password, timeout=10)
        
        # Run the command to get static routes
        stdin, stdout, stderr = client.exec_command("show static-routes")
        output = stdout.read().decode()
        errors = stderr.read().decode()
        
        # Check for errors and write output to file
        if errors:
            raise Exception(errors)
        with open(filename, "w") as f:
            f.write(output)

        messagebox.showinfo("Success", f"Static routes have been saved to {filename}.")
        # Clean up the output and save it again
        clean_and_save_routes(filename)

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()

def clean_and_save_routes(filename):
    # Read the output and apply cleaning
    with open(filename, "r") as file:
        lines = file.readlines()

    start_cleaning = False
    cleaned_data = []

    for line in lines:
        if "default" in line:
            start_cleaning = True  # Start capturing lines from "default"
        elif "Internet6:" in line:
            break  # Break the loop if "Internet6:" appears (stop capturing)

        if start_cleaning:
            # Avoid lines that start with specific words
            if line.startswith(("Routing", "Destination", "default")):
                continue  # Skip lines starting with these words
            # Assuming the format "destination gateway flags refs use netif expi"
            parts = line.split()
            if len(parts) > 1:  # To ensure there's at least destination and gateway
                destination = parts[0]
                gateway = parts[1]
                cleaned_data.append(f"{destination},{gateway}")

    # Assuming the new file name is the original with '_cleaned.csv'
    cleaned_filename = filename.replace('.csv', '_cleaned.csv')

    # Write the cleaned data to a new file
    with open(cleaned_filename, "w") as file:
        for entry in cleaned_data:
            file.write(entry + "\n")

    messagebox.showinfo("Info", f"Cleaned BlueCoat static routes have been saved to {cleaned_filename}.")
    return cleaned_filename

def get_appliance_uuid(dest_ip, dest_user, dest_pass, port=4712):
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

        return uuid
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch UUID: {e}")
        return None

def get_network_routes(dest_ip, dest_user, dest_pass, port=4712):
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass, port)
    if not uuid:
        messagebox.showerror("Error", "Failed to get UUID for GET test.")
        return

    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header}
    route_url = f"https://{dest_ip}:{port}/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.appliance.routes.configuration/property/network.routes.ip4"

    try:
        response = requests.get(route_url, headers=headers, verify=False)
        response.raise_for_status()
        messagebox.showinfo("GET Test", f"Current SWG Network Routes:\n{response.text}")
        
        # Save the XML to a file
        with open('current_network_routes.xml', 'w') as file:
            file.write(response.text)
        messagebox.showinfo("File Saved", "The current SWG network routes have been saved to 'current_network_routes.xml'.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch network routes: {e}")

def post_routes(app_version, dest_ip, dest_user, dest_pass, dest_interface, filename, mode, port=4712):
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass, port)
    if not uuid:
        return  # Stop if UUID could not be retrieved

    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header, "Content-Type": "application/xml"}

    # Step 1: Fetch existing routes
    route_url = f"https://{dest_ip}:{port}/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.appliance.routes.configuration/property/network.routes.ip4"
    try:
        response = requests.get(route_url, headers=headers, verify=False)
        existing_xml = response.text
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch existing routes: {e}")
        return

    # Step 2: Modify the XML with new routes
    try:
        with open(filename, "r") as file:
            new_routes = file.readlines()
        new_entries = ''
        for line in new_routes:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                new_entries += f'''
                    &lt;listEntry&gt;
                        &lt;complexEntry&gt;
                            &lt;configurationProperties&gt;
                                &lt;configurationProperty key="network.routes.destination" type="com.scur.type.string" value="{parts[0]}"/&gt;
                                &lt;configurationProperty key="network.routes.gateway" type="com.scur.type.string" value="{parts[1]}"/&gt;
                                &lt;configurationProperty key="network.routes.device" type="com.scur.type.string" value="{dest_interface}"/&gt;
                                &lt;configurationProperty key="network.routes.description" type="com.scur.type.string" value="Imported Using Bluecoat to SkyHigh Web Gateway Migration Assistant Utility Version: {app_version}"/&gt;
                            &lt;/configurationProperties&gt;
                        &lt;/complexEntry&gt;&lt;description&gt;&lt;/description&gt;&lt;/listEntry&gt;'''
        if mode == "append":
            # Append XML       
            # Insert new entries before </content>
            modified_xml = existing_xml.replace('&lt;/content&gt;', f'{new_entries}&lt;/content&gt;')
        else:
            #Overwrite XML
            modified_xml = f'''<entry><content>&lt;list version=&quot;1.0.3.46&quot; mwg-version=&quot;12.2.2-46461&quot; classifier=&quot;Other&quot; systemList=&quot;false&quot; structuralList=&quot;false&quot; defaultRights=&quot;2&quot;&gt;
  &lt;description&gt;&lt;/description&gt;
  &lt;content&gt;{new_entries}
  &lt;/content&gt;&lt;/list&gt;</content></entry>
            '''
        # Save the modified XML locally for testing
        with open('new_routes.xml', 'w') as new_xml_file:
            new_xml_file.write(modified_xml)

        # Step 3: Upload the modified XML
        result = subprocess.run(
            ['curl', '-k', '-c', 'cookies.txt', '-u', f'{dest_user}:{dest_pass}', '-X', 'PUT', '-d', f'@{new_xml_file.name}', f'{route_url}', '-H', 'Content-Type: application/xml'],
            capture_output=True,
            text=True
        )
        curl_output = result.stderr

        messagebox.showerror("Error", f"Failed to update routes: {curl_output}")
        return
        
        # Commit changes
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:{port}/Konfigurator/REST/commit'
        subprocess.run(curl_command, shell=True)

        # Logout
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:{port}/Konfigurator/REST/logout'
        subprocess.run(curl_command, shell=True)

        messagebox.showinfo("Success", "Routes have been updated, committed, and logout was successful.\nPlease log in to the GUI and verify the changes.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to update routes: {e}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to update routes: {e}")
