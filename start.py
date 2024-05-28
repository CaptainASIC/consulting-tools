import subprocess
import sys

def check_dependencies():
    missing_modules = []
    
    # Read the requirements.txt file
    try:
        with open('requirements.txt', 'r') as f:
            required_modules = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        sys.exit("requirements.txt file not found. Exiting application.")
    
    # Check for missing modules
    for module in required_modules:
        try:
            __import__(module.split('==')[0])  # Handle version specified modules
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        # Attempt to install from the requirements.txt file
        try:
            print("Attempting to install missing modules from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Modules installed successfully from requirements.txt.")
        except subprocess.CalledProcessError:
            sys.exit("Failed to install dependencies from requirements.txt. Exiting application.")

def launch_app():
    # Assuming 'bc-to-swg.py' is in the same directory and your environment is set up correctly to run Python scripts
    subprocess.call([sys.executable, 'bc-to-swg.py'])

def main():
    check_dependencies()
    launch_app()

if __name__ == "__main__":
    main()
