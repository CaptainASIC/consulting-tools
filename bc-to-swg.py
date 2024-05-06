import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import requests
from base64 import b64encode

def fetch_static_routes():
    bluecoat_source = simpledialog.askstring("Input", "Enter Bluecoat Source (IP or FQDN):")
    username = simpledialog.askstring("Input", "Enter username for Bluecoat:")
    password = simpledialog.askstring("Input", "Enter password for Bluecoat:", show='*')

    try:
        command = f"ssh {username}@{bluecoat_source} 'show static-routes'"
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, errors = proc.communicate()

        if proc.returncode != 0:
            raise Exception(errors)

        with open("hostname.csv", "w") as f:
            f.write(output)
        
        messagebox.showinfo("Success", "Static routes have been saved to hostname.csv.")
        post_routes()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def post_routes():
    swg_ip = simpledialog.askstring("Input", "Enter Destination SWG IP:")
    swg_user = simpledialog.askstring("Input", "Enter username for SWG:")
    swg_pass = simpledialog.askstring("Input", "Enter password for SWG:", show='*')

    auth_header = "Basic " + b64encode(f"{swg_user}:{swg_pass}".encode()).decode("utf-8")
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/atom+xml"
    }

    try:
        with open("hostname.csv", "r") as file:
            lines = file.readlines()
            # Assume data processing here as needed

        # Dummy payload and URL (update as necessary)
        xml_payload = "<entry><content>Example</content></entry>"
        route_url = f"http://{swg_ip}:4712/Konfigurator/REST/appliances/UUID/configuration/some-endpoint"

        response = requests.post(route_url, headers=headers, data=xml_payload)
        response.raise_for_status()

        messagebox.showinfo("Success", "Routes have been posted to the SWG.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def main():
    root = tk.Tk()
    root.title("Bluecoat to SkyHigh Web Gateway Migration Assistant Utility - Version 1.0.0")
    root.geometry("640x480")

    btn_migrate = tk.Button(root, text="Migrate Static Routes", command=fetch_static_routes)
    btn_migrate.pack(pady=190)

    btn_exit = tk.Button(root, text="Exit", command=root.quit)
    btn_exit.pack(side=tk.BOTTOM, padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
