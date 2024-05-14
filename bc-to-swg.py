import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import requests
import webbrowser
from base64 import b64encode

# Define app version in a variable
app_version = "1.0.3"

def fetch_static_routes(source_ip, username, password, filename):
    # Attempt to fetch static routes via SSH
    try:
        command = f"ssh {username}@{source_ip} 'show static-routes'"
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, errors = proc.communicate()

        if proc.returncode != 0:
            raise Exception(errors)

        with open(filename, "w") as f:
            f.write(output)

        messagebox.showinfo("Success", f"Static routes have been saved to {filename}.")
        # Clean up the output and save it again
        clean_and_save_routes(filename)

    except Exception as e:
        messagebox.showerror("Error", str(e))

def clean_and_save_routes(filename):
    # Read the output and apply cleaning similar to awk script
    with open(filename, "r") as file:
        lines = file.readlines()

    start_cleaning = False
    cleaned_lines = []
    for line in lines:
        if "Internet6:" in line:
            break
        if start_cleaning:
            cleaned_lines.append(line)
        if "Destination" in line:
            start_cleaning = True

    with open(filename, "w") as file:
        file.writelines(cleaned_lines)

    messagebox.showinfo("Info", f"Cleaned static routes have been saved to {filename}.")

def post_routes(dest_ip, dest_user, dest_pass, filename):
    # Prepare the authorization and headers for HTTP request
    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header, "Content-Type": "application/atom+xml"}

    try:
        # Post routes
        with open(filename, "r") as file:
            lines = file.readlines()
        xml_payload = "<entry><content>Example</content></entry>"
        route_url = f"http://{dest_ip}:4712/Konfigurator/REST/appliances/UUID/configuration/some-endpoint"
        response = requests.post(route_url, headers=headers, data=xml_payload)
        response.raise_for_status()
        messagebox.showinfo("Success", "Routes have been posted to the SWG.")

        # Logout after posting
        logout_url = f"http://{dest_ip}:4712/Konfigurator/REST/appliances/UUID/logout"
        logout_response = requests.post(logout_url, headers=headers)
        logout_response.raise_for_status()
        messagebox.showinfo("Logout Successful", "Successfully logged out from the destination device.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to communicate with the destination device: {e}")

def migrate_action():
    if src_type.get() == "file":
        clean_and_save_routes(file_entry.get())
    else:
        fetch_static_routes(entries[0].get(), entries[1].get(), entries[2].get(), f"{entries[0].get()}.csv")
    post_routes(entries[6].get(), entries[7].get(), entries[8].get(), file_entry.get() if src_type.get() == "file" else f"{entries[0].get()}.csv")


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

def main():
    root = tk.Tk()
    root.title(f"Bluecoat to SkyHigh Web Gateway Migration Assistant Utility - Version {app_version}")
    root.geometry("640x480")
    root.resizable(False, False)

    # Frame for the fields
    field_frame = tk.Frame(root)
    field_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Radio button for live data
    src_type = tk.StringVar(value="live")
    live_radio = tk.Radiobutton(field_frame, text="Live Data", variable=src_type, value="live")
    live_radio.grid(row=0, column=0, sticky="w")

    # Labels and entries for source information
    source_labels = ["Source IP/FQDN:", "Source Username:", "Source Password:"]
    entries = []
    for i, label in enumerate(source_labels):
        label_widget = tk.Label(field_frame, text=label)
        label_widget.grid(row=i+1, column=0, sticky="e")
        entry = tk.Entry(field_frame)
        entry.grid(row=i+1, column=1, sticky="ew")
        entries.append(entry)

    # Labels and entries for destination information
    dest_labels = ["Destination SWG IP:", "Destination Username:", "Destination Password:"]
    for i, label in enumerate(dest_labels):
        label_widget = tk.Label(field_frame, text=label)
        label_widget.grid(row=i+1, column=2, sticky="e")
        entry = tk.Entry(field_frame)
        entry.grid(row=i+1, column=3, sticky="ew")
        entries.append(entry)

    # Radio button for file data and related fields
    file_radio = tk.Radiobutton(field_frame, text="File Data", variable=src_type, value="file")
    file_radio.grid(row=5, column=0, sticky="w", rowspan=2, pady=20)
    file_entry = tk.Entry(field_frame)
    file_entry.grid(row=5, column=1, sticky="ew", columnspan=2, rowspan=2,pady=20)
    browse_button = tk.Button(field_frame, text="Browse", command=lambda: choose_file(file_entry))
    browse_button.grid(row=5, column=3, pady=20)

    # Migrate button with conditional action based on source type
    def migrate_action():
        if src_type.get() == "file":
            # Directly use the file if selected, ensuring it's cleaned
            clean_and_save_routes(file_entry.get())
            post_routes(entries[6].get(), entries[7].get(), entries[8].get(), file_entry.get())
        else:
            # Fetch live data if that's selected
            fetch_static_routes(entries[0].get(), entries[1].get(), entries[2].get(), f"{entries[0].get()}.csv")

    btn_migrate = tk.Button(field_frame, text="Migrate Static Routes", command=migrate_action)
    btn_migrate.grid(row=7, column=0, columnspan=5, pady=20)

    # Frame for the buttons at the bottom
    button_frame = tk.Frame(root)
    button_frame.pack(side='bottom', fill='x', padx=20, pady=20)

    # About and Exit buttons using pack within the frame
    btn_about = tk.Button(button_frame, text="About", command=show_about)
    btn_about.pack(side='left', anchor='sw')

    btn_exit = tk.Button(button_frame, text="Exit", command=root.quit)
    btn_exit.pack(side='right', anchor='se')

    root.mainloop()

if __name__ == "__main__":
    main()
