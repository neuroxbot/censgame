"""
File and directory permissions system for the virtual filesystem.
Implements Unix-like permission model with user, group, and others.
"""

from enum import IntFlag, auto
from dataclasses import dataclass
from typing import Optional


class PermissionBits(IntFlag):
    """Unix-style permission bits."""
    NONE = 0
    EXECUTE = auto()
    WRITE = auto()
    WRITE_EXECUTE = WRITE | EXECUTE
    READ = auto()
    READ_EXECUTE = READ | EXECUTE
    READ_WRITE = READ | WRITE
    READ_WRITE_EXECUTE = READ | WRITE | EXECUTE


@dataclass
class User:
    """Represents a user in the system."""
    uid: int
    username: str
    password_hash: Optional[str] = None
    is_root: bool = False
    
    def __repr__(self):
        return f"User(uid={self.uid}, username='{self.username}', root={self.is_root})"


@dataclass
class Group:
    """Represents a group in the system."""
    gid: int
    groupname: str
    members: list[int] = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []
    
    def add_member(self, uid: int):
        """Add a user to this group."""
        if uid not in self.members:
            self.members.append(uid)
    
    def remove_member(self, uid: int):
        """Remove a user from this group."""
        if uid in self.members:
            self.members.remove(uid)
    
    def __repr__(self):
        return f"Group(gid={self.gid}, groupname='{self.groupname}', members={self.members})"


@dataclass
class Permissions:
    """
    File/directory permissions following Unix model.
    
    Attributes:
        owner_perms: Permission bits for the owner
        group_perms: Permission bits for the group
        other_perms: Permission bits for everyone else
        owner_uid: UID of the owner
        group_gid: GID of the owning group
        sticky_bit: If set on directory, only file owner can delete files
        setuid_bit: Execute with owner's permissions
        setgid_bit: Execute with group's permissions or inherit group on directory
    """
    owner_perms: PermissionBits = PermissionBits.READ_WRITE
    group_perms: PermissionBits = PermissionBits.READ
    other_perms: PermissionBits = PermissionBits.READ
    owner_uid: int = 0
    group_gid: int = 0
    sticky_bit: bool = False
    setuid_bit: bool = False
    setgid_bit: bool = False
    
    def can_read(self, user: User, accessing_user: User) -> bool:
        """Check if accessing_user can read this file/directory."""
        if accessing_user.is_root:
            return True
        
        if accessing_user.uid == self.owner_uid:
            return bool(self.owner_perms & PermissionBits.READ)
        
        if accessing_user.uid in self.group_gid_members or self.group_gid in self._get_user_groups(accessing_user):
            return bool(self.group_perms & PermissionBits.READ)
        
        return bool(self.other_perms & PermissionBits.READ)
    
    def can_write(self, user: User, accessing_user: User) -> bool:
        """Check if accessing_user can write to this file/directory."""
        if accessing_user.is_root:
            return True
        
        if accessing_user.uid == self.owner_uid:
            return bool(self.owner_perms & PermissionBits.WRITE)
        
        if accessing_user.uid in self._get_group_members(self.group_gid):
            return bool(self.group_perms & PermissionBits.WRITE)
        
        return bool(self.other_perms & PermissionBits.WRITE)
    
    def can_execute(self, user: User, accessing_user: User) -> bool:
        """Check if accessing_user can execute this file/directory."""
        if accessing_user.is_root:
            return True
        
        if accessing_user.uid == self.owner_uid:
            return bool(self.owner_perms & PermissionBits.EXECUTE)
        
        if accessing_user.uid in self._get_group_members(self.group_gid):
            return bool(self.group_perms & PermissionBits.EXECUTE)
        
        return bool(self.other_perms & PermissionBits.EXECUTE)
    
    def _get_user_groups(self, user: User) -> list[int]:
        """Get list of group IDs a user belongs to."""
        # This would be implemented with a group database in full version
        return [self.group_gid]
    
    def _get_group_members(self, gid: int) -> list[int]:
        """Get list of user IDs in a group."""
        # This would be implemented with a group database in full version
        return []
    
    def to_octal(self) -> str:
        """Convert permissions to octal notation (e.g., '755')."""
        def perm_to_int(perm: PermissionBits) -> int:
            value = 0
            if PermissionBits.READ in perm:
                value += 4
            if PermissionBits.WRITE in perm:
                value += 2
            if PermissionBits.EXECUTE in perm:
                value += 1
            return value
        
        special = 0
        if self.sticky_bit:
            special += 1
        if self.setgid_bit:
            special += 2
        if self.setuid_bit:
            special += 4
        
        return f"{special}{perm_to_int(self.owner_perms)}{perm_to_int(self.group_perms)}{perm_to_int(self.other_perms)}"
    
    @classmethod
    def from_octal(cls, octal_str: str) -> 'Permissions':
        """Create Permissions from octal notation."""
        if len(octal_str) == 3:
            special = 0
            owner, group, other = octal_str
        elif len(octal_str) == 4:
            special = int(octal_str[0])
            owner, group, other = octal_str[1:]
        else:
            raise ValueError(f"Invalid octal string: {octal_str}")
        
        def int_to_perm(value: int) -> PermissionBits:
            perm = PermissionBits.NONE
            if value & 4:
                perm |= PermissionBits.READ
            if value & 2:
                perm |= PermissionBits.WRITE
            if value & 1:
                perm |= PermissionBits.EXECUTE
            return perm
        
        perms = cls(
            owner_perms=int_to_perm(int(owner)),
            group_perms=int_to_perm(int(group)),
            other_perms=int_to_perm(int(other)),
        )
        
        if special & 1:
            perms.sticky_bit = True
        if special & 2:
            perms.setgid_bit = True
        if special & 4:
            perms.setuid_bit = True
        
        return perms
    
    def __str__(self) -> str:
        """Return string representation like 'rwxr-xr-x'."""
        def perm_to_str(perm: PermissionBits) -> str:
            r = 'r' if PermissionBits.READ in perm else '-'
            w = 'w' if PermissionBits.WRITE in perm else '-'
            x = 'x' if PermissionBits.EXECUTE in perm else '-'
            return r + w + x
        
        result = perm_to_str(self.owner_perms)
        result += perm_to_str(self.group_perms)
        result += perm_to_str(self.other_perms)
        
        return result
