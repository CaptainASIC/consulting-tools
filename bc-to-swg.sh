#!/bin/bash

# Function to prompt for the Bluecoat Source
read_source() {
    read -p "Enter Bluecoat Source (IP or FQDN): " BLUECOAT_SOURCE
    read -p "Enter username for Bluecoat: " USERNAME
    read -s -p "Enter password for Bluecoat: " PASSWORD
    echo
}

# Function to prompt for the SWG IP
read_destination() {
    read -p "Enter Destination SWG IP: " SWG_IP
    read -p "Enter username for SWG: " SWG_USER
    read -s -p "Enter password for SWG: " SWG_PASS
    echo
}

# Prompt for the Bluecoat source and username
read_source

# Execute SSH command to fetch static routes
TEMP_FILE="${BLUECOAT_SOURCE}_static_routes.csv"

echo "Connecting to $BLUECOAT_SOURCE via SSH..."
echo "Please enter your SSH password when prompted."

# Using built-in SSH to connect and execute the command
output=$(ssh -o StrictHostKeyChecking=no "$USERNAME@$BLUECOAT_SOURCE" "show static-routes")

# Check if SSH command was successful
if [[ $? -eq 0 ]]; then
    echo "$output" > "$TEMP_FILE"
    echo "Static routes have been saved to $TEMP_FILE."
else
    echo "An error occurred while retrieving the static routes."
    exit 1
fi

# Filter the output file to retain only lines after "Destination" and before "Internet 6:"
echo "Filtering the file to include only relevant routes..."
awk '/^Destination/{flag=1; next} /Internet 6:/{flag=0} flag' "$TEMP_FILE" > temp.csv && mv temp.csv "$TEMP_FILE"

# Check if the filtering was successful
if [[ $? -eq 0 ]]; then
    echo "Output filtered and saved to $TEMP_FILE."
else
    echo "An error occurred while filtering the routes."
    exit 1
fi

# Provide some feedback on the final file
ls -l "$TEMP_FILE"
cat "$TEMP_FILE"


# Prompt for the destination SWG IP and credentials
read_destination

# Prepare data and authorization for API calls
ENCODED_CREDS=$(echo -n "$SWG_USER:$SWG_PASS" | base64)
AUTH_HEADER="Authorization: Basic $ENCODED_CREDS"

# Fetch UUID for the SWG
UUID=$(curl -s -H "$AUTH_HEADER" "http://$SWG_IP:4712/Konfigurator/REST/appliances/" | grep -oP 'UUID>\K[^<]+')
echo "Fetched UUID: $UUID"

# Prepare to POST the new routes
ROUTE_URL="http://$SWG_IP:4712/Konfigurator/REST/appliances/$UUID/configuration/com.scur.engine.appliance.routes.configuration/property/network.routes.ip4"

# Read and format the routes from the Bluecoat static routes file
while IFS= read -r line; do
    IFS=' ' read -r DESTINATION SWG DEVICE <<< "$line"
    DESCRIPTION="migration tool import"
    XML_PAYLOAD="<entry><content><listEntry><complexEntry><configurationProperties><configurationProperty key='network.routes.destination' value='$DESTINATION'/><configurationProperty key='network.routes.SWG' value='$SWG'/><configurationProperty key='network.routes.device' value='$DEVICE'/><configurationProperty key='network.routes.description' value='$DESCRIPTION'/></configurationProperties></complexEntry></listEntry></content></entry>"

    # POST the new route
    curl -X POST -H "$AUTH_HEADER" -H "Content-Type: application/atom+xml" --data "$XML_PAYLOAD" "$ROUTE_URL"
done < "$TEMP_FILE"

# Commit changes
COMMIT_URL="http://$SWG_IP:4712/Konfigurator/REST/commit"
curl -X POST -H "$AUTH_HEADER" "$COMMIT_URL"

echo "Routes have been posted to the SWG."
