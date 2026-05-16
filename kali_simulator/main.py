#!/usr/bin/env python3
"""
Kali Linux Simulator - Main Entry Point

A realistic Kali Linux operating system simulator inspired by Grey Hack.
Features a virtual filesystem, shell commands, custom programming language,
network simulation, and multiple devices.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init, Fore, Style
from core.filesystem.virtual_fs import VirtualFileSystem
from core.shell.shell import Shell


def check_gui_mode():
    """Check if GUI mode is requested via argument."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--gui', '-g']:
            return True
        if sys.argv[1] in ['--help', '-h']:
            print_help()
            sys.exit(0)
    return False


def print_help():
    """Print help message."""
    help_text = """
Kali Linux Simulator - Grey Hack Edition

Usage: python main.py [OPTIONS]

Options:
  --gui, -g     Launch in GUI mode (Grey Hack style interface)
  --help, -h    Show this help message
  (no args)     Launch in CLI mode (terminal interface)

Examples:
  python main.py           # Start in CLI mode
  python main.py --gui     # Start in GUI mode
"""
    print(help_text)


def print_banner():
    """Print the Kali Linux Simulator banner."""
    banner = r"""
  _  __                    _     _            
 | |/ /___  _   _ _ __   __| |   | | ___  __ _ 
 | ' // _ \| | | | '_ \ / _` |   | |/ _ \/ _` |
 | . \ (_) | |_| | | | | (_| |   | |  __/ (_| |
 |_|\_\___/ \__,_|_| |_|\__,_|   |_|\___|\__,_|
        
        Kali Linux Simulator v1.0.0
  Inspired by Grey Hack - A hacking simulation game

Type 'help' for available commands.
Type 'exit' to quit.
"""
    print(Fore.RED + banner.split('\n')[0])
    print(Fore.RED + banner.split('\n')[1])
    print(Fore.RED + banner.split('\n')[2])
    print(Fore.RED + banner.split('\n')[3])
    print(Fore.RED + banner.split('\n')[4])
    print(Style.RESET_ALL + banner.split('\n')[5])
    print(Fore.YELLOW + banner.split('\n')[6] + Style.RESET_ALL)
    print(Fore.CYAN + banner.split('\n')[7] + Style.RESET_ALL)
    print(banner.split('\n')[8])
    print(banner.split('\n')[9])
    print(banner.split('\n')[10])


def main():
    """Main entry point for the simulator."""
    # Check for GUI mode
    if check_gui_mode():
        launch_gui_mode()
        return
    
    # Initialize colorama
    init(autoreset=True)
    
    # Print banner
    print_banner()
    
    # Initialize filesystem
    fs = VirtualFileSystem()
    
    # Initialize shell
    shell = Shell(fs)
    
    # Create some sample files for demonstration
    setup_demo_environment(fs, shell)
    
    # Main loop
    running = True
    while running:
        try:
            # Get command from user
            prompt = shell.get_prompt()
            command = input(prompt)
            
            # Execute command
            result = shell.execute_command(command)
            
            # Handle special commands
            if result.output == "__EXIT__":
                running = False
                continue
            
            if result.output == "__CLEAR__":
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            # Display output
            if result.output:
                print(result.output)
            
            if result.error:
                print(f"{Fore.RED}Error: {result.error}{Style.RESET_ALL}", file=sys.stderr)
            
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit the simulator.")
        except EOFError:
            break
    
    print(f"\n{Fore.GREEN}Goodbye!{Style.RESET_ALL}")


def launch_gui_mode():
    """Launch the GUI mode."""
    try:
        from gui_engine import launch_gui
        from core.filesystem.virtual_fs import VirtualFileSystem
        from core.shell.shell import Shell
        
        # Initialize filesystem and shell
        fs = VirtualFileSystem()
        shell = Shell(fs)
        
        # Setup demo environment
        setup_demo_environment(fs, shell)
        
        # Launch GUI
        launch_gui(shell)
        
    except ImportError as e:
        print(f"Error: GUI module not available. Make sure tkinter is installed.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


def setup_demo_environment(fs: VirtualFileSystem, shell: Shell):
    """Set up a demo environment with sample files and directories."""
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
    main()
