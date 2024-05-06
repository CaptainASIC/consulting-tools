#!/bin/bash

# Function to prompt for the Bluecoat Source, username, and password
read_credentials() {
    read -p "Enter Bluecoat Source (IP or FQDN): " BLUECOAT_SOURCE
    read -p "Enter username: " USERNAME
    read -s -p "Enter password: " PASSWORD
    echo
}

# Prompt for credentials
read_credentials

# Execute SSH command to fetch static routes
TEMP_FILE="${BLUECOAT_SOURCE}_static_routes.csv"

echo "Connecting to $BLUECOAT_SOURCE via SSH..."

# Requires sshpass to handle password input
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$USERNAME@$BLUECOAT_SOURCE" "show static-routes" > "$TEMP_FILE"

# Inform the user that the file was saved
if [[ $? -eq 0 ]]; then
    echo "Static routes have been saved to $TEMP_FILE."
else
    echo "An error occurred while retrieving the static routes."
fi
