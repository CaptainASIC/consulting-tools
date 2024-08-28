import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from base64 import b64encode
import csv
from swgAPI import get_appliance_uuid, force_api_logout

def mass_deploy_snmp(dest_ip, dest_port, dest_user, dest_pass):
    def deploy():
        snmpd_conf_file = snmpd_conf_entry.get()
        assets_file = assets_entry.get()

        if not snmpd_conf_file or not assets_file:
            messagebox.showerror("Error", "Please select both SNMP configuration file and assets file.")
            return

        if messagebox.askyesno("Confirm", "Are you ready to attempt mass deployment?"):
            try:
                with open(snmpd_conf_file, 'r') as f:
                    snmpd_conf_content = f.read()

                with open(assets_file, 'r') as f:
                    csv_reader = csv.reader(f)
                    next(csv_reader)  # Skip header row
                    assets = [row[0] for row in csv_reader]  # Assuming IP is in the first column

                for asset_ip in assets:
                    uuid = get_appliance_uuid(asset_ip, dest_user, dest_pass, dest_port)
                    if not uuid:
                        messagebox.showerror("Error", f"Failed to get UUID for {asset_ip}")
                        continue

                    url = f"https://{asset_ip}:{dest_port}/Konfigurator/REST/appliances/{uuid}/system/snmpd.conf"
                    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
                    headers = {"Authorization": auth_header, "Content-Type": "text/plain"}

                    response = requests.put(url, headers=headers, data=snmpd_conf_content, verify=False)
                    response.raise_for_status()

                    # Commit changes
                    commit_url = f"https://{asset_ip}:{dest_port}/Konfigurator/REST/commit"
                    requests.post(commit_url, headers=headers, verify=False)

                    # Logout
                    force_api_logout(asset_ip, dest_port)

                messagebox.showinfo("Success", "SNMP configuration has been deployed to all assets.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to deploy SNMP configuration: {str(e)}")

            popup.destroy()

    popup = tk.Toplevel()
    popup.title("Mass Deploy SNMP Configurations")
    popup.geometry("400x200")

    snmpd_conf_frame = tk.Frame(popup)
    snmpd_conf_frame.pack(pady=10)
    snmpd_conf_entry = tk.Entry(snmpd_conf_frame, width=30)
    snmpd_conf_entry.pack(side=tk.LEFT)
    snmpd_conf_button = tk.Button(snmpd_conf_frame, text="Browse", command=lambda: snmpd_conf_entry.insert(0, filedialog.askopenfilename(filetypes=[("Configuration files", "*.conf")])))
    snmpd_conf_button.pack(side=tk.LEFT)

    assets_frame = tk.Frame(popup)
    assets_frame.pack(pady=10)
    assets_entry = tk.Entry(assets_frame, width=30)
    assets_entry.pack(side=tk.LEFT)
    assets_button = tk.Button(assets_frame, text="Browse", command=lambda: assets_entry.insert(0, filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])))
    assets_button.pack(side=tk.LEFT)

    deploy_button = tk.Button(popup, text="Deploy", command=deploy)
    deploy_button.pack(pady=10)