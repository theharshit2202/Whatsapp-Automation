import os
import subprocess
import sys
from pathlib import Path

def build_executable():
    """Build the WhatsApp automation executable using PyInstaller."""
    try:
        # Get the current directory
        current_dir = Path(__file__).parent.absolute()
        
        # Define paths
        script_path = current_dir / "Final_Chrome WA_AUTO.py"
        dist_path = current_dir
        output_name = "WA_Msg"
        
        # Verify the source file exists
        if not script_path.exists():
            print(f"Error: Source file not found at {script_path}")
            return False
            
        # Build the PyInstaller command
        cmd = [
            "pyinstaller",
            "--onefile",
            f"--name={output_name}",
            f"--distpath={dist_path}",
            str(script_path)
        ]
        
        print("Building executable...")
        print(f"Command: {' '.join(cmd)}")
        
        # Run PyInstaller
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\nBuild successful!")
            print(f"Executable created at: {dist_path / f'{output_name}.exe'}")
            return True
        else:
            print("\nBuild failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"\nError during build: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller installed successfully!")
    
    # Run the build
    success = build_executable()
    
    if not success:
        print("\nBuild failed. Please check the error messages above.")
        sys.exit(1) 