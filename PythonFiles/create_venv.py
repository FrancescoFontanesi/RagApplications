import os
import venv
import json
from pathlib import Path
import subprocess
import sys

def create_notebook_venv(notebook_path):
    """
    Create and initialize a virtual environment for a Jupyter notebook.
    
    Args:
        notebook_path (str): Path to the Jupyter notebook
    """
    # Convert notebook path to Path object
    nb_path = Path(notebook_path)
    
    # Create venv name from notebook name
    venv_name = f".venv_{nb_path.stem}"
    venv_path = nb_path / venv_name
    
    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print(f"Creating virtual environment: {venv_path}")
        venv.create(venv_path, with_pip=True)
        
        # Get the python executable path in the new venv
        if os.name == 'nt':  # Windows
            python_exe = venv_path / 'Scripts' / 'python.exe'
        else:  # Unix/Linux/MacOS
            python_exe = venv_path / 'bin' / 'python'
            
        # Install ipykernel in the new environment
        subprocess.check_call([str(python_exe), '-m', 'pip', 'install', 'ipykernel'])
        
        # Create a kernel with the name of the notebook
        kernel_name = nb_path.stem
        subprocess.check_call([
            str(python_exe),
            '-m', 'ipykernel',
            'install',
            '--user',
            f'--name={kernel_name}',
            f'--display-name=Python ({kernel_name})'
        ])
    else:
        print(f"Virtual environment already exists at {venv_path}")
        return venv_path

# Example usage:
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_notebook.ipynb>")
        sys.exit(1)
        
    notebook_path = sys.argv[1]
    create_notebook_venv(notebook_path)