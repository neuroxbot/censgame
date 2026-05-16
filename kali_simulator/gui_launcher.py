#!/usr/bin/env python3
"""
Kali Linux Simulator - GUI Launcher
Launch the simulator with graphical interface
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init
from core.filesystem.virtual_fs import VirtualFileSystem
from core.shell.shell import Shell
from gui.desktop import Desktop


def main():
    """Main entry point for the GUI launcher."""
    # Initialize colorama (for console fallback)
    init(autoreset=True)
    
    print("Starting Kali Linux Simulator GUI...")
    
    # Initialize filesystem
    fs = VirtualFileSystem()
    
    # Initialize shell
    shell = Shell(fs)
    
    # Setup demo environment
    setup_demo_environment(fs, shell)
    
    # Create and run desktop
    desktop = Desktop(fs, shell)
    desktop.run()


def setup_demo_environment(fs, shell):
    """Set up a demo environment with sample files and directories."""
    from core.filesystem.virtual_fs import VirtualFileSystem
    
    root_user = fs.users[0]
    
    # Create some interesting files in /home/user
    home_dir = fs.resolve_path('/home/user')
    
    # Create a readme file
    readme_content = """Welcome to Kali Linux Simulator!

This is a simulated Kali Linux environment inspired by Grey Hack.
You can use various commands to interact with the filesystem,
run simulated security tools, and write programs in our custom language.

Try these commands:
- ls -la          : List all files with details
- cat readme.txt  : Read this file
- nmap scanme.me  : Simulated network scan
- help            : Show all available commands

Have fun exploring!
"""
    fs.create_file('/home/user/readme.txt', readme_content, root_user)
    
    # Create a sample script
    script_content = """#!/bin/bash
# Sample bash script
echo "Hello from Kali Simulator!"
echo "This is a simulated script execution."
"""
    script_file = fs.create_file('/home/user/hello.sh', script_content, root_user)
    script_file.is_executable = True
    
    # Create a notes directory with some files
    fs.create_directory('/home/user/notes', root_user)
    fs.create_file('/home/user/notes/targets.txt', 
                   '192.168.1.1\n192.168.1.100\n10.0.0.1\n', root_user)
    fs.create_file('/home/user/notes/passwords.txt',
                   'admin:password123\nroot:toor\nuser:user\n', root_user)
    
    # Create a config file
    config_content = """# Network Configuration
INTERFACE=eth0
IP_ADDRESS=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS_SERVER=8.8.8.8
"""
    fs.create_file('/etc/network.conf', config_content, root_user)
    
    # Create some files in /tmp
    fs.create_file('/tmp/test.txt', 'Temporary test file content', root_user)
    
    # Create a Python-like script in the custom language
    kls_script = """# KaliLang Script Example
print("Hello from KaliLang!")

var target = "192.168.1.1"
var ports = [22, 80, 443]

print("Scanning target:", target)
for port in ports:
    print("Port", port, "is open")

print("Scan complete!")
"""
    fs.create_file('/home/user/scan.kls', kls_script, root_user)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        print("\nFalling back to CLI mode...")
        
        # Fallback to CLI
        from main import main as cli_main
        cli_main()
