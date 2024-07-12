import paramiko
from tkinter import messagebox, simpledialog

def show_ha_stats(dest_ip, ssh_port, ssh_username, ssh_password):
    # Execute hastats command
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        
        # Run the command
        stdin, stdout, stderr = client.exec_command("hastats all")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        else:
            messagebox.showinfo("Success", command_output)
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()

def restart_mwg_service(dest_ip, ssh_port, ssh_username, ssh_password):
    # Attempt to restart the MWG Service via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        
        # Run the command
        stdin, stdout, stderr = client.exec_command("service mwg restart")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        else:
            messagebox.showinfo("Success", command_output)
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()

def restart_mwg_ui_service(dest_ip, ssh_port, ssh_username, ssh_password):
    # Attempt to restart the MWG-UI Service via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        
        # Run the command
        stdin, stdout, stderr = client.exec_command("service mwg-ui restart")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        else:
            messagebox.showinfo("Success", command_output)
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()

def reboot_appliance(dest_ip, ssh_port, ssh_username, ssh_password):
    # Attempt to reboot the appliance via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        
        # Run the reboot command
        stdin, stdout, stderr = client.exec_command("reboot")
        error_output = stderr.read().decode()
        
        if error_output:
            raise Exception(error_output)
        else:
            messagebox.showinfo("Success", "Reboot command has been sent.")
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()

def rollback(dest_ip, ssh_port, ssh_username, ssh_password):
    # Prompt the user for the number of configurations to revert
    num_revisions = simpledialog.askinteger("Config Rollback", "Enter the number of configurations to revert:", initialvalue=1)
    if num_revisions is None:
        return  # User canceled, do nothing

    # Attempt to rollback the configuration via SSH
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Connect to the host using username, password, and port
        client.connect(dest_ip, port=ssh_port, username=ssh_username, password=ssh_password, timeout=10)
        
        # Run the rollback command
        stdin, stdout, stderr = client.exec_command(f"/opt/mwg/bin/cfgrollback.sh {num_revisions}")
        error_output = stderr.read().decode()
        command_output = stdout.read().decode()
        if error_output:
            raise Exception(error_output)
        else:
            messagebox.showinfo("Success", f"Configuration has been reverted by {num_revisions} revision(s).")
    
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        # Close the connection
        client.close()