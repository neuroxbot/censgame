"""
Unit tests for the virtual filesystem module.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.filesystem.virtual_fs import VirtualFileSystem, VirtualFile, VirtualDirectory
from core.filesystem.permissions import Permissions, User, Group, PermissionBits


class TestPermissions:
    """Tests for the Permissions class."""
    
    def test_default_permissions(self):
        """Test default permission values."""
        perms = Permissions()
        assert perms.owner_perms == PermissionBits.READ_WRITE
        assert perms.group_perms == PermissionBits.READ
        assert perms.other_perms == PermissionBits.READ
    
    def test_permission_to_octal(self):
        """Test converting permissions to octal notation."""
        perms = Permissions(
            owner_perms=PermissionBits.READ_WRITE_EXECUTE,
            group_perms=PermissionBits.READ_EXECUTE,
            other_perms=PermissionBits.READ_EXECUTE,
        )
        assert perms.to_octal() == "0755"
    
    def test_permission_from_octal(self):
        """Test creating permissions from octal notation."""
        perms = Permissions.from_octal("755")
        assert PermissionBits.READ in perms.owner_perms
        assert PermissionBits.WRITE in perms.owner_perms
        assert PermissionBits.EXECUTE in perms.owner_perms
        
        assert PermissionBits.READ in perms.group_perms
        assert PermissionBits.EXECUTE in perms.group_perms
        assert PermissionBits.WRITE not in perms.group_perms
        
        assert PermissionBits.READ in perms.other_perms
        assert PermissionBits.EXECUTE in perms.other_perms
    
    def test_permission_string_representation(self):
        """Test string representation of permissions."""
        perms = Permissions(
            owner_perms=PermissionBits.READ_WRITE_EXECUTE,
            group_perms=PermissionBits.READ_EXECUTE,
            other_perms=PermissionBits.READ_EXECUTE,
        )
        assert str(perms) == "rwxr-xr-x"
    
    def test_sticky_bit(self):
        """Test sticky bit in octal notation."""
        perms = Permissions(
            owner_perms=PermissionBits.READ_WRITE_EXECUTE,
            group_perms=PermissionBits.READ_WRITE_EXECUTE,
            other_perms=PermissionBits.READ_WRITE_EXECUTE,
            sticky_bit=True,
        )
        assert perms.to_octal() == "1777"


class TestUser:
    """Tests for the User class."""
    
    def test_create_root_user(self):
        """Test creating a root user."""
        root = User(uid=0, username='root', is_root=True)
        assert root.uid == 0
        assert root.username == 'root'
        assert root.is_root is True
    
    def test_create_normal_user(self):
        """Test creating a normal user."""
        user = User(uid=1000, username='john')
        assert user.uid == 1000
        assert user.username == 'john'
        assert user.is_root is False


class TestVirtualFile:
    """Tests for the VirtualFile class."""
    
    def test_create_file(self):
        """Test creating a virtual file."""
        file = VirtualFile(name='test.txt', content='Hello, World!')
        assert file.name == 'test.txt'
        assert file.content == 'Hello, World!'
        assert file.size == 13
    
    def test_file_read(self):
        """Test reading a file."""
        file = VirtualFile(name='test.txt', content='Test content')
        root = User(uid=0, username='root', is_root=True)
        content = file.read(root)
        assert content == 'Test content'
    
    def test_file_write(self):
        """Test writing to a file."""
        file = VirtualFile(name='test.txt', content='Original')
        root = User(uid=0, username='root', is_root=True)
        file.write('Modified', root)
        assert file.content == 'Modified'
    
    def test_file_append(self):
        """Test appending to a file."""
        file = VirtualFile(name='test.txt', content='Hello')
        root = User(uid=0, username='root', is_root=True)
        file.append(' World', root)
        assert file.content == 'Hello World'


class TestVirtualDirectory:
    """Tests for the VirtualDirectory class."""
    
    def test_create_directory(self):
        """Test creating a virtual directory."""
        dir = VirtualDirectory(name='test_dir')
        assert dir.name == 'test_dir'
        assert len(dir.entries) == 0
    
    def test_add_entry(self):
        """Test adding an entry to a directory."""
        dir = VirtualDirectory(name='parent')
        file = VirtualFile(name='child.txt', content='content')
        root = User(uid=0, username='root', is_root=True)
        
        dir.add_entry(file, root)
        assert 'child.txt' in dir.entries
        assert file.parent == dir
    
    def test_remove_entry(self):
        """Test removing an entry from a directory."""
        dir = VirtualDirectory(name='parent')
        file = VirtualFile(name='child.txt', content='content')
        root = User(uid=0, username='root', is_root=True)
        
        dir.add_entry(file, root)
        dir.remove_entry('child.txt', root)
        assert 'child.txt' not in dir.entries
    
    def test_list_entries(self):
        """Test listing directory entries."""
        dir = VirtualDirectory(name='test')
        root = User(uid=0, username='root', is_root=True)
        
        dir.add_entry(VirtualFile(name='file1.txt'), root)
        dir.add_entry(VirtualFile(name='file2.txt'), root)
        dir.add_entry(VirtualDirectory(name='subdir'), root)
        
        entries = dir.list_entries(root)
        assert len(entries) == 3
        assert 'file1.txt' in entries
        assert 'file2.txt' in entries
        assert 'subdir' in entries


class TestVirtualFileSystem:
    """Tests for the VirtualFileSystem class."""
    
    def test_create_filesystem(self):
        """Test creating a virtual filesystem."""
        fs = VirtualFileSystem()
        assert fs.root is not None
        assert fs.root.name == ''
    
    def test_standard_directories_exist(self):
        """Test that standard Linux directories are created."""
        fs = VirtualFileSystem()
        standard_dirs = ['bin', 'boot', 'dev', 'etc', 'home', 'tmp', 'usr', 'var']
        
        for dir_name in standard_dirs:
            assert dir_name in fs.root.entries, f"Directory {dir_name} should exist"
    
    def test_resolve_path_absolute(self):
        """Test resolving absolute paths."""
        fs = VirtualFileSystem()
        home_dir = fs.resolve_path('/home')
        assert home_dir.name == 'home'
    
    def test_resolve_path_relative(self):
        """Test resolving relative paths."""
        fs = VirtualFileSystem()
        current = fs.root
        home_dir = fs.resolve_path('home', current)
        assert home_dir.name == 'home'
    
    def test_create_file(self):
        """Test creating a file in the filesystem."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        file = fs.create_file('/tmp/test.txt', 'Test content', root)
        assert file.name == 'test.txt'
        assert file.content == 'Test content'
    
    def test_create_directory(self):
        """Test creating a directory in the filesystem."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        dir = fs.create_directory('/tmp/newdir', root)
        assert dir.name == 'newdir'
        
        # Verify it exists
        resolved = fs.resolve_path('/tmp/newdir')
        assert resolved == dir
    
    def test_create_directory_recursive(self):
        """Test creating nested directories."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        dir = fs.create_directory('/tmp/a/b/c', root, recursive=True)
        assert dir.name == 'c'
        
        # Verify all directories exist
        assert fs.resolve_path('/tmp/a')
        assert fs.resolve_path('/tmp/a/b')
        assert fs.resolve_path('/tmp/a/b/c')
    
    def test_delete_file(self):
        """Test deleting a file."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        fs.create_file('/tmp/test.txt', 'content', root)
        fs.delete('/tmp/test.txt', root)
        
        with pytest.raises(FileNotFoundError):
            fs.resolve_file('/tmp/test.txt')
    
    def test_move_file(self):
        """Test moving a file."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        fs.create_file('/tmp/source.txt', 'content', root)
        fs.move('/tmp/source.txt', '/tmp/dest.txt', root)
        
        # Verify source is gone
        with pytest.raises(FileNotFoundError):
            fs.resolve_file('/tmp/source.txt')
        
        # Verify destination exists
        dest = fs.resolve_file('/tmp/dest.txt')
        assert dest.content == 'content'
    
    def test_copy_file(self):
        """Test copying a file."""
        fs = VirtualFileSystem()
        root = fs.users[0]
        
        fs.create_file('/tmp/original.txt', 'original content', root)
        fs.copy('/tmp/original.txt', '/tmp/copy.txt', root)
        
        # Verify both exist
        original = fs.resolve_file('/tmp/original.txt')
        copy = fs.resolve_file('/tmp/copy.txt')
        
        assert original.content == 'original content'
        assert copy.content == 'original content'
    
    def test_user_authentication(self):
        """Test user authentication."""
        fs = VirtualFileSystem()
        
        # Root has no password
        root = fs.authenticate_user('root', '')
        assert root is not None
        assert root.is_root
        
        # Normal user
        user = fs.authenticate_user('user', 'hashed_password')
        assert user is not None
        assert user.username == 'user'
        
        # Failed authentication
        failed = fs.authenticate_user('user', 'wrong_password')
        assert failed is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
