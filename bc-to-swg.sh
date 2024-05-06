#!/bin/bash
# Clear the screen
clear

# Version info
VERSION="1.0.0"
BUILD_DATE="May 2024"
BANNER_WIDTH=64

# Function to print centered text within a fixed width
print_centered() {
    local text="$1"
    local pad_width=$(( (BANNER_WIDTH - ${#text}) / 2 ))
    printf "%${pad_width}s%s%${pad_width}s" "" "$text" ""  # Center text within banner width
    if [ $(( (BANNER_WIDTH - ${#text}) % 2 )) -ne 0 ]; then
        printf " "  # Add an extra space if needed to maintain symmetry
    fi
}

# Banner
banner() {
    local dark_orange="\033[38;5;202m"
    local white="\033[97m"
    local reset_color="\033[0m"

    # Print top border
    echo -e "${white}+${reset_color}$(printf -- '-%.0s' $(seq 1 $((BANNER_WIDTH - 2))))${white}+${reset_color}"

    # Print lines
    echo -e "$(print_centered "")"
    echo -e "$(print_centered "${dark_orange}Bluecoat to SkyHigh Web Gateway${reset_color}")"
    echo -e "$(print_centered "${dark_orange}Migration Assistant Utility${reset_color}")"
    echo -e "$(print_centered "")"
    echo -e "$(print_centered "${dark_orange}Created by Captain ASIC${reset_color}")"
    echo -e "$(print_centered "${dark_orange}Version ${VERSION}, ${BUILD_DATE}${reset_color}")"
    echo -e "$(print_centered "")"

    # Print bottom border
    echo -e "${white}+${reset_color}$(printf -- '-%.0s' $(seq 1 $((BANNER_WIDTH - 2))))${white}+${reset_color}"
}

# Display the banner
banner

# Function to display the menu
display_menu() {
    echo -e "\nMenu Options:"
    echo "1. Migrate Static Routes"
    echo "Q. Quit"
    read -p "Please select an option: " option
    case "$option" in
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
    echo -e "\nEnter details for Bluecoat source:"
    read -p "Enter Bluecoat Source (IP or FQDN): " BLUECOAT_SOURCE
    read -p "Enter username for Bluecoat: " USERNAME
    echo
}

# Function to prompt for the SWG IP
read_destination() {
    echo -e "\nEnter details for Destination SWG:"
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

    echo -e "\nConnecting to $BLUECOAT_SOURCE via SSH..."
    echo "Please enter your SSH password when prompted."

    # Using built-in SSH to connect and execute the command
    output=$(ssh -o StrictHostKeyChecking=no "$USERNAME@$BLUECOAT_SOURCE" "show static-routes")
    echo "$output" > "$TEMP_FILE"

    # Filter the output file to retain only lines after "Destination" and before "Internet 6:"
    echo "Filtering the file to include only relevant routes..."
    awk '/^Destination/{flag=1; next} /Internet6:/{flag=0; next} flag' "$TEMP_FILE" > temp.csv && mv temp.csv "$TEMP_FILE"

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
}

# Start the program by showing the menu
display_menu
