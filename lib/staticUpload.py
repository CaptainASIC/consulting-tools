import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import paramiko
import os

def static_config_upload(dest_ip, ssh_port, ssh_username, ssh_password):
    config_options = {
        'Admin Auth Config': 'internal/cfg/com.scur.adminauthconfig.xml'
    }

    def upload_file():
        selected_config = config_var.get()
        file_path = file_entry.get()

        if not selected_config or not file_path:
            messagebox.showerror("Error", "Please select a config option and choose a file.")
            return

        if messagebox.askyesno("Confirm", f"Are you sure you want to replace {selected_config}?"):
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)

                sftp = client.open_sftp()
                sftp.chdir('current')
                remote_path = config_options[selected_config]
                sftp.put(file_path, remote_path)
                sftp.close()

                messagebox.showinfo("Success", f"{selected_config} has been uploaded successfully.")
                popup.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to upload file: {str(e)}")
            finally:
                client.close()

    def browse_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            file_entry.delete(0, tk.END)
            file_entry.insert(0, file_path)

    popup = tk.Toplevel()
    popup.title("Static Config Upload")
    popup.geometry("400x200")

    config_var = tk.StringVar(popup)
    config_var.set("Select Config")
    config_dropdown = ttk.Combobox(popup, textvariable=config_var, values=list(config_options.keys()))
    config_dropdown.pack(pady=10)

    file_frame = tk.Frame(popup)
    file_frame.pack(pady=10)
    file_entry = tk.Entry(file_frame, width=30)
    file_entry.pack(side=tk.LEFT)
    browse_button = tk.Button(file_frame, text="Browse", command=browse_file)
    browse_button.pack(side=tk.LEFT)

    upload_button = tk.Button(popup, text="Upload", command=upload_file)
    upload_button.pack(pady=10)