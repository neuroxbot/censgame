"""
Shell command interpreter for Kali Linux Simulator.
Provides a realistic terminal experience with common Linux commands.
"""

import shlex
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from ..filesystem.virtual_fs import VirtualFileSystem, VirtualFile, VirtualDirectory
from ..filesystem.permissions import User
from ..network.network_engine import get_network_manager


@dataclass
class CommandResult:
    """Result of a command execution."""
    output: str
    error: str = ""
    exit_code: int = 0


class Shell:
    """
    Interactive shell interpreter.
    Implements common Linux/Kali commands.
    """
    
    def __init__(self, filesystem: VirtualFileSystem):
        """Initialize the shell with a filesystem instance."""
        self.fs = filesystem
        self.current_user: User = filesystem.users[0]  # Default to root
        self.history: List[str] = []
        self.aliases: Dict[str, str] = {}
        
        # Sync with fs.cwd and get current directory
        self._update_current_dir_from_fs()
        
        # Register built-in commands
        self.commands: Dict[str, Callable] = {
            'help': self.cmd_help,
            'ls': self.cmd_ls,
            'cd': self.cmd_cd,
            'pwd': self.cmd_pwd,
            'cat': self.cmd_cat,
            'echo': self.cmd_echo,
            'mkdir': self.cmd_mkdir,
            'rm': self.cmd_rm,
            'cp': self.cmd_cp,
            'mv': self.cmd_mv,
            'touch': self.cmd_touch,
            'chmod': self.cmd_chmod,
            'chown': self.cmd_chown,
            'whoami': self.cmd_whoami,
            'su': self.cmd_su,
            'exit': self.cmd_exit,
            'clear': self.cmd_clear,
            'history': self.cmd_history,
            'alias': self.cmd_alias,
            'grep': self.cmd_grep,
            'head': self.cmd_head,
            'tail': self.cmd_tail,
            'wc': self.cmd_wc,
            'find': self.cmd_find,
            'locate': self.cmd_locate,
            'man': self.cmd_man,
            'file': self.cmd_file,
            'less': self.cmd_less,
            'more': self.cmd_more,
            'nano': self.cmd_nano,
            'vim': self.cmd_vim,
            'python3': self.cmd_python3,
            './': self.cmd_execute,
        }
        
        # Add some Kali-like tools (simulated)
        self.kali_tools = {
            'nmap': self.cmd_nmap,
            'ifconfig': self.cmd_ifconfig,
            'ip': self.cmd_ip,
            'ping': self.cmd_ping,
            'netstat': self.cmd_netstat,
            'ss': self.cmd_ss,
            'wget': self.cmd_wget,
            'curl': self.cmd_curl,
            'hashcat': self.cmd_hashcat,
            'john': self.cmd_john,
            'hydra': self.cmd_hydra,
            'metasploit': self.cmd_metasploit,
            'msfconsole': self.cmd_msfconsole,
            'sqlmap': self.cmd_sqlmap,
            'nikto': self.cmd_nikto,
            'burp': self.cmd_burp,
            'wireshark': self.cmd_wireshark,
            'tcpdump': self.cmd_tcpdump,
            'aircrack-ng': self.cmd_aircrack,
            'reaver': self.cmd_reaver,
            'wifite': self.cmd_wifite,
            'setoolkit': self.cmd_setoolkit,
            'beef': self.cmd_beef,
            'zap': self.cmd_zap,
        }
        
        self.commands.update(self.kali_tools)
    
    def _update_current_dir_from_fs(self):
        """Update shell's current_dir from filesystem's cwd."""
        try:
            self.current_dir = self.fs.get_current_directory()
        except:
            self.current_dir = self.fs.root
            self.fs.cwd = "/"
    
    def execute_command(self, command_line: str) -> CommandResult:
        """Execute a command line."""
        if not command_line.strip():
            return CommandResult(output="", exit_code=0)
        
        # Add to history
        self.history.append(command_line)
        if len(self.history) > 1000:
            self.history.pop(0)
        
        # Parse command
        try:
            parts = shlex.split(command_line)
        except ValueError as e:
            return CommandResult(error=f"Parse error: {e}", exit_code=1)
        
        if not parts:
            return CommandResult(output="", exit_code=0)
        
        cmd_name = parts[0]
        args = parts[1:]
        
        # Check for aliases
        if cmd_name in self.aliases:
            command_line = self.aliases[cmd_name] + ' ' + ' '.join(args)
            return self.execute_command(command_line)
        
        # Execute command
        if cmd_name in self.commands:
            try:
                result = self.commands[cmd_name](args)
                return result
            except Exception as e:
                return CommandResult(error=str(e), exit_code=1)
        else:
            return CommandResult(error=f"Command not found: {cmd_name}", exit_code=127)
    
    def get_prompt(self) -> str:
        """Get the current shell prompt."""
        if self.current_user.is_root:
            return f"\033[1;31mroot@kali\033[0m:\033[1;34m{self._get_short_pwd()}\033[0m# "
        else:
            return f"\033[1;32m{self.current_user.username}@kali\033[0m:\033[1;34m{self._get_short_pwd()}\033[0m$ "
    
    def _get_short_pwd(self) -> str:
        """Get shortened current directory path."""
        path = self.current_dir.path
        if path.startswith('/home/' + self.current_user.username):
            return '~' + path[len('/home/' + self.current_user.username):]
        return path
    
    def _resolve_path(self, path: str) -> str:
        """Resolve a path relative to current directory."""
        if path.startswith('/'):
            return path
        elif path.startswith('~'):
            return f"/home/{self.current_user.username}{path[1:]}"
        else:
            if self.current_dir.path == '/':
                return f'/{path}'
            return f'{self.current_dir.path}/{path}'
    
    # Command implementations
    
    def cmd_help(self, args: List[str]) -> CommandResult:
        """Show help information."""
        if args:
            cmd_name = args[0]
            if cmd_name in self.commands:
                cmd_func = self.commands[cmd_name]
                doc = cmd_func.__doc__ or "No documentation available."
                return CommandResult(output=f"{cmd_name}: {doc}")
            else:
                return CommandResult(error=f"Unknown command: {cmd_name}", exit_code=1)
        
        help_text = """Kali Linux Simulator - Available Commands

Filesystem:
  ls, cd, pwd, mkdir, rm, cp, mv, touch, cat, find, locate

Permissions:
  chmod, chown

Text Processing:
  echo, grep, head, tail, wc, less, more

Editors:
  nano, vim

System:
  whoami, su, exit, clear, history, alias, man, file

Network & Security Tools (Simulated):
  nmap, ifconfig, ip, ping, netstat, ss, wget, curl
  hashcat, john, hydra, metasploit, msfconsole, sqlmap
  nikto, burp, wireshark, tcpdump, aircrack-ng, wifite

Programming:
  python3

Type 'help <command>' for more information on a specific command.
"""
        return CommandResult(output=help_text)
    
    def cmd_ls(self, args: List[str]) -> CommandResult:
        """List directory contents."""
        show_hidden = '-a' in args or '--all' in args
        long_format = '-l' in args or '--long' in args
        
        # Find target directory
        target_path = None
        for arg in args:
            if not arg.startswith('-'):
                target_path = arg
                break
        
        if target_path:
            resolved_path = self._resolve_path(target_path)
            try:
                target_dir = self.fs.resolve_path(resolved_path, self.current_dir)
            except FileNotFoundError as e:
                return CommandResult(error=str(e), exit_code=2)
            except NotADirectoryError as e:
                # It's a file, show it
                try:
                    file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
                    return CommandResult(output=file_obj.name)
                except Exception as e:
                    return CommandResult(error=str(e), exit_code=2)
        else:
            target_dir = self.current_dir
        
        try:
            if long_format:
                entries = target_dir.list_entries_detailed(self.current_user, show_hidden)
                output_lines = []
                for entry in entries:
                    perms = entry['permissions']
                    size = entry['size']
                    name = entry['name']
                    if entry['type'] == 'directory':
                        name = f"\033[1;34m{name}\033[0m"
                    output_lines.append(f"{perms} {size:8d} {name}")
                return CommandResult(output='\n'.join(output_lines))
            else:
                entries = target_dir.list_entries(self.current_user, show_hidden)
                colored_entries = []
                for entry in entries:
                    try:
                        obj = target_dir.get_entry(entry)
                        if isinstance(obj, VirtualDirectory):
                            colored_entries.append(f"\033[1;34m{entry}\033[0m")
                        elif obj.is_executable:
                            colored_entries.append(f"\033[1;32m{entry}\033[0m")
                        else:
                            colored_entries.append(entry)
                    except:
                        colored_entries.append(entry)
                return CommandResult(output='  '.join(colored_entries))
        except PermissionError as e:
            return CommandResult(error=str(e), exit_code=13)
    
    def cmd_cd(self, args: List[str]) -> CommandResult:
        """Change current directory."""
        if not args:
            # Go to home directory
            home_path = f"/home/{self.current_user.username}"
            try:
                self.current_dir = self.fs.resolve_path(home_path)
                self.fs.cwd = self.current_dir.path
                return CommandResult(output="")
            except:
                self.current_dir = self.fs.root
                self.fs.cwd = "/"
                return CommandResult(output="")
        
        target_path = args[0]
        
        # Handle special cases
        if target_path == '-':
            # Previous directory (not implemented yet)
            return CommandResult(output="")
        
        resolved_path = self._resolve_path(target_path)
        
        try:
            new_dir = self.fs.resolve_path(resolved_path, self.current_dir)
            if not isinstance(new_dir, VirtualDirectory):
                return CommandResult(error=f"Not a directory: {target_path}", exit_code=1)
            self.current_dir = new_dir
            self.fs.cwd = new_dir.path  # Sync with fs.cwd
            return CommandResult(output="")
        except FileNotFoundError as e:
            return CommandResult(error=str(e), exit_code=1)
        except PermissionError as e:
            return CommandResult(error=str(e), exit_code=13)
    
    def cmd_pwd(self, args: List[str]) -> CommandResult:
        """Print working directory."""
        return CommandResult(output=self.current_dir.path)
    
    def cmd_cat(self, args: List[str]) -> CommandResult:
        """Concatenate and display file contents."""
        if not args:
            return CommandResult(error="Usage: cat <file>", exit_code=1)
        
        output_lines = []
        for file_path in args:
            resolved_path = self._resolve_path(file_path)
            try:
                file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
                if isinstance(file_obj, VirtualFile):
                    content = file_obj.read(self.current_user)
                    output_lines.append(content)
                else:
                    return CommandResult(error=f"Is a directory: {file_path}", exit_code=1)
            except FileNotFoundError as e:
                return CommandResult(error=str(e), exit_code=1)
            except PermissionError as e:
                return CommandResult(error=str(e), exit_code=13)
        
        return CommandResult(output='\n'.join(output_lines))
    
    def cmd_echo(self, args: List[str]) -> CommandResult:
        """Display text."""
        # Handle basic escape sequences
        text = ' '.join(args)
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        return CommandResult(output=text)
    
    def cmd_mkdir(self, args: List[str]) -> CommandResult:
        """Create directories."""
        if not args:
            return CommandResult(error="Usage: mkdir [-p] <directory>", exit_code=1)
        
        recursive = '-p' in args
        dir_names = [arg for arg in args if not arg.startswith('-')]
        
        for dir_name in dir_names:
            resolved_path = self._resolve_path(dir_name)
            try:
                self.fs.create_directory(resolved_path, self.current_user, recursive)
            except FileExistsError:
                if not recursive:
                    return CommandResult(error=f"File exists: {dir_name}", exit_code=1)
            except Exception as e:
                return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_rm(self, args: List[str]) -> CommandResult:
        """Remove files or directories."""
        if not args:
            return CommandResult(error="Usage: rm [-rf] <file/directory>", exit_code=1)
        
        recursive = '-r' in args or '-R' in args
        force = '-f' in args
        paths = [arg for arg in args if not arg.startswith('-')]
        
        for path in paths:
            resolved_path = self._resolve_path(path)
            try:
                self.fs.delete(resolved_path, self.current_user, recursive)
            except FileNotFoundError:
                if not force:
                    return CommandResult(error=f"No such file: {path}", exit_code=1)
            except Exception as e:
                if not force:
                    return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_cp(self, args: List[str]) -> CommandResult:
        """Copy files or directories."""
        if len(args) < 2:
            return CommandResult(error="Usage: cp [-r] <source> <destination>", exit_code=1)
        
        recursive = '-r' in args or '-R' in args
        paths = [arg for arg in args if not arg.startswith('-')]
        src_path = self._resolve_path(paths[0])
        dst_path = self._resolve_path(paths[1])
        
        try:
            self.fs.copy(src_path, dst_path, self.current_user)
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_mv(self, args: List[str]) -> CommandResult:
        """Move/rename files or directories."""
        if len(args) < 2:
            return CommandResult(error="Usage: mv <source> <destination>", exit_code=1)
        
        src_path = self._resolve_path(args[0])
        dst_path = self._resolve_path(args[1])
        
        try:
            self.fs.move(src_path, dst_path, self.current_user)
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_touch(self, args: List[str]) -> CommandResult:
        """Create empty files or update timestamps."""
        if not args:
            return CommandResult(error="Usage: touch <file>", exit_code=1)
        
        for file_path in args:
            resolved_path = self._resolve_path(file_path)
            try:
                file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
                # File exists, just update timestamp
                file_obj.update_access_time()
                file_obj.update_modify_time()
            except FileNotFoundError:
                # Create new file
                self.fs.create_file(resolved_path, "", self.current_user)
        
        return CommandResult(output="")
    
    def cmd_chmod(self, args: List[str]) -> CommandResult:
        """Change file permissions."""
        if len(args) < 2:
            return CommandResult(error="Usage: chmod <mode> <file>", exit_code=1)
        
        mode = args[0]
        file_path = self._resolve_path(args[1])
        
        try:
            from ..filesystem.permissions import Permissions
            file_obj = self.fs.resolve_file(file_path, self.current_dir)
            
            if mode.isdigit():
                # Octal notation
                file_obj.permissions = Permissions.from_octal(mode)
            else:
                # Symbolic notation (simplified)
                return CommandResult(error="Symbolic notation not yet implemented. Use octal (e.g., 755)", exit_code=1)
            
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_chown(self, args: List[str]) -> CommandResult:
        """Change file owner."""
        if len(args) < 2:
            return CommandResult(error="Usage: chown <user> <file>", exit_code=1)
        
        username = args[0]
        file_path = self._resolve_path(args[1])
        
        # Find user by username or uid
        target_user = None
        if username.isdigit():
            target_user = self.fs.get_user(int(username))
        else:
            for user in self.fs.users.values():
                if user.username == username:
                    target_user = user
                    break
        
        if not target_user:
            return CommandResult(error=f"Unknown user: {username}", exit_code=1)
        
        try:
            file_obj = self.fs.resolve_file(file_path, self.current_dir)
            file_obj.owner_uid = target_user.uid
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output="")
    
    def cmd_whoami(self, args: List[str]) -> CommandResult:
        """Display current user."""
        return CommandResult(output=self.current_user.username)
    
    def cmd_su(self, args: List[str]) -> CommandResult:
        """Switch user."""
        if not args:
            # Switch to root
            self.current_user = self.fs.users[0]
            return CommandResult(output="")
        
        username = args[0]
        
        # Find user
        target_user = None
        if username.isdigit():
            target_user = self.fs.get_user(int(username))
        else:
            for user in self.fs.users.values():
                if user.username == username:
                    target_user = user
                    break
        
        if not target_user:
            return CommandResult(error=f"Unknown user: {username}", exit_code=1)
        
        # In a real implementation, would prompt for password
        self.current_user = target_user
        return CommandResult(output=f"Switched to user {username}")
    
    def cmd_exit(self, args: List[str]) -> CommandResult:
        """Exit the shell."""
        return CommandResult(output="__EXIT__")
    
    def cmd_clear(self, args: List[str]) -> CommandResult:
        """Clear the screen."""
        return CommandResult(output="__CLEAR__")
    
    def cmd_history(self, args: List[str]) -> CommandResult:
        """Show command history."""
        lines = [f"{i+1:4d}  {cmd}" for i, cmd in enumerate(self.history)]
        return CommandResult(output='\n'.join(lines))
    
    def cmd_alias(self, args: List[str]) -> CommandResult:
        """Define or display aliases."""
        if not args:
            # Show all aliases
            aliases_str = '\n'.join([f"{k}='{v}'" for k, v in self.aliases.items()])
            return CommandResult(output=aliases_str)
        
        if len(args) == 1:
            # Show specific alias
            alias_name = args[0]
            if alias_name in self.aliases:
                return CommandResult(output=f"{alias_name}='{self.aliases[alias_name]}'")
            else:
                return CommandResult(error=f"Alias not found: {alias_name}", exit_code=1)
        
        # Define new alias
        alias_def = ' '.join(args[1:])
        if alias_def.startswith("'") and alias_def.endswith("'"):
            alias_def = alias_def[1:-1]
        elif alias_def.startswith('"') and alias_def.endswith('"'):
            alias_def = alias_def[1:-1]
        
        self.aliases[args[0]] = alias_def
        return CommandResult(output="")
    
    def cmd_grep(self, args: List[str]) -> CommandResult:
        """Search for patterns in files."""
        if len(args) < 2:
            return CommandResult(error="Usage: grep <pattern> <file>", exit_code=1)
        
        pattern = args[0]
        file_path = self._resolve_path(args[1])
        
        ignore_case = '-i' in args
        file_obj = self.fs.resolve_file(file_path, self.current_dir)
        
        if not isinstance(file_obj, VirtualFile):
            return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
        
        content = file_obj.read(self.current_user)
        lines = content.split('\n')
        
        matching_lines = []
        for line in lines:
            search_line = line if not ignore_case else line.lower()
            search_pattern = pattern if not ignore_case else pattern.lower()
            
            if search_pattern in search_line:
                matching_lines.append(line)
        
        return CommandResult(output='\n'.join(matching_lines))
    
    def cmd_head(self, args: List[str]) -> CommandResult:
        """Display first lines of a file."""
        if not args:
            return CommandResult(error="Usage: head [-n N] <file>", exit_code=1)
        
        n = 10
        file_path = None
        
        i = 0
        while i < len(args):
            if args[i] == '-n' and i + 1 < len(args):
                n = int(args[i + 1])
                i += 2
            elif not args[i].startswith('-'):
                file_path = args[i]
                i += 1
            else:
                i += 1
        
        if not file_path:
            return CommandResult(error="No file specified", exit_code=1)
        
        resolved_path = self._resolve_path(file_path)
        file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
        
        if not isinstance(file_obj, VirtualFile):
            return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
        
        content = file_obj.read(self.current_user)
        lines = content.split('\n')
        
        return CommandResult(output='\n'.join(lines[:n]))
    
    def cmd_tail(self, args: List[str]) -> CommandResult:
        """Display last lines of a file."""
        if not args:
            return CommandResult(error="Usage: tail [-n N] <file>", exit_code=1)
        
        n = 10
        file_path = None
        
        i = 0
        while i < len(args):
            if args[i] == '-n' and i + 1 < len(args):
                n = int(args[i + 1])
                i += 2
            elif not args[i].startswith('-'):
                file_path = args[i]
                i += 1
            else:
                i += 1
        
        if not file_path:
            return CommandResult(error="No file specified", exit_code=1)
        
        resolved_path = self._resolve_path(file_path)
        file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
        
        if not isinstance(file_obj, VirtualFile):
            return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
        
        content = file_obj.read(self.current_user)
        lines = content.split('\n')
        
        return CommandResult(output='\n'.join(lines[-n:]))
    
    def cmd_wc(self, args: List[str]) -> CommandResult:
        """Count words, lines, and bytes in files."""
        if not args:
            return CommandResult(error="Usage: wc [-lwc] <file>", exit_code=1)
        
        count_lines = '-l' in args
        count_words = '-w' in args
        count_bytes = '-c' in args
        
        show_all = not (count_lines or count_words or count_bytes)
        
        file_path = [arg for arg in args if not arg.startswith('-')][0]
        resolved_path = self._resolve_path(file_path)
        file_obj = self.fs.resolve_file(resolved_path, self.current_dir)
        
        if not isinstance(file_obj, VirtualFile):
            return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
        
        content = file_obj.read(self.current_user)
        
        lines = len(content.split('\n')) if count_lines or show_all else 0
        words = len(content.split()) if count_words or show_all else 0
        bytes_count = len(content.encode('utf-8')) if count_bytes or show_all else 0
        
        if show_all:
            return CommandResult(output=f"{lines:7d} {words:7d} {bytes_count:7d} {file_path}")
        else:
            result = []
            if count_lines:
                result.append(str(lines))
            if count_words:
                result.append(str(words))
            if count_bytes:
                result.append(str(bytes_count))
            return CommandResult(output=' '.join(result) + f" {file_path}")
    
    def cmd_find(self, args: List[str]) -> CommandResult:
        """Find files and directories."""
        if not args:
            return CommandResult(error="Usage: find <path> [options]", exit_code=1)
        
        start_path = self._resolve_path(args[0])
        name_pattern = None
        type_filter = None
        
        i = 1
        while i < len(args):
            if args[i] == '-name' and i + 1 < len(args):
                name_pattern = args[i + 1]
                i += 2
            elif args[i] == '-type' and i + 1 < len(args):
                type_filter = args[i + 1]
                i += 2
            else:
                i += 1
        
        results = []
        
        def search_recursive(directory: VirtualDirectory):
            for entry_name, entry in directory.entries.items():
                # Apply filters
                if name_pattern:
                    import fnmatch
                    if not fnmatch.fnmatch(entry_name, name_pattern):
                        continue
                
                if type_filter:
                    if type_filter == 'f' and not isinstance(entry, VirtualFile):
                        continue
                    elif type_filter == 'd' and not isinstance(entry, VirtualDirectory):
                        continue
                
                results.append(entry.path)
                
                if isinstance(entry, VirtualDirectory):
                    search_recursive(entry)
        
        try:
            start_dir = self.fs.resolve_path(start_path, self.current_dir)
            if not isinstance(start_dir, VirtualDirectory):
                return CommandResult(error=f"Not a directory: {start_path}", exit_code=1)
            search_recursive(start_dir)
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
        
        return CommandResult(output='\n'.join(results))
    
    def cmd_locate(self, args: List[str]) -> CommandResult:
        """Find files by name (simplified version)."""
        if not args:
            return CommandResult(error="Usage: locate <pattern>", exit_code=1)
        
        pattern = args[0].lower()
        results = []
        
        def search_recursive(directory: VirtualDirectory):
            for entry_name, entry in directory.entries.items():
                if pattern in entry_name.lower():
                    results.append(entry.path)
                
                if isinstance(entry, VirtualDirectory):
                    search_recursive(entry)
        
        search_recursive(self.fs.root)
        return CommandResult(output='\n'.join(results))
    
    def cmd_man(self, args: List[str]) -> CommandResult:
        """Display manual pages."""
        if not args:
            return CommandResult(error="Usage: man <command>", exit_code=1)
        
        cmd_name = args[0]
        
        if cmd_name not in self.commands:
            return CommandResult(error=f"No manual entry for {cmd_name}", exit_code=1)
        
        cmd_func = self.commands[cmd_name]
        doc = cmd_func.__doc__ or "No documentation available."
        
        man_page = f"""NAME
       {cmd_name} - simulated command

SYNOPSIS
       {cmd_name} [OPTIONS] [ARGUMENTS]

DESCRIPTION
       {doc}

NOTE
       This is a simulated command in Kali Linux Simulator.
       Some features may not be fully implemented.
"""
        return CommandResult(output=man_page)
    
    def cmd_file(self, args: List[str]) -> CommandResult:
        """Determine file type."""
        if not args:
            return CommandResult(error="Usage: file <file>", exit_code=1)
        
        file_path = self._resolve_path(args[0])
        file_obj = self.fs.resolve_file(file_path, self.current_dir)
        
        if isinstance(file_obj, VirtualDirectory):
            return CommandResult(output=f"{file_path}: directory")
        
        if file_obj.mime_type == "text/plain":
            return CommandResult(output=f"{file_path}: ASCII text")
        elif file_obj.is_executable:
            return CommandResult(output=f"{file_path}: executable script")
        else:
            return CommandResult(output=f"{file_path}: data")
    
    def cmd_less(self, args: List[str]) -> CommandResult:
        """View file contents one screen at a time."""
        if not args:
            return CommandResult(error="Usage: less <file>", exit_code=1)
        
        file_path = self._resolve_path(args[0])
        file_obj = self.fs.resolve_file(file_path, self.current_dir)
        
        if not isinstance(file_obj, VirtualFile):
            return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
        
        content = file_obj.read(self.current_user)
        return CommandResult(output=content)
    
    def cmd_more(self, args: List[str]) -> CommandResult:
        """View file contents page by page."""
        return self.cmd_less(args)
    
    def cmd_nano(self, args: List[str]) -> CommandResult:
        """Open nano editor (simulated)."""
        if not args:
            return CommandResult(error="Usage: nano <file>", exit_code=1)
        
        return CommandResult(output="[Nano editor simulation not fully implemented]")
    
    def cmd_vim(self, args: List[str]) -> CommandResult:
        """Open vim editor (simulated)."""
        if not args:
            return CommandResult(error="Usage: vim <file>", exit_code=1)
        
        return CommandResult(output="[Vim editor simulation not fully implemented]\n:wq to exit")
    
    def cmd_python3(self, args: List[str]) -> CommandResult:
        """Run Python interpreter or script."""
        if not args:
            return CommandResult(output="[Python3 interactive mode not implemented in simulator]")
        
        file_path = self._resolve_path(args[0])
        
        try:
            file_obj = self.fs.resolve_file(file_path, self.current_dir)
            if not isinstance(file_obj, VirtualFile):
                return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
            
            content = file_obj.read(self.current_user)
            
            # In a real implementation, this would execute Python code
            # For now, just show a message
            return CommandResult(output=f"[Would execute Python script: {file_path}]\nCode length: {len(content)} chars")
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
    
    def cmd_execute(self, args: List[str]) -> CommandResult:
        """Execute a file."""
        # This is called when user types ./script
        if not args:
            return CommandResult(error="Usage: ./<file>", exit_code=1)
        
        file_path = self._resolve_path(args[0])
        
        try:
            file_obj = self.fs.resolve_file(file_path, self.current_dir)
            if not isinstance(file_obj, VirtualFile):
                return CommandResult(error=f"Not a file: {file_path}", exit_code=1)
            
            if not file_obj.is_executable:
                return CommandResult(error=f"Permission denied: {file_path} is not executable", exit_code=13)
            
            return file_obj.execute(self.current_user, args[1:])
        except Exception as e:
            return CommandResult(error=str(e), exit_code=1)
    
    # Simulated Kali tools
    
    def cmd_nmap(self, args: List[str]) -> CommandResult:
        """Simulated nmap network scanner."""
        if not args:
            return CommandResult(error="Usage: nmap [options] <target>", exit_code=1)
        
        target = args[-1]
        
        output = f"""Starting Nmap 7.94 ( https://nmap.org )
Nmap scan report for {target}
Host is up (0.0023s latency).
Not shown: 997 closed ports
PORT    STATE SERVICE
22/tcp  open  ssh
80/tcp  open  http
443/tcp open  https

Nmap done: 1 IP address (1 host up) scanned in 0.56 seconds
"""
        return CommandResult(output=output)
    
    def cmd_ifconfig(self, args: List[str]) -> CommandResult:
        """Simulated ifconfig network configuration."""
        output = """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255
        ether 00:0c:29:xx:xx:xx  txqueuelen 1000  (Ethernet)
        RX packets 1234  bytes 987654 (964.5 KiB)
        TX packets 5678  bytes 123456 (120.5 KiB)

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 100  bytes 12345 (12.0 KiB)
        TX packets 100  bytes 12345 (12.0 KiB)
"""
        return CommandResult(output=output)
    
    def cmd_ip(self, args: List[str]) -> CommandResult:
        """Simulated ip command."""
        if not args or args[0] == 'addr':
            output = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:xx:xx:xx brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global dynamic eth0
       valid_lft 86399sec preferred_lft 86399sec
"""
            return CommandResult(output=output)
        return CommandResult(output="ip command options not fully implemented")
    
    def cmd_ping(self, args: List[str]) -> CommandResult:
        """Simulated ping command."""
        if not args:
            return CommandResult(error="Usage: ping <host>", exit_code=1)
        
        host = args[0]
        count = 4
        
        if '-c' in args:
            idx = args.index('-c')
            if idx + 1 < len(args):
                count = int(args[idx + 1])
        
        output = f"PING {host} ({host}) 56(84) bytes of data.\n"
        for i in range(count):
            output += f"64 bytes from {host}: icmp_seq={i+1} ttl=64 time=0.{10+i} ms\n"
        
        output += f"\n--- {host} ping statistics ---\n"
        output += f"{count} packets transmitted, {count} received, 0% packet loss, time 3004ms\n"
        
        return CommandResult(output=output)
    
    def cmd_netstat(self, args: List[str]) -> CommandResult:
        """Simulated netstat command."""
        output = """Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN
tcp        0      0 192.168.1.100:22        192.168.1.1:54321       ESTABLISHED
udp        0      0 0.0.0.0:68              0.0.0.0:*                           
"""
        return CommandResult(output=output)
    
    def cmd_ss(self, args: List[str]) -> CommandResult:
        """Simulated ss command."""
        return self.cmd_netstat(args)
    
    def cmd_wget(self, args: List[str]) -> CommandResult:
        """Simulated wget command."""
        if not args:
            return CommandResult(error="Usage: wget <url>", exit_code=1)
        
        url = args[0]
        return CommandResult(output=f"[Would download: {url}]\nwget simulation not fully implemented")
    
    def cmd_curl(self, args: List[str]) -> CommandResult:
        """Simulated curl command."""
        if not args:
            return CommandResult(error="Usage: curl <url>", exit_code=1)
        
        url = args[0]
        return CommandResult(output=f"[Would fetch: {url}]\ncurl simulation not fully implemented")
    
    def cmd_hashcat(self, args: List[str]) -> CommandResult:
        """Simulated hashcat password cracker."""
        return CommandResult(output="[Hashcat password cracker simulation]\nUsage: hashcat [options] <hashfile> <wordlist>")
    
    def cmd_john(self, args: List[str]) -> CommandResult:
        """Simulated John the Ripper."""
        return CommandResult(output="[John the Ripper simulation]\nUsage: john [options] <password-file>")
    
    def cmd_hydra(self, args: List[str]) -> CommandResult:
        """Simulated Hydra login cracker."""
        return CommandResult(output="[Hydra login cracker simulation]\nUsage: hydra [[-l LOGIN|-L file] [-p PASS|-P file]] <target> <service>")
    
    def cmd_metasploit(self, args: List[str]) -> CommandResult:
        """Simulated Metasploit framework."""
        return CommandResult(output="[Metasploit Framework simulation]\nUse 'msfconsole' to start the console")
    
    def cmd_msfconsole(self, args: List[str]) -> CommandResult:
        """Simulated Metasploit console."""
        return CommandResult(output="""
       =[ metasploit v6.3.0-dev                           ]
+ -- --=[ 2347 exploits - 1218 auxiliary - 413 post       ]
+ -- --=[ 1397 payloads - 46 encoders - 11 nops           ]
+ -- --=[ 9 evasion                                       ]

Metasploit tip: You can set a payload within a module using 
the SET PAYLOAD command.

msf6 > [Console simulation - use commands like 'use', 'search', 'set']
""")
    
    def cmd_sqlmap(self, args: List[str]) -> CommandResult:
        """Simulated sqlmap SQL injection tool."""
        return CommandResult(output="[sqlmap SQL injection tool simulation]\nUsage: sqlmap -u <URL> [options]")
    
    def cmd_nikto(self, args: List[str]) -> CommandResult:
        """Simulated Nikto web scanner."""
        return CommandResult(output="[Nikto web scanner simulation]\nUsage: nikto -h <target>")
    
    def cmd_burp(self, args: List[str]) -> CommandResult:
        """Simulated Burp Suite."""
        return CommandResult(output="[Burp Suite simulation]\nGUI-based tool - not available in CLI mode")
    
    def cmd_wireshark(self, args: List[str]) -> CommandResult:
        """Simulated Wireshark."""
        return CommandResult(output="[Wireshark simulation]\nGUI-based tool - use 'tcpdump' for CLI packet capture")
    
    def cmd_tcpdump(self, args: List[str]) -> CommandResult:
        """Simulated tcpdump packet analyzer."""
        return CommandResult(output="[tcpdump packet analyzer simulation]\nUsage: tcpdump [options] [filter]")
    
    def cmd_aircrack(self, args: List[str]) -> CommandResult:
        """Simulated aircrack-ng."""
        return CommandResult(output="[aircrack-ng WiFi cracking simulation]\nUsage: aircrack-ng [options] <capture file>")
    
    def cmd_reaver(self, args: List[str]) -> CommandResult:
        """Simulated Reaver WPS cracker."""
        return CommandResult(output="[Reaver WPS cracker simulation]\nUsage: reaver -i <interface> -b <BSSID>")
    
    def cmd_wifite(self, args: List[str]) -> CommandResult:
        """Simulated Wifite automated attacker."""
        return CommandResult(output="[Wifite automated WiFi attacker simulation]\nUsage: wifite [options]")
    
    def cmd_setoolkit(self, args: List[str]) -> CommandResult:
        """Simulated Social Engineer Toolkit."""
        return CommandResult(output="[Social Engineer Toolkit simulation]\nMenu-driven GUI tool")
    
    def cmd_beef(self, args: List[str]) -> CommandResult:
        """Simulated BeEF browser exploitation framework."""
        return CommandResult(output="[BeEF Browser Exploitation Framework simulation]\nWeb-based tool")
    
    def cmd_zap(self, args: List[str]) -> CommandResult:
        """Simulated OWASP ZAP."""
        return CommandResult(output="[OWASP ZAP simulation]\nGUI-based web application scanner")
