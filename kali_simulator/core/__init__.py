"""
Kali Linux Simulator - Core Module

This module contains the core simulation engine including:
- Virtual filesystem
- Shell command interpreter
- Network simulation
- Device management
- Process scheduling
"""

from .filesystem.virtual_fs import VirtualFileSystem, VirtualFile, VirtualDirectory
from .shell.shell import Shell

# These will be implemented in future versions
# from .network.network import Network
# from .devices.device import Device
# from .processes.process import Process

__all__ = [
    'VirtualFileSystem',
    'VirtualFile',
    'VirtualDirectory',
    'Shell',
]
