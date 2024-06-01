from tkinter import messagebox
import paramiko
from datetime import datetime
import re

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
                service_type = "Telnet"

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
            converted_line = f"{service_type}," + re.sub(r'\s+', ',', line.strip())
            converted_lines.append(converted_line)

def migrate_proxy_services(source_ip, source_port, source_username, source_password):
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

        messagebox.showinfo("Success", f"Proxy services have been fetched, converted, and saved to {temp_proxy_services_file}.")
    
    except Exception as e:
        messagebox.showerror("Error", f"Failed to migrate proxy services: {e}")