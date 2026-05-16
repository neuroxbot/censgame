#!/usr/bin/env python3
"""
Terminal Window - Graphical terminal emulator with Kali-style appearance
Provides a GUI wrapper around the shell system
"""

import tkinter as tk
from tkinter import ttk, font
from typing import Optional
import sys
from io import StringIO


class TerminalWindow:
    """
    A graphical terminal window that mimics the look and feel of a real Linux terminal.
    Supports command input, output display, and syntax highlighting.
    """
    
    def __init__(self, parent, shell, filesystem, window_id=1):
        self.shell = shell
        self.fs = filesystem
        self.window_id = window_id
        
        # Create top-level window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Terminal {window_id} - root@kali:~")
        self.window.geometry("800x600")
        self.window.configure(bg='#0c0c0c')
        
        # Terminal colors (Kali theme)
        self.colors = {
            'bg': '#0c0c0c',
            'fg': '#00ff00',
            'prompt': '#00ff00',
            'error': '#ff5555',
            'info': '#55ffff',
            'warning': '#feca57',
            'comment': '#6a9955',
            'string': '#ce9178',
            'keyword': '#569cd6',
        }
        
        # Configure window
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create terminal components
        self._create_terminal()
        
        # Command history
        self.command_history = []
        self.history_index = -1
        self.current_input = ""
        
        # Display welcome message
        self._display_welcome()
    
    def _create_terminal(self):
        """Create terminal text widget and scrollbar."""
        # Main frame
        main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Text widget for terminal output
        self.text_widget = tk.Text(
            main_frame,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            font=('Courier New', 11),
            wrap=tk.WORD,
            state='disabled',
            cursor='xterm',
            relief=tk.FLAT,
            highlightthickness=0,
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, command=self.text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.config(yscrollcommand=scrollbar.set)
        
        # Configure text tags for syntax highlighting
        self._configure_tags()
        
        # Bind keyboard events
        self.text_widget.bind('<Key>', self._on_key_press)
        self.text_widget.bind('<Return>', self._on_enter)
        self.text_widget.bind('<Up>', self._history_up)
        self.text_widget.bind('<Down>', self._history_down)
        self.text_widget.bind('<Control-c>', self._on_ctrl_c)
        self.text_widget.bind('<Control-l>', self._clear_terminal)
        
        # Track input position
        self.input_start = '1.0'
    
    def _configure_tags(self):
        """Configure text tags for syntax highlighting."""
        self.text_widget.tag_config('prompt', foreground=self.colors['prompt'])
        self.text_widget.tag_config('error', foreground=self.colors['error'])
        self.text_widget.tag_config('info', foreground=self.colors['info'])
        self.text_widget.tag_config('warning', foreground=self.colors['warning'])
        self.text_widget.tag_config('comment', foreground=self.colors['comment'])
        self.text_widget.tag_config('string', foreground=self.colors['string'])
        self.text_widget.tag_config('keyword', foreground=self.colors['keyword'])
    
    def _display_welcome(self):
        """Display welcome message and initial prompt."""
        welcome = """\x1b[31m  _  __                    _     _            
 | |/ /___  _   _ _ __   __| |   | | ___  __ _ 
 | ' // _ \\| | | | '_ \\ / _` |   | |/ _ \\/ _` |
 | . \\ (_) | |_| | | | | (_| |   | |  __/ (_| |
 |_|\\_\\___/ \\__,_|_| |_|\\__,_|   |_|\\___|\\__,_|
        
\x1b[33m        Kali Linux Simulator v1.0.0
\x1b[36m  Inspired by Grey Hack - A hacking simulation game

\x1b[0mType 'help' for available commands.
Type 'exit' to close terminal.

"""
        self._append_text(welcome)
        self._show_prompt()
    
    def _show_prompt(self):
        """Display the command prompt."""
        prompt = self.shell.get_prompt()
        self.input_start = self.text_widget.index('end-1c')
        self._append_text(prompt, 'prompt')
    
    def _append_text(self, text, tag=None):
        """Append text to the terminal with optional styling."""
        self.text_widget.config(state='normal')
        if tag:
            self.text_widget.insert('end', text, tag)
        else:
            self.text_widget.insert('end', text)
        self.text_widget.config(state='disabled')
        self.text_widget.see('end')
    
    def _get_current_command(self):
        """Get the current command being typed."""
        return self.text_widget.get(self.input_start, 'end-1c').strip()
    
    def _on_key_press(self, event):
        """Handle key press events."""
        # Prevent editing before input start
        if self.text_widget.compare('insert', '<', self.input_start):
            self.text_widget.mark_set('insert', 'end-1c')
    
    def _on_enter(self, event):
        """Handle Enter key press - execute command."""
        command = self._get_current_command()
        
        # Add to history
        if command.strip():
            self.command_history.append(command)
            self.history_index = len(self.command_history)
        
        # Execute command
        result = self.shell.execute_command(command)
        
        # Handle special commands
        if result.output == "__EXIT__":
            self.on_close()
            return 'break'
        
        if result.output == "__CLEAR__":
            self._clear_terminal(event)
            return 'break'
        
        # Display output
        if result.output:
            self._append_text('\n' + result.output)
        
        if result.error:
            self._append_text(f'\nError: {result.error}', 'error')
        
        # Show new prompt
        self._append_text('\n')
        self._show_prompt()
        
        return 'break'
    
    def _history_up(self, event):
        """Navigate up in command history."""
        if self.command_history and self.history_index > 0:
            if self.history_index == len(self.command_history):
                self.current_input = self._get_current_command()
            self.history_index -= 1
            self._replace_current_command(self.command_history[self.history_index])
        return 'break'
    
    def _history_down(self, event):
        """Navigate down in command history."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self._replace_current_command(self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self._replace_current_command(self.current_input)
        return 'break'
    
    def _replace_current_command(self, new_command):
        """Replace the current command line with new text."""
        self.text_widget.config(state='normal')
        self.text_widget.delete(self.input_start, 'end-1c')
        self.text_widget.insert(self.input_start, new_command)
        self.text_widget.config(state='disabled')
        self.text_widget.mark_set('insert', 'end-1c')
        self.text_widget.see('end')
    
    def _on_ctrl_c(self, event):
        """Handle Ctrl+C - interrupt current command."""
        self._append_text('\n^C\n')
        self._show_prompt()
        return 'break'
    
    def _clear_terminal(self, event=None):
        """Clear the terminal screen."""
        self.text_widget.config(state='normal')
        self.text_widget.delete('1.0', 'end')
        self.text_widget.config(state='disabled')
        self._show_prompt()
        return 'break'
    
    def on_close(self):
        """Handle window close event."""
        self.window.destroy()


if __name__ == '__main__':
    # Test terminal standalone
    from core.filesystem.virtual_fs import VirtualFileSystem
    from core.shell.shell import Shell
    
    root = tk.Tk()
    root.withdraw()
    
    fs = VirtualFileSystem()
    shell = Shell(fs)
    
    terminal = TerminalWindow(root, shell, fs, 1)
    root.mainloop()
