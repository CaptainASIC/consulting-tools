#!/bin/bash

# Function to prompt for the Bluecoat Source
read_source() {
    read -p "Enter Bluecoat Source (IP or FQDN): " BLUECOAT_SOURCE
    read -p "Enter username: " USERNAME
}

# Prompt for the Bluecoat source and username
read_source

# Execute SSH command to fetch static routes
TEMP_FILE="${BLUECOAT_SOURCE}_static_routes.csv"

echo "Connecting to $BLUECOAT_SOURCE via SSH..."
echo "Please enter your SSH password when prompted."

# Using built-in SSH to connect and execute the command
ssh -o StrictHostKeyChecking=no "$USERNAME@$BLUECOAT_SOURCE" "show static-routes" > "$TEMP_FILE"

# Inform the user that the file was saved
if [[ $? -eq 0 ]]; then
    echo "Static routes have been saved to $TEMP_FILE."
else
    echo "An error occurred while retrieving the static routes."
fi
