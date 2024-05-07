import subprocess
import sys

def check_dependencies():
    required_modules = ["requests"]
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        # Attempt to install from a local .whl file
        try:
            print("Attempting to install missing modules from local source...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "req/requests-2.31.0-py3-none-any.whl"])
            print("Modules installed successfully from local source.")
        except subprocess.CalledProcessError:
            # If installation fails, prompt the user for manual installation or exit
            print("Failed to install from the local source.")
            install = input("Would you like to attempt to install the missing modules from PyPI? (y/n): ")
            if install.lower() == 'y':
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_modules)
                except subprocess.CalledProcessError:
                    sys.exit("Failed to install dependencies from PyPI. Exiting application.")
            else:
                sys.exit("Exiting: Cannot run the application without all dependencies.")

def launch_app():
    # Assuming 'bc-to-swg.py' is in the same directory and your environment is set up correctly to run Python scripts
    subprocess.call([sys.executable, 'bc-to-swg.py'])

def main():
    check_dependencies()
    launch_app()

if __name__ == "__main__":
    main()
