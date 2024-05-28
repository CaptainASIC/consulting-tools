import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import requests
import webbrowser
from base64 import b64encode
import configparser
import re
import paramiko

# Define app version in a variable
app_version = "1.0.6"

def load_config(entries, file_entry):
    config = configparser.ConfigParser()
    config.read('last.cfg')

    if 'SOURCE' in config:
        entries[0].insert(0, config['SOURCE'].get('IP', ''))
        entries[1].insert(0, config['SOURCE'].get('Username', ''))
        entries[2].insert(0, config['SOURCE'].get('Password', ''))

    if 'DESTINATION' in config:
        entries[3].insert(0, config['DESTINATION'].get('IP', ''))
        entries[4].insert(0, config['DESTINATION'].get('Username', ''))
        entries[5].insert(0, config['DESTINATION'].get('Password', ''))

    if 'FILE' in config:
        file_entry.insert(0, config['FILE'].get('Path', ''))

def get_appliance_uuid(dest_ip, dest_user, dest_pass):
    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header}
    url = f"https://{dest_ip}:4712/Konfigurator/REST/appliances"
    
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()

        # Log the raw XML for debugging
        print("Raw XML Response:", response.text)

        # Parsing XML to get UUID, assuming response is XML and contains <entry><id>UUID</id></entry>
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        uuid = root.find('.//entry/id').text

        # Display a popup with the UUID
        #messagebox.showinfo("UUID Retrieved", f"Current System UUID: {uuid}")

        return uuid
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch UUID: {e}")
        return None

def fetch_static_routes(source_ip, username, password, filename):
    # Attempt to fetch static routes via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username and password
        client.connect(source_ip, username=username, password=password, timeout=10)
        
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

    messagebox.showinfo("Info", f"Cleaned static routes have been saved to {cleaned_filename}.")
    return cleaned_filename

def get_network_routes(dest_ip, dest_user, dest_pass):
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass)
    if not uuid:
        messagebox.showerror("Error", "Failed to get UUID for GET test.")
        return

    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header}
    route_url = f"https://{dest_ip}:4712/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.appliance.routes.configuration/property/network.routes.ip4"

    try:
        response = requests.get(route_url, headers=headers, verify=False)
        response.raise_for_status()
        messagebox.showinfo("GET Test", f"Current Network Routes:\n{response.text}")
        
        # Save the XML to a file
        with open('current_network_routes.xml', 'w') as file:
            file.write(response.text)
        messagebox.showinfo("File Saved", "The current network routes have been saved to 'current_network_routes.xml'.")

    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch network routes: {e}")

def build_xml_payload(filename,uuid):
    with open(filename, "r") as file:
        lines = file.readlines()
    
def post_routes(dest_ip, dest_user, dest_pass, filename):
    uuid = get_appliance_uuid(dest_ip, dest_user, dest_pass)
    if not uuid:
        return  # Stop if UUID could not be retrieved

    auth_header = "Basic " + b64encode(f"{dest_user}:{dest_pass}".encode()).decode("utf-8")
    headers = {"Authorization": auth_header, "Content-Type": "application/xml"}

    # Step 1: Fetch existing routes
    route_url = f"https://{dest_ip}:4712/Konfigurator/REST/appliances/{uuid}/configuration/com.scur.engine.appliance.routes.configuration/property/network.routes.ip4"
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
                                &lt;configurationProperty key="network.routes.device" type="com.scur.type.string" value="eth0"/&gt;
                                &lt;configurationProperty key="network.routes.description" type="com.scur.type.string" value="Imported Using Bluecoat to SkyHigh Web Gateway Migration Assistant Utility Version: {app_version}"/&gt;
                            &lt;/configurationProperties&gt;
                        &lt;/complexEntry&gt;
                        &lt;description&gt;&lt;/description&gt;
                    &lt;/listEntry&gt;'''
                
        # Remove <link> tag using regex
        modified_xml = re.sub(r'<link[^>]*\/?>', '', existing_xml)
        # Insert new entries before </content></entry>
        modified_xml = existing_xml.replace('</content></entry>', f'&lt;list version=&quot;1.0.3.46&quot; mwg-version=&quot;12.2.2-46461&quot; classifier=&quot;Other&quot; systemList=&quot;false&quot; structuralList=&quot;false&quot; defaultRights=&quot;2&quot;&gt;{new_entries}&lt;/content&gt;&lt;/list&gt;</content></entry>')


        # Save the modified XML locally for testing
        with open('new_routes.xml', 'w') as new_xml_file:
            new_xml_file.write(modified_xml)

        # Step 3: Upload the modified XML
        #response = requests.put(route_url, headers=headers, data=modified_xml, verify=False)
        #response.raise_for_status()
        curl_command = f'curl -k -c cookies.txt -u {dest_user}:{dest_pass} -X PUT -d @{new_xml_file.name} {route_url} -H "Content-Type: application/xml"'
        subprocess.run(curl_command, shell=True)
        
        # Commit changes
        #commit_url = f"https://{dest_ip}:4712/Konfigurator/REST/commit"
        #requests.post(commit_url, headers=headers, verify=False).raise_for_status()
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:4712/Konfigurator/REST/commit'
        subprocess.run(curl_command, shell=True)

        # Logout
        #logout_url = f"https://{dest_ip}:4712/Konfigurator/REST/logout"
        #requests.post(logout_url, headers=headers, verify=False).raise_for_status()
        curl_command = f'curl -k -b cookies.txt -X POST https://{dest_ip}:4712/Konfigurator/REST/logout'
        subprocess.run(curl_command, shell=True)


        messagebox.showinfo("Success", "Routes have been updated, committed, and logout was successful.\nPlease log in to the GUI and verify the changes.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"Failed to update routes: {e}")


def migrate_action(src_type, entries, file_entry):
    if src_type.get() == "file":
        # Use the file directly
        post_routes(entries[3].get(), entries[4].get(), entries[5].get(), file_entry.get())

    else:
        # Fetch live data, clean it, and post
        source_file = f"{entries[0].get()}.csv"
        fetch_static_routes(entries[0].get(), entries[1].get(), entries[2].get(), source_file)
        cleaned_file = clean_and_save_routes(source_file)
        post_routes(entries[3].get(), entries[4].get(), entries[5].get(), cleaned_file)


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
    
    # Assuming entries are in the order: [source IP, source Username, source Password, dest IP, dest Username, dest Password]
    config['SOURCE'] = {
        'IP': entries[0].get(),
        'Username': entries[1].get(),
        'Password': entries[2].get()
    }
    config['DESTINATION'] = {
        'IP': entries[3].get(),
        'Username': entries[4].get(),
        'Password': entries[5].get()
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
    root.geometry("640x480")
    root.resizable(False, False)

    # Initialize the variable for choosing data source after creating the root window
    src_type = tk.StringVar(value="live")

    # Frame for the fields
    field_frame = tk.Frame(root)
    field_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Radio buttons for selecting data source
    live_radio = tk.Radiobutton(field_frame, text="Live Data", variable=src_type, value="live")
    live_radio.grid(row=0, column=0, sticky="w")

    # List to store entry widgets for source and destination information
    entries = []
    file_entry = tk.Entry(field_frame)

    # Labels and entries for source information
    source_labels = ["Source IP/FQDN:", "Source Username:", "Source Password:"]
    for i, label in enumerate(source_labels):
        label_widget = tk.Label(field_frame, text=label)
        label_widget.grid(row=i+1, column=0, sticky="e")
        entry = tk.Entry(field_frame)
        entry.grid(row=i+1, column=1, sticky="ew")
        entries.append(entry)  # Append each entry widget to the list

    # Labels and entries for destination information
    dest_labels = ["Destination SWG IP:", "Destination Username:", "Destination Password:"]
    for i, label in enumerate(dest_labels):
        label_widget = tk.Label(field_frame, text=label)
        label_widget.grid(row=i+1, column=2, sticky="e")
        entry = tk.Entry(field_frame)
        entry.grid(row=i+1, column=3, sticky="ew")
        entries.append(entry)  # Continue appending each entry widget

    # Radio button for file data and entry for file selection
    file_radio = tk.Radiobutton(field_frame, text="File Data", variable=src_type, value="file")
    file_radio.grid(row=5, column=0, sticky="w", pady=20)
    file_entry = tk.Entry(field_frame)
    file_entry.grid(row=5, column=1, sticky="ew", columnspan=2, pady=20)

    browse_button = tk.Button(field_frame, text="Browse", command=lambda: choose_file(file_entry))
    browse_button.grid(row=5, column=3)

    # Migrate button with conditional action based on source type
    btn_migrate = tk.Button(field_frame, text="Migrate Static Routes", command=lambda: migrate_action(src_type, entries, file_entry))
    btn_migrate.grid(row=6, column=0, columnspan=5, pady=20)

    # Add a button for performing the GET test
    #btn_get_test = tk.Button(field_frame, text="GET Test", command=lambda: get_network_routes(entries[3].get(), entries[4].get(), entries[5].get()))
    #btn_get_test.grid(row=7, column=3, pady=20)

    # Frame for the buttons at the bottom
    button_frame = tk.Frame(root)
    button_frame.pack(side='bottom', fill='x', padx=20, pady=20)

    btn_about = tk.Button(button_frame, text="About", command=show_about)
    btn_about.pack(side='left', anchor='sw')

    btn_exit = tk.Button(button_frame, text="Exit", command=lambda: on_exit(entries, file_entry, root))
    btn_exit.pack(side='right', anchor='se')

    # Load config if exists
    load_config(entries, file_entry)
    
    root.mainloop()

if __name__ == "__main__":
    main()