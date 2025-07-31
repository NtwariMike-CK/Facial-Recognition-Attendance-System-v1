# local_recognition/run.py
import os
import subprocess
import sys

def run_command(command, shell=False):
    try:
        subprocess.check_call(command, shell=shell)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        sys.exit(1)

def main():
    print("Starting FRAS Local Recognition System...")

    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("Virtual environment not found. Creating one...")
        run_command([sys.executable, "-m", "venv", "venv"])

    # Activate virtual environment
    print("Activating virtual environment...")
    if os.name == "nt":
        activate_script = ".\\venv\\Scripts\\activate"
        pip_exe = ".\\venv\\Scripts\\pip.exe"
        python_exe = ".\\venv\\Scripts\\python.exe"
    else:
        activate_script = "./venv/bin/activate"
        pip_exe = "./venv/bin/pip"
        python_exe = "./venv/bin/python"

    # Install requirements if not installed
    installed_marker = os.path.join("venv", "installed")
    if not os.path.exists(installed_marker):
        print("Installing requirements...")
        run_command([pip_exe, "install", "-r", "requirements.txt"])
        open(installed_marker, "w").close()

    # Check for face landmarks model
    model_file = "shape_predictor_68_face_landmarks.dat"
    if not os.path.exists(model_file):
        print("WARNING: Face landmarks model not found!")
        print("Please download from:")
        print("http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        print(f"Extract and place in this directory as '{model_file}'")
        input("Press Enter to continue anyway or Ctrl+C to exit...")

    # Run the application
    print("Starting application...")
    run_command([python_exe, "main.py"])

if __name__ == "__main__":
    main()
