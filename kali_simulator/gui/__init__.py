#!/usr/bin/env python3
"""
Kali Linux Simulator - GUI Package
Provides a graphical user interface similar to Grey Hack
"""

from .desktop import Desktop
from .terminal import TerminalWindow
from .file_manager import FileManagerWindow
from .taskbar import Taskbar

__all__ = ['Desktop', 'TerminalWindow', 'FileManagerWindow', 'Taskbar']