#!/usr/bin/env python3
"""
Desktop Environment - Main window managing all GUI components
Similar to Grey Hack's desktop interface
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, List
import os

from .terminal import TerminalWindow
from .file_manager import FileManagerWindow
from .taskbar import Taskbar


class Desktop:
    """
    Main desktop environment that manages windows, taskbar, and user interactions.
    Provides a Grey Hack-like experience with draggable windows and icons.
    """
    
    def __init__(self, filesystem, shell):
        self.fs = filesystem
        self.shell = shell
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("Kali Linux Simulator")
        self.root.geometry("1280x720")
        self.root.configure(bg='#1a1a2e')
        
        # Set Kali-like icon if available
        try:
            self.root.iconbitmap('data/icons/kali.ico')
        except:
            pass
        
        # Window management
        self.windows: List[tk.Toplevel] = []
        self.active_window: Optional[tk.Toplevel] = None
        self.window_count = 0
        
        # Desktop canvas for icons
        self.desktop_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.desktop_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create desktop icons
        self._create_desktop_icons()
        
        # Create taskbar
        self.taskbar = Taskbar(self.root, self)
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center window on screen
        self._center_window()
    
    def _center_window(self):
        """Center the main window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_desktop_icons(self):
        """Create desktop shortcut icons."""
        icons = [
            ("Terminal", self.open_terminal, '#00ff00'),
            ("File Manager", self.open_file_manager, '#4a90d9'),
            ("Browser", None, '#ff6b6b'),
            ("Text Editor", None, '#feca57'),
        ]
        
        row = 0
        col = 0
        for name, command, color in icons:
            icon_frame = tk.Frame(self.desktop_frame, bg='#1a1a2e', cursor='hand2')
            icon_frame.grid(row=row, column=col, padx=20, pady=20, sticky='nw')
            
            # Icon square
            icon_square = tk.Canvas(
                icon_frame, 
                width=48, 
                height=48, 
                bg=color,
                highlightthickness=0
            )
            icon_square.pack()
            
            # Icon label
            label = tk.Label(
                icon_frame,
                text=name,
                bg='#1a1a2e',
                fg='white',
                font=('Arial', 9),
                cursor='hand2'
            )
            label.pack(pady=(5, 0))
            
            # Bind click event
            if command:
                icon_frame.bind('<Button-1>', lambda e, cmd=command: cmd())
                label.bind('<Button-1>', lambda e, cmd=command: cmd())
            
            col += 1
            if col > 3:
                col = 0
                row += 1
    
    def open_terminal(self):
        """Open a new terminal window."""
        self.window_count += 1
        terminal = TerminalWindow(self.root, self.shell, self.fs, self.window_count)
        self.windows.append(terminal.window)
        self.taskbar.add_window(f"Terminal {self.window_count}", terminal.window)
    
    def open_file_manager(self):
        """Open a new file manager window."""
        self.window_count += 1
        fm = FileManagerWindow(self.root, self.fs, self.window_count)
        self.windows.append(fm.window)
        self.taskbar.add_window(f"File Manager {self.window_count}", fm.window)
    
    def close_window(self, window):
        """Close a window and remove it from taskbar."""
        if window in self.windows:
            self.windows.remove(window)
            self.taskbar.remove_window(window)
            window.destroy()
    
    def run(self):
        """Start the desktop environment main loop."""
        # Open initial terminal
        self.open_terminal()
        self.root.mainloop()
    
    def on_close(self):
        """Handle main window close event."""
        if tk.messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.root.destroy()


if __name__ == '__main__':
    # Test desktop standalone
    from core.filesystem.virtual_fs import VirtualFileSystem
    from core.shell.shell import Shell
    
    fs = VirtualFileSystem()
    shell = Shell(fs)
    
    desktop = Desktop(fs, shell)
    desktop.run()
