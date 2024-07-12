# Bluecoat to SkyHigh Web Gateway Migration Assistant Utility

This utility helps in migrating from a Bluecoat appliance to a SkyHigh Web Gateway. It automates the fetching and posting of various configurations, simplifying the process and ensuring accuracy.

## Features

- **Fetch Static Routes**: Connect to a Bluecoat appliance via SSH to retrieve static routes.
- **Post Routes**: Automatically post retrieved routes to a SkyHigh Web Gateway.
- **Dependency Checking**: Ensures all necessary Python packages are installed before running the application.
- **User-Friendly Interface**: Simple GUI built with Tkinter for easy interaction.

## Requirements

- Python 3.x
- Tkinter (usually comes with Python)
- Requests
- Subprocess (included in standard Python library)
- Webbrowser (included in standard Python library)

## Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/CaptainASIC/consulting-tools.git
    ```
2. **Navigate to the project directory**:
    - Open the Project Directory in your File Browser
    - From the Command Prompt or Terminal run `cd consulting-tools`
3. **Start the Application**:
    - Double-click start.py
    - From the Command Prompt or Terminal run `python start.py`
    - Follow the on-screen prompts to enter appliance details and initiate the migration.

## Credits

This script was created by Captain ASIC.

## Version History

- 1.0.0: Initial release (May 2024)
- 1.0.1: Public Release (May 2024)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.