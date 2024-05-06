#!/bin/bash

VERSION="1.0.0"
BANNER="
██████╗ ██╗     ██╗   ██╗███████╗ ██████╗ ██████╗  █████╗ ████████╗                                                                                 
██╔══██╗██║     ██║   ██║██╔════╝██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝                                                                                 
██████╔╝██║     ██║   ██║█████╗  ██║     ██║   ██║███████║   ██║                                                                                    
██╔══██╗██║     ██║   ██║██╔══╝  ██║     ██║   ██║██╔══██║   ██║                                                                                    
██████╔╝███████╗╚██████╔╝███████╗╚██████╗╚██████╔╝██║  ██║   ██║                                                                                    
╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝                                                                                    
                                                                                                                                                    
████████╗ ██████╗                                                                                                                                   
╚══██╔══╝██╔═══██╗                                                                                                                                  
   ██║   ██║   ██║                                                                                                                                  
   ██║   ██║   ██║                                                                                                                                  
   ██║   ╚██████╔╝                                                                                                                                  
   ╚═╝    ╚═════╝                                                                                                                                   
                                                                                                                                                    
███████╗██╗  ██╗██╗   ██╗██╗  ██╗██╗ ██████╗ ██╗  ██╗    ██╗    ██╗███████╗██████╗      ██████╗  █████╗ ████████╗███████╗██╗    ██╗ █████╗ ██╗   ██╗
██╔════╝██║ ██╔╝╚██╗ ██╔╝██║  ██║██║██╔════╝ ██║  ██║    ██║    ██║██╔════╝██╔══██╗    ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝██║    ██║██╔══██╗╚██╗ ██╔╝
███████╗█████╔╝  ╚████╔╝ ███████║██║██║  ███╗███████║    ██║ █╗ ██║█████╗  ██████╔╝    ██║  ███╗███████║   ██║   █████╗  ██║ █╗ ██║███████║ ╚████╔╝ 
╚════██║██╔═██╗   ╚██╔╝  ██╔══██║██║██║   ██║██╔══██║    ██║███╗██║██╔══╝  ██╔══██╗    ██║   ██║██╔══██║   ██║   ██╔══╝  ██║███╗██║██╔══██║  ╚██╔╝  
███████║██║  ██╗   ██║   ██║  ██║██║╚██████╔╝██║  ██║    ╚███╔███╔╝███████╗██████╔╝    ╚██████╔╝██║  ██║   ██║   ███████╗╚███╔███╔╝██║  ██║   ██║   
╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═╝     ╚══╝╚══╝ ╚══════╝╚═════╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝   
                                                                                                                                                    
██╗   ██╗████████╗██╗██╗     ██╗████████╗██╗███████╗███████╗                                                                                        
██║   ██║╚══██╔══╝██║██║     ██║╚══██╔══╝██║██╔════╝██╔════╝                                                                                        
██║   ██║   ██║   ██║██║     ██║   ██║   ██║█████╗  ███████╗                                                                                        
██║   ██║   ██║   ██║██║     ██║   ██║   ██║██╔══╝  ╚════██║                                                                                        
╚██████╔╝   ██║   ██║███████╗██║   ██║   ██║███████╗███████║                                                                                        
 ╚═════╝    ╚═╝   ╚═╝╚══════╝╚═╝   ╚═╝   ╚═╝╚══════╝╚══════╝                                                                                        
"

# Display the banner and version
echo "$BANNER"
echo "Version: $VERSION"

# Function to display the menu
display_menu() {
    echo "Menu Options:"
    echo "1. Migrate Static Routes"
    echo "Q. Quit"
    echo "Please select an option:"
    read option
    case $option in
        1)
            migrate_routes
            ;;
        [Qq])
            echo "Exiting program."
            exit 0
            ;;
        *)
            echo "Invalid option, please try again."
            display_menu
            ;;
    esac
}

# Function to prompt for the Bluecoat Source
read_source() {
    echo "Enter details for Bluecoat source:"
    read -p "Enter Bluecoat Source (IP or FQDN): " BLUECOAT_SOURCE
    read -p "Enter username for Bluecoat: " USERNAME
    echo
}

# Function to prompt for the SWG IP
read_destination() {
    echo "Enter details for Destination SWG:"
    read -p "Enter Destination SWG IP: " SWG_IP
    read -p "Enter username for SWG: " SWG_USER
    read -s -p "Enter password for SWG: " SWG_PASS
    echo
}

# The main function to handle the migration of routes
migrate_routes() {
    read_source

    # Execute SSH command to fetch static routes
    TEMP_FILE="${BLUECOAT_SOURCE}_static_routes.csv"

    echo "Connecting to $BLUECOAT_SOURCE via SSH..."
    echo "Please enter your SSH password when prompted."

    # Using built-in SSH to connect and execute the command
    output=$(ssh -o StrictHostKeyChecking=no "$USERNAME@$BLUECOAT_SOURCE" "show static-routes")
    echo "$output" > "$TEMP_FILE"

    # Filter the output file to retain only lines after "Destination" and before "Internet 6:"
    echo "Filtering the file to include only relevant routes..."
    awk '/^Destination/{flag=1; next} /Internet 6:/{flag=0; next} flag' "$TEMP_FILE" > temp.csv && mv temp.csv "$TEMP_FILE"

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

    read_destination

    # Prepare data and authorization for API calls
    ENCODED_CREDS=$(echo -n "$SWG_USER:$SWG_PASS" | base64)
    AUTH_HEADER="Authorization: Basic $ENCODED_CREDS"

    # Fetch UUID for the SWG
    UUID=$(curl -s -H "$AUTH_HEADER" "http://$SWG_IP:4712/Konfigurator/REST/appliances/" | grep -oP 'UUID>\K[^<]+')
    echo "Fetched UUID: $UUID"

    # Prepare to POST the new routes
    ROUTE
