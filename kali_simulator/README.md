# Kali Linux Simulator

A realistic Kali Linux operating system simulator inspired by Grey Hack. Features a virtual filesystem, shell commands, custom programming language, network simulation, multiple devices, and a full GUI desktop environment.

## 🖥️ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
sudo apt-get install python3-tk  # For GUI support on Linux

# Start with GUI (recommended) - Grey Hack style!
python main.py --gui

# Or start with CLI only
python main.py

# Show help
python main.py --help
```

## Project Structure

```
kali_simulator/
├── core/                   # Core simulation engine
│   ├── filesystem/         # Virtual filesystem implementation
│   ├── shell/              # Command interpreter and built-in commands
│   ├── network/            # Network simulation (devices, packets, protocols)
│   ├── devices/            # Device management and emulation
│   └── processes/          # Process management and scheduling
├── gui_engine.py           # Grey Hack style GUI engine ⭐ NEW!
├── languages/              # Custom programming language interpreter
├── utils/                  # Utility functions and helpers
├── data/                   # Default data and configurations
│   ├── users/              # User profiles and credentials
│   ├── programs/           # Pre-installed programs
│   └── configs/            # System configuration files
└── tests/                  # Unit and integration tests
    ├── unit/
    └── integration/
```

## ✨ Features

### 🖼️ GUI Desktop Environment (Grey Hack Style)
- **Single-Window Interface**: All virtual windows rendered inside one OS window
- **Draggable Windows**: Move terminal and file manager windows freely
- **CRT Effects**: Scanlines and retro monitor aesthetics
- **Terminal Widget**: Built-in terminal with color output and command history
- **File Manager Widget**: Browse files with icons and details
- **Taskbar**: System tray with clock and app launcher
- **Cyberpunk Theme**: Dark colors with hacker green accents

### 📁 Realistic Filesystem
- Full virtual filesystem with directories, files, permissions, and ownership
- Unix-style permission system (rwx for user/group/others)
- Standard Linux directory structure (/etc, /home, /tmp, /var, etc.)

### 💻 Shell Commands
- 60+ Kali Linux-like commands: `ls`, `cd`, `cat`, `grep`, `nmap`, `ifconfig`, etc.
- Simulated security tools: `metasploit`, `hashcat`, `wireshark`, `burpsuite`
- Pipe and redirection support
- Command history and tab completion (in CLI mode)

### 🐍 Custom Programming Language (KaliLang)
- Python-like syntax for writing scripts
- Variables, loops, conditionals, functions
- Built-in functions for file I/O and network operations
- Execute with `run script.kls` command

### 🌐 Network Simulation
- Virtual networks with multiple devices
- Packet transmission and protocol emulation
- Simulated IP addresses, ports, and services
- Network scanning and exploitation tools

### 🔐 Multi-user Support
- User accounts with different privilege levels
- Authentication system with password hashing
- Root/sudo privileges for administrative tasks

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Tkinter (usually included with Python)

### Setup

```bash
# Clone or navigate to the project
cd kali_simulator

# Install Python dependencies
pip install -r requirements.txt

# Install Tkinter (if not already installed)
# On Debian/Ubuntu:
sudo apt-get install python3-tk
# On Fedora:
sudo dnf install python3-tkinter
# On macOS:
brew install python-tk
# On Windows: Tkinter is included with Python installer
```

## 📖 Usage

### GUI Mode (Recommended)

```bash
python main.py --gui
```

This launches the Grey Hack-style desktop environment with:
- One main window containing all virtual components
- Draggable terminal window (pre-opened)
- Taskbar with clock and system tray
- CRT scanline effects for retro aesthetics
- Cyberpunk color scheme (dark bg, green text)

**Controls:**
- Drag windows by their title bar
- Click [X] button to close windows
- Type commands in the terminal widget
- All interaction happens inside the single application window

### CLI Mode

```bash
python main.py
```

Available commands:
- `help` - Show all available commands
- `ls -la` - List files with details
- `cd <dir>` - Change directory
- `cat <file>` - Display file contents
- `nmap <target>` - Simulated network scan
- `ifconfig` - Network interface information
- `run <script.kls>` - Execute KaliLang script
- `exit` - Exit simulator

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 📝 Custom Language Example

Create a file `scan.kls`:

```python
# KaliLang Script Example
print("Hello from KaliLang!")

var target = "192.168.1.1"
var ports = [22, 80, 443]

print("Scanning target:", target)
for port in ports:
    print("Port", port, "is open")

print("Scan complete!")
```

Run it in the simulator:
```bash
run scan.kls
```

## 🎮 Gameplay Ideas

Inspired by Grey Hack, you can:
- Explore the filesystem and discover secrets
- Use hacking tools to simulate network scans
- Write scripts to automate tasks
- Manage multiple devices and networks
- Complete challenges and missions (future feature)
- Customize your desktop environment

## 🛠️ Development

### Project Architecture

The simulator follows a modular architecture:

1. **Core Layer**: Filesystem, shell, network, devices, processes
2. **Language Layer**: KaliLang interpreter
3. **GUI Layer**: Tkinter-based desktop environment
4. **Data Layer**: User profiles, configurations, programs

### Adding New Features

```bash
# Add a new shell command
# Edit: core/shell/shell.py

# Add a new GUI component
# Create: gui/your_component.py

# Add network protocols
# Edit: core/network/protocols.py
```

## 📄 License

MIT License

## 🙏 Acknowledgments

- Inspired by [Grey Hack](https://store.steampowered.com/app/721650/Grey_Hack/)
- Kali Linux tools and aesthetics
- Python Tkinter for GUI components

---

**Enjoy hacking in the simulator!** 🐉💻
