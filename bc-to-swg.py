import tkinter as tk
from tkinter import messagebox
import subprocess
import requests
import webbrowser
import sys
from base64 import b64encode

# Define app version in a variable
app_version = "1.0.1"

def check_dependencies():
    required_modules = ["requests"]
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        response = messagebox.askyesno(
            "Missing Dependencies",
            f"The following modules are missing: {', '.join(missing_modules)}\nDo you want to install them now?"
        )
        if response:
            subprocess.call([sys.executable, "-m", "pip", "install"] + missing_modules)
        else:
            sys.exit("Exiting: Cannot run the application without all dependencies.")

def fetch_static_routes(source_ip, username, password, dest_ip, dest_user, dest_pass):
    # Attempt to fetch static routes via SSH
    try:
        command = f"ssh {username}@{source_ip} 'show static-routes'"
        proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, errors = proc.communicate()

        if proc.returncode != 0:
            raise Exception(errors)

        # Write the output to a CSV file named after the source IP or hostname
        filename = f"{source_ip}.csv"
        with open(filename, "w") as f:
            f.write(output)

        messagebox.showinfo("Success", f"Static routes have been saved to {filename}.")
        # Clean up the output and save it again
        clean_and_save_routes(filename)

        # Proceed to post routes to destination
        post_routes(dest_ip, dest_user, dest_pass)
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

def post_routes(swg_ip, swg_user, swg_pass):
    # Prepare the authorization and headers for HTTP request
    auth_header = "Basic " + b64encode(f"{swg_user}:{swg_pass}".encode()).decode("utf-8")
    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/atom+xml"
    }

    try:
        with open("hostname.csv", "r") as file:
            lines = file.readlines()

        xml_payload = "<entry><content>Example</content></entry>"
        route_url = f"http://{swg_ip}:4712/Konfigurator/REST/appliances/UUID/configuration/some-endpoint"
        response = requests.post(route_url, headers=headers, data=xml_payload)
        response.raise_for_status()

        messagebox.showinfo("Success", "Routes have been posted to the SWG.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_about():
    # Display about information using the global app_version variable
    about_text = f"Bluecoat to SkyHigh Web Gateway\nMigration Assistant Utility\nVersion: {app_version}\nAuthor: Captain ASIC\n"
    about_window = tk.Toplevel()
    about_window.title("About")
    about_window.geometry("400x480")  # Adjust the size to fit content and spacing
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
    check_dependencies()
    root = tk.Tk()
    root.title(f"Bluecoat to SkyHigh Web Gateway Migration Assistant Utility - Version {app_version}")
    root.geometry("640x480")
    root.resizable(False, False)

    # Frame for the fields
    field_frame = tk.Frame(root)
    field_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Labels and entries using grid in the field frame
    labels = ["Source IP/FQDN:", "Source Username:", "Source Password:", "Destination SWG IP:", "Destination Username:", "Destination Password:"]
    entries = []
    for i, label in enumerate(labels):
        row = i % 3
        column = 0 if i < 3 else 1
        label_widget = tk.Label(field_frame, text=label)
        label_widget.grid(row=row, column=column*2, sticky="e", padx=(20, 0))
        entry = tk.Entry(field_frame)
        entry.grid(row=row, column=column*2+1, sticky="w", padx=(0, 20))
        entries.append(entry)

    # Migrate button
    btn_migrate = tk.Button(field_frame, text="Migrate Static Routes", command=lambda: fetch_static_routes(*[e.get() for e in entries[:3]], *[e.get() for e in entries[3:]]))
    btn_migrate.grid(row=3, column=0, columnspan=4, pady=20)

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
