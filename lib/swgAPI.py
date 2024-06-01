from tkinter import messagebox, filedialog, ttk, Canvas
import subprocess
from datetime import datetime

def backup_config(dest_ip, dest_port, dest_user, dest_pass):
    # Prompt user for the backup file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    default_filename = f"{dest_ip}-{timestamp}.backup"
    backup_file = filedialog.asksaveasfilename(defaultextension=".backup", filetypes=[("Backup files", "*.backup")], title="Save Backup File As", initialfile=default_filename)
    if not backup_file:
        return  # User canceled, do nothing
    
    try:
        curl_command = f'curl -k -b cookies.txt -u {dest_user}:{dest_pass} -X POST https://{dest_ip}:{dest_port}/Konfigurator/REST/backup -o {backup_file}'
        subprocess.run(curl_command, shell=True, check=True)
        messagebox.showinfo("Backup Config", f"Backup successful! Configuration saved as: {backup_file}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Backup Config", f"Backup failed: {e}")

def force_api_logout(dest_ip, port):
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:{port}/Konfigurator/REST/logout'
        subprocess.run(curl_command, shell=True)

def migrate_policy_lists():
    messagebox.showinfo("Info", "Feature not yet implemented.")
