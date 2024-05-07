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
        install = input("Would you like to install the missing modules? (y/n): ")
        if install.lower() == 'y':
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_modules)
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
