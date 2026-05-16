"""
Virtual Filesystem implementation for Kali Linux Simulator.
Provides a Unix-like filesystem with directories, files, permissions, and metadata.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from .permissions import Permissions, User, Group, PermissionBits


@dataclass
class FileSystemObject:
    """Base class for all filesystem objects."""
    name: str
    parent: Optional['VirtualDirectory'] = None
    permissions: Permissions = field(default_factory=Permissions)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    owner_uid: int = 0
    group_gid: int = 0
    
    @property
    def path(self) -> str:
        """Get the full path of this object."""
        if self.parent is None:
            return '/'
        parent_path = self.parent.path
        if parent_path == '/':
            return f'/{self.name}'
        return f'{parent_path}/{self.name}'
    
    @property
    def size(self) -> int:
        """Get the size of this object in bytes."""
        return 0
    
    def update_access_time(self):
        """Update the last access time."""
        self.accessed_at = datetime.now()
    
    def update_modify_time(self):
        """Update the last modification time."""
        self.modified_at = datetime.now()


@dataclass
class VirtualFile(FileSystemObject):
    """Represents a file in the virtual filesystem."""
    content: str = ""
    is_executable: bool = False
    mime_type: str = "text/plain"
    
    @property
    def size(self) -> int:
        """Get the size of the file content in bytes."""
        return len(self.content.encode('utf-8'))
    
    def read(self, user: User) -> str:
        """Read the file content."""
        self.update_access_time()
        if not self.permissions.can_read(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        return self.content
    
    def write(self, content: str, user: User):
        """Write content to the file."""
        if not self.permissions.can_write(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        self.content = content
        self.update_modify_time()
    
    def append(self, content: str, user: User):
        """Append content to the file."""
        if not self.permissions.can_write(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        self.content += content
        self.update_modify_time()
    
    def execute(self, user: User, args: List[str] = None) -> str:
        """Execute the file if it's executable."""
        if not self.is_executable:
            raise PermissionError(f"Permission denied: {self.path} is not executable")
        
        if not self.permissions.can_execute(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        self.update_access_time()
        
        # For now, just return the content as if it were a script
        # In a full implementation, this would interpret the file based on its type
        return f"Executing {self.name}...\n{self.content}"


@dataclass
class VirtualDirectory(FileSystemObject):
    """Represents a directory in the virtual filesystem."""
    entries: Dict[str, FileSystemObject] = field(default_factory=dict)
    
    @property
    def size(self) -> int:
        """Get the total size of all entries in the directory."""
        return sum(entry.size for entry in self.entries.values())
    
    def add_entry(self, entry: FileSystemObject, user: User):
        """Add an entry to the directory."""
        if not self.permissions.can_write(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        if entry.name in self.entries:
            raise FileExistsError(f"Entry already exists: {entry.name}")
        
        entry.parent = self
        self.entries[entry.name] = entry
        self.update_modify_time()
    
    def remove_entry(self, name: str, user: User):
        """Remove an entry from the directory."""
        if not self.permissions.can_write(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        if name not in self.entries:
            raise FileNotFoundError(f"Entry not found: {name}")
        
        entry = self.entries[name]
        
        # Check sticky bit
        if self.permissions.sticky_bit and entry.owner_uid != user.uid and not user.is_root:
            raise PermissionError(f"Sticky bit set: cannot remove {name}")
        
        del self.entries[name]
        self.update_modify_time()
    
    def get_entry(self, name: str, user: User = None) -> FileSystemObject:
        """Get an entry from the directory."""
        if name not in self.entries:
            raise FileNotFoundError(f"Entry not found: {name}")
        
        entry = self.entries[name]
        
        if user and not self.permissions.can_read(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        self.update_access_time()
        return entry
    
    def list_entries(self, user: User, show_hidden: bool = False) -> List[str]:
        """List all entries in the directory."""
        if not self.permissions.can_read(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        self.update_access_time()
        
        entries = []
        for name, entry in self.entries.items():
            if show_hidden or not name.startswith('.'):
                entries.append(name)
        
        return sorted(entries)
    
    def list_entries_detailed(self, user: User, show_hidden: bool = False) -> List[Dict[str, Any]]:
        """List all entries with detailed information."""
        if not self.permissions.can_read(user, user):
            raise PermissionError(f"Permission denied: {self.path}")
        
        self.update_access_time()
        
        entries = []
        for name, entry in self.entries.items():
            if show_hidden or not name.startswith('.'):
                entries.append({
                    'name': name,
                    'type': 'directory' if isinstance(entry, VirtualDirectory) else 'file',
                    'size': entry.size,
                    'permissions': str(entry.permissions),
                    'owner_uid': entry.owner_uid,
                    'group_gid': entry.group_gid,
                    'modified_at': entry.modified_at,
                })
        
        return sorted(entries, key=lambda x: x['name'])


class VirtualFileSystem:
    """
    Main virtual filesystem class.
    Manages the root directory and provides filesystem operations.
    """
    
    def __init__(self):
        """Initialize the virtual filesystem with a root directory."""
        self.root = VirtualDirectory(name='', parent=None)
        self.root.permissions = Permissions(
            owner_perms=PermissionBits.READ_WRITE_EXECUTE,
            group_perms=PermissionBits.READ_EXECUTE,
            other_perms=PermissionBits.READ_EXECUTE,
        )
        self.users: Dict[int, User] = {}
        self.groups: Dict[int, Group] = {}
        self.current_users: Dict[str, User] = {}  # Session-based user tracking
        
        # Create default users
        self._create_default_users()
        
        # Create standard Linux directories
        self._create_standard_directories()
    
    def _create_default_users(self):
        """Create default system users."""
        root_user = User(uid=0, username='root', is_root=True)
        normal_user = User(uid=1000, username='user', password_hash='hashed_password')
        
        self.users[0] = root_user
        self.users[1000] = normal_user
        
        # Create default groups
        root_group = Group(gid=0, groupname='root', members=[0])
        user_group = Group(gid=1000, groupname='user', members=[1000])
        
        self.groups[0] = root_group
        self.groups[1000] = user_group
    
    def _create_standard_directories(self):
        """Create standard Linux directory structure."""
        root_user = self.users[0]
        
        standard_dirs = [
            'bin', 'boot', 'dev', 'etc', 'home', 'lib', 'media',
            'mnt', 'opt', 'proc', 'root', 'run', 'sbin', 'srv',
            'sys', 'tmp', 'usr', 'var'
        ]
        
        for dir_name in standard_dirs:
            dir_obj = VirtualDirectory(name=dir_name)
            dir_obj.owner_uid = 0
            dir_obj.group_gid = 0
            
            if dir_name in ['tmp']:
                dir_obj.permissions = Permissions(
                    owner_perms=PermissionBits.READ_WRITE_EXECUTE,
                    group_perms=PermissionBits.READ_WRITE_EXECUTE,
                    other_perms=PermissionBits.READ_WRITE_EXECUTE,
                    sticky_bit=True,
                )
            elif dir_name in ['root']:
                dir_obj.permissions = Permissions(
                    owner_perms=PermissionBits.READ_WRITE_EXECUTE,
                    group_perms=PermissionBits.NONE,
                    other_perms=PermissionBits.NONE,
                )
            
            self.root.add_entry(dir_obj, root_user)
        
        # Create /home/user directory
        home_dir = self.resolve_path('/home')
        user_dir = VirtualDirectory(name='user')
        user_dir.owner_uid = 1000
        user_dir.group_gid = 1000
        user_dir.permissions = Permissions(
            owner_perms=PermissionBits.READ_WRITE_EXECUTE,
            group_perms=PermissionBits.READ_EXECUTE,
            other_perms=PermissionBits.READ_EXECUTE,
        )
        home_dir.add_entry(user_dir, root_user)
    
    def resolve_path(self, path: str, current_dir: VirtualDirectory = None) -> VirtualDirectory:
        """Resolve a path to a directory object."""
        if current_dir is None:
            current_dir = self.root
        
        if path.startswith('/'):
            # Absolute path
            current = self.root
            path_parts = path[1:].split('/')
        else:
            # Relative path
            current = current_dir
            path_parts = path.split('/')
        
        for part in path_parts:
            if not part or part == '.':
                continue
            elif part == '..':
                if current.parent:
                    current = current.parent
            else:
                if not isinstance(current, VirtualDirectory):
                    raise NotADirectoryError(f"Not a directory: {current.path}")
                
                try:
                    current = current.get_entry(part)
                except FileNotFoundError:
                    raise FileNotFoundError(f"No such file or directory: {path}")
        
        return current
    
    def resolve_file(self, path: str, current_dir: VirtualDirectory = None) -> FileSystemObject:
        """Resolve a path to a file or directory object."""
        if path.endswith('/'):
            path = path[:-1]
        
        if '/' in path:
            dir_path = os.path.dirname(path)
            file_name = os.path.basename(path)
            
            if dir_path:
                parent_dir = self.resolve_path(dir_path, current_dir)
            else:
                parent_dir = current_dir if current_dir else self.root
            
            return parent_dir.get_entry(file_name)
        else:
            # Just a filename in current directory
            if current_dir is None:
                current_dir = self.root
            return current_dir.get_entry(path)
    
    def create_file(self, path: str, content: str = "", user: User = None) -> VirtualFile:
        """Create a new file at the specified path."""
        if user is None:
            user = self.users[0]  # Default to root
        
        dir_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        
        if not dir_path:
            dir_path = '/'
        
        parent_dir = self.resolve_path(dir_path)
        
        file_obj = VirtualFile(name=file_name, content=content)
        file_obj.owner_uid = user.uid
        file_obj.group_gid = user.uid  # Default to user's primary group
        
        parent_dir.add_entry(file_obj, user)
        return file_obj
    
    def create_directory(self, path: str, user: User = None, recursive: bool = False) -> VirtualDirectory:
        """Create a new directory at the specified path."""
        if user is None:
            user = self.users[0]  # Default to root
        
        if recursive:
            # Create parent directories if they don't exist
            parts = path.strip('/').split('/')
            current = self.root
            
            for part in parts:
                try:
                    entry = current.get_entry(part)
                    if not isinstance(entry, VirtualDirectory):
                        raise NotADirectoryError(f"{part} is not a directory")
                    current = entry
                except FileNotFoundError:
                    dir_obj = VirtualDirectory(name=part)
                    dir_obj.owner_uid = user.uid
                    dir_obj.group_gid = user.uid
                    current.add_entry(dir_obj, user)
                    current = dir_obj
            
            return current
        else:
            dir_path = os.path.dirname(path)
            dir_name = os.path.basename(path)
            
            if not dir_path:
                dir_path = '/'
            
            parent_dir = self.resolve_path(dir_path)
            
            dir_obj = VirtualDirectory(name=dir_name)
            dir_obj.owner_uid = user.uid
            dir_obj.group_gid = user.uid
            
            parent_dir.add_entry(dir_obj, user)
            return dir_obj
    
    def delete(self, path: str, user: User = None, recursive: bool = False) -> bool:
        """Delete a file or directory."""
        if user is None:
            user = self.users[0]
        
        obj = self.resolve_file(path)
        parent = obj.parent
        
        if isinstance(obj, VirtualDirectory) and obj.entries and not recursive:
            raise OSError(f"Directory not empty: {path}. Use recursive=True to delete non-empty directories.")
        
        parent.remove_entry(obj.name, user)
        return True
    
    def move(self, src_path: str, dst_path: str, user: User = None) -> bool:
        """Move a file or directory to a new location."""
        if user is None:
            user = self.users[0]
        
        src_obj = self.resolve_file(src_path)
        src_parent = src_obj.parent
        
        dst_dir = self.resolve_path(os.path.dirname(dst_path))
        dst_name = os.path.basename(dst_path)
        
        # Check if destination exists
        if dst_name in dst_dir.entries:
            raise FileExistsError(f"Destination already exists: {dst_path}")
        
        # Remove from source
        src_parent.remove_entry(src_obj.name, user)
        
        # Add to destination
        src_obj.name = dst_name
        dst_dir.add_entry(src_obj, user)
        
        return True
    
    def copy(self, src_path: str, dst_path: str, user: User = None) -> bool:
        """Copy a file or directory to a new location."""
        if user is None:
            user = self.users[0]
        
        src_obj = self.resolve_file(src_path)
        dst_dir = self.resolve_path(os.path.dirname(dst_path))
        dst_name = os.path.basename(dst_path)
        
        if isinstance(src_obj, VirtualFile):
            # Copy file
            new_file = VirtualFile(
                name=dst_name,
                content=src_obj.content,
                is_executable=src_obj.is_executable,
                mime_type=src_obj.mime_type,
            )
            new_file.owner_uid = user.uid
            new_file.permissions = Permissions(
                owner_perms=src_obj.permissions.owner_perms,
                group_perms=src_obj.permissions.group_perms,
                other_perms=src_obj.permissions.other_perms,
            )
            dst_dir.add_entry(new_file, user)
        elif isinstance(src_obj, VirtualDirectory):
            # Copy directory recursively
            new_dir = VirtualDirectory(name=dst_name)
            new_dir.owner_uid = user.uid
            dst_dir.add_entry(new_dir, user)
            
            for entry_name, entry in src_obj.entries.items():
                entry_src_path = f"{src_path}/{entry_name}"
                entry_dst_path = f"{dst_path}/{entry_name}"
                self.copy(entry_src_path, entry_dst_path, user)
        
        return True
    
    def get_user(self, uid: int) -> Optional[User]:
        """Get a user by UID."""
        return self.users.get(uid)
    
    def get_group(self, gid: int) -> Optional[Group]:
        """Get a group by GID."""
        return self.groups.get(gid)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        # In a real implementation, this would check against hashed passwords
        for user in self.users.values():
            if user.username == username:
                # Simple password check (in reality, use proper hashing)
                if user.password_hash == password or user.password_hash is None:
                    return user
        return None
