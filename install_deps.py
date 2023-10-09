import os
import sys
import subprocess

def install_packages(packages):
    """Install packages using pip3."""
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)

def main():
    # List of common packages for both Windows and Mac
    common_packages = [
        "wxPython",
        "networkx",
        "matplotlib",
        "numpy", 
        "pydot",
    ]

    # Install common packages
    install_packages(common_packages)

    # Check for operating system specific dependencies
    if os.name == "nt":  # Windows
        # Add Windows-specific packages if any
        windows_packages = []
        install_packages(windows_packages)
    elif os.name == "posix":  # Mac and Linux
        # Add Mac-specific packages if any
        mac_packages = [
            "pyobjc-framework-Cocoa",
            "pyobjc-framework-Quartz"
        ]
        install_packages(mac_packages)

if __name__ == "__main__":
    main()
