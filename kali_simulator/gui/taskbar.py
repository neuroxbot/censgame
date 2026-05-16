#!/usr/bin/env python3
"""
Taskbar - Windows taskbar for managing open windows
Similar to Windows taskbar with window switching and system tray
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional


class Taskbar:
    """
    A taskbar component that displays open windows and provides system controls.
    Similar to the Windows taskbar or GNOME panel.
    """
    
    def __init__(self, parent, desktop):
        self.desktop = desktop
        self.parent = parent
        
        # Create taskbar frame
        self.taskbar_frame = tk.Frame(
            parent, 
            bg='#1a1a2e', 
            height=48,
            relief=tk.RAISED,
            bd=2
        )
        self.taskbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Start button
        self._create_start_button()
        
        # Window buttons container
        self.window_buttons_frame = tk.Frame(self.taskbar_frame, bg='#1a1a2e')
        self.window_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # System tray
        self._create_system_tray()
        
        # Track window buttons
        self.window_buttons: Dict[tk.Toplevel, tk.Button] = {}
    
    def _create_start_button(self):
        """Create the start/menu button."""
        self.start_button = tk.Button(
            self.taskbar_frame,
            text="🐉 Kali",
            bg='#007acc',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            width=10,
            command=self._show_start_menu
        )
        self.start_button.pack(side=tk.LEFT, padx=2, pady=4)
    
    def _create_system_tray(self):
        """Create the system tray area."""
        tray_frame = tk.Frame(self.taskbar_frame, bg='#1a1a2e')
        tray_frame.pack(side=tk.RIGHT, padx=10)
        
        # Clock
        self.clock_label = tk.Label(
            tray_frame,
            text="--:--",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 9),
            cursor='hand2'
        )
        self.clock_label.pack(side=tk.RIGHT, padx=10)
        self._update_clock()
        
        # Network icon (simulated)
        network_icon = tk.Label(
            tray_frame,
            text="🌐",
            bg='#1a1a2e',
            fg='#55ffff',
            font=('Arial', 12),
            cursor='hand2'
        )
        network_icon.pack(side=tk.RIGHT, padx=5)
        network_icon.bind('<Button-1>', self._show_network_info)
        
        # Volume icon (simulated)
        volume_icon = tk.Label(
            tray_frame,
            text="🔊",
            bg='#1a1a2e',
            fg='white',
            font=('Arial', 12),
            cursor='hand2'
        )
        volume_icon.pack(side=tk.RIGHT, padx=5)
        
        # User icon
        user_icon = tk.Label(
            tray_frame,
            text="👤",
            bg='#1a1a2e',
            fg='#feca57',
            font=('Arial', 12),
            cursor='hand2'
        )
        user_icon.pack(side=tk.RIGHT, padx=5)
        user_icon.bind('<Button-1>', self._show_user_menu)
    
    def _update_clock(self):
        """Update the clock display."""
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        self.clock_label.config(text=current_time)
        # Schedule next update in 1 second
        self.clock_label.after(1000, self._update_clock)
    
    def add_window(self, title: str, window: tk.Toplevel):
        """Add a window button to the taskbar."""
        # Create button for the window
        btn = tk.Button(
            self.window_buttons_frame,
            text=title,
            bg='#2d2d30',
            fg='white',
            font=('Arial', 9),
            relief=tk.FLAT,
            cursor='hand2',
            width=20,
            anchor='w',
            command=lambda: self._activate_window(window)
        )
        btn.pack(side=tk.LEFT, padx=2, pady=4)
        
        self.window_buttons[window] = btn
        self._update_window_buttons()
    
    def remove_window(self, window: tk.Toplevel):
        """Remove a window button from the taskbar."""
        if window in self.window_buttons:
            btn = self.window_buttons[window]
            btn.destroy()
            del self.window_buttons[window]
    
    def _update_window_buttons(self):
        """Update the appearance of window buttons based on active state."""
        for window, btn in self.window_buttons.items():
            if window == self.desktop.active_window:
                btn.config(bg='#007acc', relief=tk.SUNKEN)
            else:
                btn.config(bg='#2d2d30', relief=tk.FLAT)
    
    def _activate_window(self, window: tk.Toplevel):
        """Activate/focus a window."""
        # If window is already active, minimize it
        if window == self.desktop.active_window and window.winfo_viewable():
            window.iconify()
        else:
            # Deiconify if minimized
            if window.state() == 'iconic':
                window.deiconify()
            
            # Bring to front and focus
            window.lift()
            window.focus_force()
            
            # Update active window
            self.desktop.active_window = window
            self._update_window_buttons()
    
    def _show_start_menu(self):
        """Show the start menu."""
        menu = tk.Menu(self.parent, tearoff=0, bg='#2d2d30', fg='white')
        
        # Add menu items
        menu.add_command(label="📁 File Manager", command=self.desktop.open_file_manager)
        menu.add_command(label="💻 Terminal", command=self.desktop.open_terminal)
        menu.add_separator()
        menu.add_command(label="⚙️ Settings", command=self._show_settings)
        menu.add_command(label="ℹ️ About", command=self._show_about)
        menu.add_separator()
        menu.add_command(label="🚪 Exit", command=self.desktop.on_close)
        
        # Show menu at start button location
        try:
            x = self.start_button.winfo_rootx()
            y = self.start_button.winfo_rooty() - 150
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def _show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings panel coming soon!")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """Kali Linux Simulator v1.0.0
        
Inspired by Grey Hack - A hacking simulation game

Features:
• Realistic filesystem simulation
• 60+ shell commands
• Custom programming language
• Network simulation
• Multi-user support

Built with Python and Tkinter"""
        messagebox.showinfo("About Kali Simulator", about_text)
    
    def _show_network_info(self, event=None):
        """Show network information."""
        # Get simulated network info from filesystem
        try:
            config_node = self.desktop.fs.resolve_path('/etc/network.conf')
            if config_node and config_node.content:
                content = config_node.content.decode('utf-8', errors='ignore')
                messagebox.showinfo("Network Configuration", content)
            else:
                messagebox.showinfo("Network Status", 
                    "Interface: eth0\nIP: 192.168.1.100\nStatus: Connected")
        except:
            messagebox.showinfo("Network Status", 
                "Interface: eth0\nIP: 192.168.1.100\nStatus: Connected")
    
    def _show_user_menu(self, event=None):
        """Show user menu."""
        menu = tk.Menu(self.parent, tearoff=0, bg='#2d2d30', fg='white')
        menu.add_command(label="👤 Profile", command=self._show_profile)
        menu.add_command(label="🔒 Lock", command=self._lock_screen)
        menu.add_command(label="🚪 Logout", command=self._logout)
        
        try:
            x = self.parent.winfo_pointerx()
            y = self.parent.winfo_pointery() - 100
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    
    def _show_profile(self):
        """Show user profile."""
        user = self.desktop.fs.current_user
        profile_text = f"Username: {user.username}\nUID: {user.uid}\nHome: {user.home_dir}"
        messagebox.showinfo("User Profile", profile_text)
    
    def _lock_screen(self):
        """Simulate screen lock."""
        messagebox.showinfo("Screen Locked", "Screen locked. Enter password to unlock.")
    
    def _logout(self):
        """Simulate logout."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.desktop.on_close()


if __name__ == '__main__':
    # Test taskbar standalone
    root = tk.Tk()
    root.title("Taskbar Test")
    root.geometry("800x600")
    
    class MockDesktop:
        def __init__(self, root):
            self.root = root
            self.active_window = None
            self.windows = []
            self.fs = None
        
        def open_terminal(self):
            pass
        
        def open_file_manager(self):
            pass
        
        def on_close(self):
            self.root.destroy()
    
    from core.filesystem.virtual_fs import VirtualFileSystem
    desktop = MockDesktop(root)
    desktop.fs = VirtualFileSystem()
    
    taskbar = Taskbar(root, desktop)
    root.mainloop()
