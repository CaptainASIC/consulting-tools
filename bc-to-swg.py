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

app_version = "2.1.0 Beta"

# Modify the Python path to include the 'lib' directory
script_dir = Path(__file__).resolve().parent
lib_dir = script_dir / 'lib'
sys.path.append(str(lib_dir))

# Import modules from the 'lib' directory
from staticRoutes import fetch_static_routes, clean_and_save_routes, post_routes
from connectionTest import test_bc_connection, test_swg_connection

def load_config(entries, file_entry):
    config = configparser.ConfigParser()
    config.read('last.cfg')

    if 'SOURCE' in config:
        entries[0].delete(0, tk.END)
        entries[0].insert(0, config['SOURCE'].get('IP', ''))
        entries[1].delete(0, tk.END)
        entries[1].insert(0, config['SOURCE'].get('Username', ''))
        entries[2].delete(0, tk.END)
        entries[2].insert(0, config['SOURCE'].get('Password', ''))
        entries[8].delete(0, tk.END)
        entries[8].insert(0, config['SOURCE'].get('Port', '22'))

    if 'DESTINATION' in config:
        entries[3].delete(0, tk.END)
        entries[3].insert(0, config['DESTINATION'].get('IP', ''))
        entries[4].delete(0, tk.END)
        entries[4].insert(0, config['DESTINATION'].get('Username', ''))
        entries[5].delete(0, tk.END)
        entries[5].insert(0, config['DESTINATION'].get('Password', ''))
        entries[6].delete(0, tk.END)
        entries[6].insert(0, config['DESTINATION'].get('Interface', 'eth0'))
        entries[7].delete(0, tk.END)
        entries[7].insert(0, config['DESTINATION'].get('Local Static Routes File', 'staticroutes.csv'))
        entries[9].delete(0, tk.END)
        entries[9].insert(0, config['DESTINATION'].get('Port', '4712'))

    if 'FILE' in config:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, config['FILE'].get('Path', ''))

def build_xml_payload(filename,uuid):
    with open(filename, "r") as file:
        lines = file.readlines()

def migrate_action(src_type, entries, file_entry):
    if src_type.get() == "file":
        # Use the file directly
        post_routes(entries[3].get(), entries[4].get(), entries[5].get(), entries[6].get(), file_entry.get(), "overwrite", entries[9].get())

    else:
        # Fetch live data, clean it, and post
        source_file = f"{entries[0].get()}.csv"
        fetch_static_routes(entries[0].get(), entries[1].get(), entries[2].get(), source_file, entries[8].get())
        cleaned_file = clean_and_save_routes(source_file)
        post_routes(entries[3].get(), entries[4].get(), entries[5].get(), entries[6].get(), cleaned_file, "overwrite", entries[9].get())

def backup_config(dest_ip, dest_user, dest_pass):
    # Prompt user for the backup file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    default_filename = f"{dest_ip}-{timestamp}.backup"
    backup_file = filedialog.asksaveasfilename(defaultextension=".backup", filetypes=[("Backup files", "*.backup")], title="Save Backup File As", initialfile=default_filename)
    if not backup_file:
        return  # User canceled, do nothing
    
    try:
        curl_command = f'curl -k -b cookies.txt -u {dest_user}:{dest_pass} -X POST https://{dest_ip}:4712/Konfigurator/REST/backup -o {backup_file}'
        subprocess.run(curl_command, shell=True, check=True)
        messagebox.showinfo("Backup Config", f"Backup successful! Configuration saved as: {backup_file}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Backup Config", f"Backup failed: {e}")

def choose_file(entry):
    filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)

def show_about():
    # Display about information using the global app_version variable
    about_text = f"Bluecoat to SkyHigh Web Gateway\nMigration Assistant Utility\nVersion: {app_version}\nAuthor: Captain ASIC\n"
    about_window = tk.Toplevel()
    about_window.title("About")
    about_window.geometry("400x540")  # Adjust the size to fit content and spacing
    about_window.resizable(False, False)  # Make the window not resizable

    # Load and display the image at the top of the popup
    image_path = 'img/ASIC.png'
    img = tk.PhotoImage(file=image_path).subsample(3,3)
    img_label = tk.Label(about_window, image=img)
    img_label.image = img  # Keep a reference to prevent garbage collection
    img_label.pack()
    text_widget = tk.Text(about_window, height=4, wrap=tk.WORD, font=('Arial', 16), cursor="arrow", borderwidth=0, background=about_window.cget("background"))
    text_widget.tag_configure("label", justify='center')
    text_widget.tag_configure("link", foreground="blue", underline=1, justify='center')
    text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.configure(cursor="hand2"))
    text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.configure(cursor="arrow"))
    text_widget.tag_bind("link", "<Button-1>", lambda e: webbrowser.open_new("https://github.com/CaptainASIC/consulting-tools"))
    text_widget.insert(tk.END, about_text, "label")
    text_widget.insert(tk.END, "Source: ", "label")
    text_widget.insert(tk.END, "GitHub\n", "link")
    text_widget.configure(state="disabled", padx=10, pady=10)
    text_widget.pack(expand=True, fill='both')

def save_config(entries, file_entry):
    config = configparser.ConfigParser()
    
    config['SOURCE'] = {
        'IP': entries[0].get(),
        'Username': entries[1].get(),
        'Password': entries[2].get(),
        'Port': entries[8].get()
    }
    config['DESTINATION'] = {
        'IP': entries[3].get(),
        'Username': entries[4].get(),
        'Password': entries[5].get(),
        'Interface': entries[6].get(),
        'Port': entries[9].get()
    }
    config['FILE'] = {
        'Path': file_entry.get()
    }
    
    with open('last.cfg', 'w') as configfile:
        config.write(configfile)
    messagebox.showinfo("Configuration Saved", "Configuration has been saved to 'last.cfg'.")

def on_exit(entries, file_entry, root):
    save_config(entries, file_entry)
    root.quit()

def main():
    root = tk.Tk()
    root.title(f"Bluecoat to SkyHigh Migration Assistant Utility - Version {app_version}")
    root.geometry("1050x800")
    root.resizable(False, False)
    #icon_path = 'img/ASIC.png'
    #img_icon = tk.PhotoImage(file=icon_path)
    #root.iconphoto(False, img_icon)

    src_type = tk.StringVar(value="live")
    append_overwrite_type = tk.StringVar(value="append")
    field_frame = tk.Frame(root)
    field_frame.pack(fill='both', expand=True, padx=20, pady=20)

    entries = []

    # Source fields with border
    source_frame = tk.LabelFrame(field_frame, text="Bluecoat", padx=10, pady=10, bd=2, relief="groove")
    source_frame.grid(row=1, column=0, sticky="ew", pady=10, padx=20)

    source_labels = ["Source IP/FQDN:", "Source Username:", "Source Password:", "Source SSH Port:"]
    for i, label in enumerate(source_labels):
        label_widget = tk.Label(source_frame, text=label)
        label_widget.grid(row=i, column=0, sticky="e")
        entry = tk.Entry(source_frame, width=16)
        if "Password" in label:
            entry.config(show="*")
        if "Port" in label:
            entry.insert(0, "22")  # Default port for SSH
        entry.grid(row=i, column=1, sticky="ew")
        entries.append(entry)

    btn_test_bluecoat = tk.Button(field_frame, text="Test Connection\n to Bluecoat", command=lambda: test_bc_connection(entries[0].get(), entries[1].get(), entries[2].get(), entries[8].get()))
    btn_test_bluecoat.grid(row=1, column=1, padx=10, sticky="w")

    # Destination fields with border
    dest_frame = tk.LabelFrame(field_frame, text="SkyHigh Web Gateway", padx=10, pady=10, bd=2, relief="groove")
    dest_frame.grid(row=1, column=2, sticky="ew", pady=10, padx=20)

    dest_labels = ["Destination IP/FQDN:", "Destination Username:", "Destination Password:", "Destination REST Port (https):"]
    for i, label in enumerate(dest_labels):
        label_widget = tk.Label(dest_frame, text=label)
        label_widget.grid(row=i, column=0, sticky="e")
        entry = tk.Entry(dest_frame, width=16)
        if "Password" in label:
            entry.config(show="*")
        if "Port" in label:
            entry.insert(0, "4712")  # Default port for REST
        entry.grid(row=i, column=1, sticky="ew")
        entries.append(entry)

    btn_test_swg = tk.Button(field_frame, text="Test Connection\n to SWG", command=lambda: test_swg_connection(entries[3].get(), entries[4].get(), entries[5].get(), entries[9].get()))
    btn_test_swg.grid(row=1, column=3, padx=10, sticky="w")

    # Separator
    separator = ttk.Separator(field_frame, orient='horizontal')
    separator.grid(row=2, column=0, columnspan=5, sticky="ew", pady=10)

    # Static Routes
    staticroutes_frame = tk.LabelFrame(field_frame, text="Static Routes (IPv4 Only)", padx=10, pady=10, bd=2, relief="groove")
    staticroutes_frame.grid(row=3, column=0, sticky="ew", pady=10)

    # Live data and file data radio buttons
    live_radio = tk.Radiobutton(staticroutes_frame, text="Live Data", variable=src_type, value="live")
    live_radio.grid(row=0, column=0, sticky="w")
    file_radio = tk.Radiobutton(staticroutes_frame, text="File Data", variable=src_type, value="file")
    file_radio.grid(row=0, column=1, sticky="w", padx=10)

    # Destination interface field
    interface_label = tk.Label(staticroutes_frame, text="SWG Interface:")
    interface_label.grid(row=1, column=0, sticky="e")
    interface_entry = tk.Entry(staticroutes_frame)
    interface_entry.grid(row=1, column=1, sticky="ew")
    entries.append(interface_entry)
    entries[6].insert(0, "eth0")

    # File input field
    file_entry = tk.Entry(staticroutes_frame)
    file_entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
    browse_button = tk.Button(staticroutes_frame, text="Browse", command=lambda: choose_file(file_entry))
    browse_button.grid(row=2, column=2, padx=10)
    entries.append(file_entry)
    entries[7].insert(0, "staticroutes.csv")

    # Append or Overwrite radio buttons
    append_radio = tk.Radiobutton(staticroutes_frame, text="Append Routes", variable=append_overwrite_type, value="append")
    append_radio.grid(row=3, column=0, sticky="w")
    overwrite_radio = tk.Radiobutton(staticroutes_frame, text="Overwrite Routes", variable=append_overwrite_type, value="overwrite")
    overwrite_radio.grid(row=3, column=1, sticky="w", padx=10)

    # Migrate button
    def handle_migration():
        post_routes(entries[3].get(), entries[4].get(), entries[5].get(), entries[6].get(), file_entry.get(), append_overwrite_type.get(), entries[9].get())

    btn_migrate = tk.Button(staticroutes_frame, text="Migrate Static Routes", command=handle_migration)
    btn_migrate.grid(row=4, column=0, columnspan=3, pady=20)

    # Policy Lists Migration section
    policy_frame = tk.LabelFrame(field_frame, text="Policy Lists", padx=10, pady=10, bd=2, relief="groove")
    policy_frame.grid(row=3, column=2, sticky="ew", pady=10)

    # Policy Lists live and file data radio buttons
    policy_src_type = tk.StringVar(value="live")
    policy_live_radio = tk.Radiobutton(policy_frame, text="Live Data", variable=policy_src_type, value="live")
    policy_live_radio.grid(row=0, column=0, sticky="w")
    policy_file_radio = tk.Radiobutton(policy_frame, text="File Data", variable=policy_src_type, value="file")
    policy_file_radio.grid(row=0, column=1, sticky="w", padx=10)

    # Policy Lists file input field
    policy_file_entry = tk.Entry(policy_frame)
    policy_file_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
    policy_browse_button = tk.Button(policy_frame, text="Browse", command=lambda: choose_file(policy_file_entry))
    policy_browse_button.grid(row=1, column=2, padx=10)

    # Migrate Policy Lists button
    btn_migrate_policy_lists = tk.Button(policy_frame, text="Migrate Policy Lists", command=lambda: migrate_policy_lists(entries, policy_file_entry))
    btn_migrate_policy_lists.grid(row=2, column=0, columnspan=3, pady=20)

    # Proxy Services Migration section with border
    proxy_frame = tk.LabelFrame(field_frame, text="Everything Else", padx=10, pady=10, bd=2, relief="groove")
    proxy_frame.grid(row=4, column=0, sticky="ew", pady=10)
    
    # Backup Current Config button
    btn_backup_config = tk.Button(proxy_frame, text="Backup Current Config", command=lambda: backup_config(entries[3].get(), entries[4].get(), entries[5].get()))
    btn_backup_config.grid(row=0, column=0, padx=10, sticky="w")

    # Migrate Proxy Services button
    btn_migrate_proxy_services = tk.Button(proxy_frame, text="Migrate Proxy Services", command=lambda: migrate_proxy_services(entries, file_entry))
    btn_migrate_proxy_services.grid(row=1, column=0, pady=20)

    button_frame = tk.Frame(root)
    button_frame.pack(side='bottom', fill='x', padx=20, pady=20)

    btn_about = tk.Button(button_frame, text="About", command=show_about)
    btn_about.pack(side='left', anchor='sw')

    btn_exit = tk.Button(button_frame, text="Exit", command=lambda: on_exit(entries, file_entry, root))
    btn_exit.pack(side='right', anchor='se')

    load_config(entries, file_entry)

    root.mainloop()

if __name__ == "__main__":
    main()