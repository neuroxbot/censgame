#!/usr/bin/env python3
"""
File Manager Window - Graphical file browser for the virtual filesystem
Similar to Windows Explorer or Nautilus in Linux
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Dict, List
import os


class FileManagerWindow:
    """
    A graphical file manager that allows browsing and managing files in the virtual filesystem.
    Provides a tree view of directories and file operations.
    """
    
    def __init__(self, parent, filesystem, window_id=1):
        self.fs = filesystem
        self.window_id = window_id
        self.current_path = '/'
        
        # Create top-level window
        self.window = tk.Toplevel(parent)
        self.window.title(f"File Manager {window_id}")
        self.window.geometry("900x600")
        self.window.configure(bg='#2d2d30')
        
        # Configure window
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create components
        self._create_ui()
        
        # Load initial directory
        self._load_directory('/')
    
    def _create_ui(self):
        """Create the file manager UI components."""
        # Main paned window
        paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Left panel - Directory tree
        left_frame = tk.Frame(paned, bg='#252526', width=250)
        paned.add(left_frame, weight=1)
        
        # Right panel - File list
        right_frame = tk.Frame(paned, bg='#1e1e1e')
        paned.add(right_frame, weight=3)
        
        # Create directory tree
        self._create_directory_tree(left_frame)
        
        # Create file list
        self._create_file_list(right_frame)
        
        # Create toolbar
        self._create_toolbar(right_frame)
        
        # Create status bar
        self._create_status_bar(self.window)
    
    def _create_directory_tree(self, parent):
        """Create the directory tree view."""
        # Label
        label = tk.Label(
            parent, 
            text="Directories", 
            bg='#252526', 
            fg='#cccccc',
            font=('Arial', 10, 'bold')
        )
        label.pack(pady=(10, 5), padx=10, anchor='w')
        
        # Tree widget
        self.tree = ttk.Treeview(parent, selectmode='browse')
        self.tree.heading('#0', text='Directory Structure', anchor='w')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Populate tree
        self._populate_tree()
        
        # Bind selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)
    
    def _populate_tree(self):
        """Populate the directory tree with filesystem structure."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add root
        root_id = self.tree.insert('', 'end', text='/', values=['/'], open=True)
        
        # Add main directories
        main_dirs = ['bin', 'etc', 'home', 'root', 'tmp', 'usr', 'var']
        for dir_name in main_dirs:
            dir_path = f'/{dir_name}'
            node_id = self.tree.insert(root_id, 'end', text=dir_name, values=[dir_path], open=False)
            
            # Add subdirectories (limited depth for performance)
            try:
                node = self.fs.resolve_path(dir_path)
                if node and node.is_directory:
                    self._add_subdirs(node_id, dir_path, 1)
            except:
                pass
    
    def _add_subdirs(self, parent_id, parent_path, depth):
        """Recursively add subdirectories to the tree."""
        if depth > 2:  # Limit depth
            return
        
        try:
            parent_node = self.fs.resolve_path(parent_path)
            if parent_node and parent_node.is_directory:
                for child_name, child_node in parent_node.children.items():
                    if child_node.is_directory:
                        child_path = f'{parent_path.rstrip("/")}/{child_name}'
                        child_id = self.tree.insert(
                            parent_id, 'end', text=child_name, 
                            values=[child_path], open=False
                        )
                        self._add_subdirs(child_id, child_path, depth + 1)
        except:
            pass
    
    def _create_file_list(self, parent):
        """Create the file list view."""
        # Frame for file list
        list_frame = tk.Frame(parent, bg='#1e1e1e')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with columns
        columns = ('Name', 'Type', 'Size', 'Permissions', 'Modified')
        self.file_list = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        self.file_list.heading('Name', text='Name')
        self.file_list.heading('Type', text='Type')
        self.file_list.heading('Size', text='Size')
        self.file_list.heading('Permissions', text='Permissions')
        self.file_list.heading('Modified', text='Modified')
        
        self.file_list.column('Name', width=300)
        self.file_list.column('Type', width=80)
        self.file_list.column('Size', width=80)
        self.file_list.column('Permissions', width=100)
        self.file_list.column('Modified', width=150)
        
        # Scrollbars
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        hsb = ttk.Scrollbar(list_frame, orient="horizontal", command=self.file_list.xview)
        self.file_list.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.file_list.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click
        self.file_list.bind('<Double-1>', self._on_file_double_click)
        
        # Bind context menu
        self.file_list.bind('<Button-3>', self._show_context_menu)
    
    def _create_toolbar(self, parent):
        """Create the toolbar with action buttons."""
        toolbar = tk.Frame(parent, bg='#333333', height=40)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        # Navigation buttons
        btn_back = tk.Button(
            toolbar, text="⬆ Up", command=self._go_up,
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_back.pack(side=tk.LEFT, padx=5)
        
        btn_refresh = tk.Button(
            toolbar, text="⟳ Refresh", command=lambda: self._load_directory(self.current_path),
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_refresh.pack(side=tk.LEFT, padx=5)
        
        btn_home = tk.Button(
            toolbar, text="🏠 Home", command=lambda: self._load_directory('/home/user'),
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_home.pack(side=tk.LEFT, padx=5)
        
        # Path entry
        path_label = tk.Label(toolbar, text="Path:", bg='#333333', fg='white')
        path_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.path_entry = tk.Entry(toolbar, bg='#252526', fg='white', insertbackground='white')
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.path_entry.bind('<Return>', self._on_path_enter)
        
        # Action buttons
        btn_new_folder = tk.Button(
            toolbar, text="+ Folder", command=self._new_folder,
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_new_folder.pack(side=tk.RIGHT, padx=5)
        
        btn_delete = tk.Button(
            toolbar, text="🗑 Delete", command=self._delete_selected,
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_delete.pack(side=tk.RIGHT, padx=5)
        
        btn_rename = tk.Button(
            toolbar, text="✏ Rename", command=self._rename_selected,
            bg='#333333', fg='white', relief=tk.FLAT,
            cursor='hand2'
        )
        btn_rename.pack(side=tk.RIGHT, padx=5)
    
    def _create_status_bar(self, parent):
        """Create the status bar."""
        self.status_bar = tk.Label(
            parent, text="Ready", bd=1, relief=tk.SUNKEN,
            anchor=tk.W, bg='#007acc', fg='white'
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _load_directory(self, path):
        """Load and display contents of a directory."""
        try:
            node = self.fs.resolve_path(path)
            if not node or not node.is_directory:
                messagebox.showerror("Error", f"Directory not found: {path}")
                return
            
            self.current_path = path
            
            # Update path entry
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            
            # Clear file list
            for item in self.file_list.get_children():
                self.file_list.delete(item)
            
            # Add files and directories
            if node.children:
                for name, child in sorted(node.children.items()):
                    file_type = "Folder" if child.is_directory else "File"
                    size = str(len(child.content)) if child.content else "0"
                    perms = child.permissions.to_string() if hasattr(child.permissions, 'to_string') else "rw-r--r--"
                    modified = child.modified.strftime('%Y-%m-%d %H:%M') if hasattr(child, 'modified') else '-'
                    
                    self.file_list.insert('', 'end', iid=name, values=(
                        name, file_type, size, perms, modified
                    ))
            
            # Update status
            count = len(node.children) if node.children else 0
            self.status_bar.config(text=f"{count} items in {path}")
            
            # Update window title
            self.window.title(f"File Manager {self.window_id} - {path}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _on_tree_select(self, event):
        """Handle directory tree selection."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            path = item['values'][0]
            self._load_directory(path)
    
    def _on_file_double_click(self, event):
        """Handle file/folder double-click."""
        selection = self.file_list.selection()
        if selection:
            item_name = selection[0]
            item_path = f"{self.current_path.rstrip('/')}/{item_name}"
            
            try:
                node = self.fs.resolve_path(item_path)
                if node and node.is_directory:
                    self._load_directory(item_path)
                else:
                    # Could open file editor here
                    self.status_bar.config(text=f"File: {item_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _on_path_enter(self, event):
        """Handle path entry submission."""
        path = self.path_entry.get().strip()
        self._load_directory(path)
    
    def _go_up(self):
        """Navigate to parent directory."""
        if self.current_path != '/':
            parent_path = os.path.dirname(self.current_path)
            self._load_directory(parent_path)
    
    def _new_folder(self):
        """Create a new folder in current directory."""
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            try:
                user = self.fs.users[0]  # Get root user
                path = f"{self.current_path.rstrip('/')}/{name}"
                self.fs.create_directory(path, user)
                self._load_directory(self.current_path)
                self.status_bar.config(text=f"Created folder: {name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _delete_selected(self):
        """Delete selected file/folder."""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showwarning("Warning", "No item selected")
            return
        
        item_name = selection[0]
        if messagebox.askyesno("Confirm Delete", f"Delete '{item_name}'?"):
            try:
                path = f"{self.current_path.rstrip('/')}/{item_name}"
                node = self.fs.resolve_path(path)
                if node:
                    parent = self.fs.resolve_path(self.current_path)
                    if parent and parent.is_directory:
                        del parent.children[item_name]
                        self._load_directory(self.current_path)
                        self.status_bar.config(text=f"Deleted: {item_name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _rename_selected(self):
        """Rename selected file/folder."""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showwarning("Warning", "No item selected")
            return
        
        item_name = selection[0]
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=item_name)
        if new_name and new_name != item_name:
            try:
                old_path = f"{self.current_path.rstrip('/')}/{item_name}"
                new_path = f"{self.current_path.rstrip('/')}/{new_name}"
                
                node = self.fs.resolve_path(old_path)
                if node:
                    # Simple rename by updating parent's children dict
                    parent = self.fs.resolve_path(self.current_path)
                    if parent and parent.is_directory:
                        node.name = new_name
                        parent.children[new_name] = node
                        del parent.children[item_name]
                        self._load_directory(self.current_path)
                        self.status_bar.config(text=f"Renamed: {item_name} → {new_name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="Open", command=lambda: self._on_file_double_click(event))
        menu.add_command(label="Rename", command=self._rename_selected)
        menu.add_separator()
        menu.add_command(label="Delete", command=self._delete_selected)
        menu.add_command(label="Properties", command=self._show_properties)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _show_properties(self):
        """Show properties of selected item."""
        selection = self.file_list.selection()
        if not selection:
            return
        
        item_name = selection[0]
        path = f"{self.current_path.rstrip('/')}/{item_name}"
        
        try:
            node = self.fs.resolve_path(path)
            if node:
                props = f"Name: {node.name}\n"
                props += f"Type: {'Directory' if node.is_directory else 'File'}\n"
                props += f"Path: {path}\n"
                if node.content:
                    props += f"Size: {len(node.content)} bytes\n"
                if hasattr(node, 'permissions'):
                    props += f"Permissions: {node.permissions}\n"
                if hasattr(node, 'owner'):
                    props += f"Owner: {node.owner.username}\n"
                
                messagebox.showinfo("Properties", props)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def on_close(self):
        """Handle window close event."""
        self.window.destroy()


if __name__ == '__main__':
    # Test file manager standalone
    from core.filesystem.virtual_fs import VirtualFileSystem
    
    root = tk.Tk()
    root.withdraw()
    
    fs = VirtualFileSystem()
    
    fm = FileManagerWindow(root, fs, 1)
    root.mainloop()
