"""
KaliLang - Custom Python-like programming language for Kali Linux Simulator.
Inspired by Grey Hack's scripting system.
Provides automation capabilities for security tasks.
"""

import re
import ast
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum


class TokenType(Enum):
    """Token types for lexer."""
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"
    KEYWORD = "KEYWORD"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    COLON = "COLON"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass
class Token:
    """Represents a lexical token."""
    type: TokenType
    value: Any
    line: int
    column: int


class Lexer:
    """Tokenizer for KaliLang."""
    
    KEYWORDS = {
        'var', 'func', 'return', 'if', 'else', 'while', 'for', 'in',
        'break', 'continue', 'import', 'print', 'scan', 'connect',
        'exploit', 'crack', 'upload', 'download', 'exec'
    }
    
    OPERATORS = {
        '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
        'and', 'or', 'not', '+=', '-=', '*=', '/='
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the source code."""
        while self.pos < len(self.source):
            char = self.source[self.pos]
            
            if char == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', self.line, self.column))
                self.line += 1
                self.column = 1
                self.pos += 1
            elif char.isspace():
                self.column += 1
                self.pos += 1
            elif char == '#':
                # Comment
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            elif char.isdigit() or (char == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1].isdigit()):
                self._read_number()
            elif char == '"' or char == "'":
                self._read_string(char)
            elif char.isalpha() or char == '_':
                self._read_identifier()
            elif char in '(){}[],:':
                token_map = {
                    '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                    '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                    '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                    ',': TokenType.COMMA, ':': TokenType.COLON
                }
                self.tokens.append(Token(token_map[char], char, self.line, self.column))
                self.column += 1
                self.pos += 1
            elif char in '+-*/%<>!=':
                self._read_operator()
            else:
                raise SyntaxError(f"Unexpected character '{char}' at line {self.line}, column {self.column}")
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
    
    def _read_number(self):
        """Read a number token."""
        start_pos = self.pos
        start_line = self.line
        start_col = self.column
        
        if self.source[self.pos] == '-':
            self.pos += 1
            self.column += 1
        
        while self.pos < len(self.source) and self.source[self.pos].isdigit():
            self.pos += 1
            self.column += 1
        
        if self.pos < len(self.source) and self.source[self.pos] == '.':
            self.pos += 1
            self.column += 1
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                self.pos += 1
                self.column += 1
            value = float(self.source[start_pos:self.pos])
        else:
            value = int(self.source[start_pos:self.pos])
        
        self.tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))
    
    def _read_string(self, quote: str):
        """Read a string token."""
        start_line = self.line
        start_col = self.column
        self.pos += 1  # Skip opening quote
        self.column += 1
        
        result = []
        while self.pos < len(self.source) and self.source[self.pos] != quote:
            if self.source[self.pos] == '\\':
                self.pos += 1
                self.column += 1
                if self.pos < len(self.source):
                    escape_char = self.source[self.pos]
                    if escape_char == 'n':
                        result.append('\n')
                    elif escape_char == 't':
                        result.append('\t')
                    elif escape_char == '\\':
                        result.append('\\')
                    elif escape_char == quote:
                        result.append(quote)
                    else:
                        result.append(escape_char)
                    self.pos += 1
                    self.column += 1
            else:
                if self.source[self.pos] == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                result.append(self.source[self.pos])
                self.pos += 1
        
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated string at line {start_line}")
        
        self.pos += 1  # Skip closing quote
        self.column += 1
        
        self.tokens.append(Token(TokenType.STRING, ''.join(result), start_line, start_col))
    
    def _read_identifier(self):
        """Read an identifier or keyword token."""
        start_pos = self.pos
        start_line = self.line
        start_col = self.column
        
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            self.pos += 1
            self.column += 1
        
        value = self.source[start_pos:self.pos]
        
        if value in self.KEYWORDS:
            self.tokens.append(Token(TokenType.KEYWORD, value, start_line, start_col))
        elif value in self.OPERATORS:
            self.tokens.append(Token(TokenType.OPERATOR, value, start_line, start_col))
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, value, start_line, start_col))
    
    def _read_operator(self):
        """Read an operator token."""
        start_pos = self.pos
        start_line = self.line
        start_col = self.column
        
        # Try two-character operators first
        if self.pos + 1 < len(self.source):
            two_char = self.source[self.pos:self.pos + 2]
            if two_char in self.OPERATORS:
                self.tokens.append(Token(TokenType.OPERATOR, two_char, start_line, start_col))
                self.pos += 2
                self.column += 2
                return
        
        # Single character operator
        char = self.source[self.pos]
        if char in self.OPERATORS:
            self.tokens.append(Token(TokenType.OPERATOR, char, start_line, start_col))
        
        self.pos += 1
        self.column += 1


@dataclass
class ASTNode:
    """Base class for AST nodes."""
    pass


@dataclass
class NumberNode(ASTNode):
    value: Union[int, float]


@dataclass
class StringNode(ASTNode):
    value: str


@dataclass
class IdentifierNode(ASTNode):
    name: str


@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    op: str
    operand: ASTNode


@dataclass
class AssignmentNode(ASTNode):
    name: str
    value: ASTNode


@dataclass
class FunctionCallNode(ASTNode):
    name: str
    args: List[ASTNode]


@dataclass
class FunctionDefNode(ASTNode):
    name: str
    params: List[str]
    body: List[ASTNode]


@dataclass
class IfNode(ASTNode):
    condition: ASTNode
    then_block: List[ASTNode]
    else_block: List[ASTNode] = field(default_factory=list)


@dataclass
class WhileNode(ASTNode):
    condition: ASTNode
    body: List[ASTNode]


@dataclass
class ForNode(ASTNode):
    var: str
    iterable: ASTNode
    body: List[ASTNode]


@dataclass
class ReturnNode(ASTNode):
    value: Optional[ASTNode]


@dataclass
class PrintNode(ASTNode):
    value: ASTNode


@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]


class Parser:
    """Parser for KaliLang."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]
    
    def peek_token(self, offset: int = 1) -> Token:
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else self.tokens[-1]
    
    def advance(self):
        self.pos += 1
    
    def expect(self, token_type: TokenType, value: Any = None):
        token = self.current_token()
        if token.type != token_type or (value is not None and token.value != value):
            raise SyntaxError(f"Expected {token_type} {value}, got {token.type} {token.value} at line {token.line}")
        self.advance()
    
    def parse(self) -> ProgramNode:
        """Parse the token stream into an AST."""
        statements = []
        
        while self.current_token().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return ProgramNode(statements)
    
    def parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        token = self.current_token()
        
        # Skip newlines
        while token.type == TokenType.NEWLINE:
            self.advance()
            token = self.current_token()
        
        if token.type == TokenType.EOF:
            return None
        
        if token.type == TokenType.KEYWORD:
            if token.value == 'var':
                return self.parse_assignment()
            elif token.value == 'func':
                return self.parse_function_def()
            elif token.value == 'if':
                return self.parse_if()
            elif token.value == 'while':
                return self.parse_while()
            elif token.value == 'for':
                return self.parse_for()
            elif token.value == 'return':
                return self.parse_return()
            elif token.value == 'print':
                return self.parse_print()
            elif token.value == 'break':
                self.advance()
                return BreakNode()
            elif token.value == 'continue':
                self.advance()
                return ContinueNode()
        
        # Expression statement
        expr = self.parse_expression()
        
        # Check for assignment
        if self.current_token().type == TokenType.OPERATOR and self.current_token().value == '=':
            if isinstance(expr, IdentifierNode):
                self.advance()
                value = self.parse_expression()
                return AssignmentNode(expr.name, value)
        
        return expr
    
    def parse_assignment(self) -> AssignmentNode:
        """Parse variable assignment."""
        self.expect(TokenType.KEYWORD, 'var')
        name_token = self.current_token()
        if name_token.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"Expected identifier, got {name_token.type} at line {name_token.line}")
        self.advance()
        
        self.expect(TokenType.OPERATOR, '=')
        value = self.parse_expression()
        
        return AssignmentNode(name_token.value, value)
    
    def parse_function_def(self) -> FunctionDefNode:
        """Parse function definition."""
        self.expect(TokenType.KEYWORD, 'func')
        name_token = self.current_token()
        if name_token.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"Expected function name, got {name_token.type} at line {name_token.line}")
        self.advance()
        
        self.expect(TokenType.LPAREN)
        params = []
        if self.current_token().type != TokenType.RPAREN:
            params.append(self.current_token().value)
            self.advance()
            while self.current_token().type == TokenType.COMMA:
                self.advance()
                params.append(self.current_token().value)
                self.advance()
        self.expect(TokenType.RPAREN)
        
        body = self.parse_block()
        
        return FunctionDefNode(name_token.value, params, body)
    
    def parse_if(self) -> IfNode:
        """Parse if statement."""
        self.expect(TokenType.KEYWORD, 'if')
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_block = []
        
        if self.current_token().type == TokenType.KEYWORD and self.current_token().value == 'else':
            self.advance()
            else_block = self.parse_block()
        
        return IfNode(condition, then_block, else_block)
    
    def parse_while(self) -> WhileNode:
        """Parse while loop."""
        self.expect(TokenType.KEYWORD, 'while')
        condition = self.parse_expression()
        body = self.parse_block()
        return WhileNode(condition, body)
    
    def parse_for(self) -> ForNode:
        """Parse for loop."""
        self.expect(TokenType.KEYWORD, 'for')
        var_token = self.current_token()
        if var_token.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"Expected identifier, got {var_token.type} at line {var_token.line}")
        self.advance()
        
        self.expect(TokenType.KEYWORD, 'in')
        iterable = self.parse_expression()
        body = self.parse_block()
        
        return ForNode(var_token.value, iterable, body)
    
    def parse_return(self) -> ReturnNode:
        """Parse return statement."""
        self.expect(TokenType.KEYWORD, 'return')
        
        if self.current_token().type == TokenType.NEWLINE or self.current_token().type == TokenType.EOF:
            return ReturnNode(None)
        
        value = self.parse_expression()
        return ReturnNode(value)
    
    def parse_print(self) -> PrintNode:
        """Parse print statement."""
        self.expect(TokenType.KEYWORD, 'print')
        value = self.parse_expression()
        return PrintNode(value)
    
    def parse_block(self) -> List[ASTNode]:
        """Parse a block of statements."""
        statements = []
        
        # Check for brace-delimited block
        if self.current_token().type == TokenType.LBRACE:
            self.advance()
            while self.current_token().type != TokenType.RBRACE and self.current_token().type != TokenType.EOF:
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            self.expect(TokenType.RBRACE)
        else:
            # Single statement
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        return statements
    
    def parse_expression(self) -> ASTNode:
        """Parse an expression."""
        return self.parse_comparison()
    
    def parse_comparison(self) -> ASTNode:
        """Parse comparison expression."""
        left = self.parse_additive()
        
        while self.current_token().type == TokenType.OPERATOR and \
              self.current_token().value in ('==', '!=', '<', '>', '<=', '>='):
            op = self.current_token().value
            self.advance()
            right = self.parse_additive()
            left = BinaryOpNode(left, op, right)
        
        return left
    
    def parse_additive(self) -> ASTNode:
        """Parse additive expression."""
        left = self.parse_multiplicative()
        
        while self.current_token().type == TokenType.OPERATOR and \
              self.current_token().value in ('+', '-'):
            op = self.current_token().value
            self.advance()
            right = self.parse_multiplicative()
            left = BinaryOpNode(left, op, right)
        
        return left
    
    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplicative expression."""
        left = self.parse_unary()
        
        while self.current_token().type == TokenType.OPERATOR and \
              self.current_token().value in ('*', '/', '%'):
            op = self.current_token().value
            self.advance()
            right = self.parse_unary()
            left = BinaryOpNode(left, op, right)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Parse unary expression."""
        if self.current_token().type == TokenType.OPERATOR and \
           self.current_token().value in ('-', 'not'):
            op = self.current_token().value
            self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(op, operand)
        
        return self.parse_primary()
    
    def parse_primary(self) -> ASTNode:
        """Parse primary expression."""
        token = self.current_token()
        
        if token.type == TokenType.NUMBER:
            self.advance()
            return NumberNode(token.value)
        
        elif token.type == TokenType.STRING:
            self.advance()
            return StringNode(token.value)
        
        elif token.type == TokenType.IDENTIFIER:
            name = token.value
            self.advance()
            
            # Check for function call
            if self.current_token().type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.current_token().type != TokenType.RPAREN:
                    args.append(self.parse_expression())
                    while self.current_token().type == TokenType.COMMA:
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TokenType.RPAREN)
                return FunctionCallNode(name, args)
            
            return IdentifierNode(name)
        
        elif token.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        
        elif token.type == TokenType.LBRACKET:
            # List literal
            self.advance()
            elements = []
            if self.current_token().type != TokenType.RBRACKET:
                elements.append(self.parse_expression())
                while self.current_token().type == TokenType.COMMA:
                    self.advance()
                    elements.append(self.parse_expression())
            self.expect(TokenType.RBRACKET)
            return ListNode(elements)
        
        raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")


@dataclass
class BreakNode(ASTNode):
    pass


@dataclass
class ContinueNode(ASTNode):
    pass


@dataclass
class ListNode(ASTNode):
    elements: List[ASTNode]


class Interpreter:
    """Interpreter for KaliLang."""
    
    def __init__(self, filesystem=None, network_manager=None):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, FunctionDefNode] = {}
        self.builtins: Dict[str, Callable] = {}
        self.filesystem = filesystem
        self.network_manager = network_manager
        self.return_value: Any = None
        self.in_loop = False
        self.loop_break = False
        self.loop_continue = False
        
        self._register_builtins()
    
    def _register_builtins(self):
        """Register built-in functions."""
        self.builtins['print'] = self._builtin_print
        self.builtins['len'] = self._builtin_len
        self.builtins['str'] = self._builtin_str
        self.builtins['int'] = self._builtin_int
        self.builtins['float'] = self._builtin_float
        self.builtins['range'] = self._builtin_range
        self.builtins['list'] = self._builtin_list
        self.builtins['append'] = self._builtin_append
        
        # Security-related builtins (simulated)
        self.builtins['scan'] = self._builtin_scan
        self.builtins['connect'] = self._builtin_connect
        self.builtins['exploit'] = self._builtin_exploit
        self.builtins['crack'] = self._builtin_crack
        self.builtins['upload'] = self._builtin_upload
        self.builtins['download'] = self._builtin_download
        self.builtins['exec'] = self._builtin_exec
    
    def _builtin_print(self, *args):
        print(' '.join(str(a) for a in args))
        return None
    
    def _builtin_len(self, obj):
        return len(obj)
    
    def _builtin_str(self, obj):
        return str(obj)
    
    def _builtin_int(self, obj):
        return int(obj)
    
    def _builtin_float(self, obj):
        return float(obj)
    
    def _builtin_range(self, *args):
        return list(range(*args))
    
    def _builtin_list(self):
        return []
    
    def _builtin_append(self, lst, item):
        lst.append(item)
        return lst
    
    def _builtin_scan(self, target):
        """Simulate network scanning."""
        if self.network_manager:
            ip = self.network_manager.resolve_hostname(str(target))
            if ip:
                host = self.network_manager.get_or_create_host(ip)
                return {"ip": str(ip), "ports": host.open_ports, "os": host.os_type}
        return {"error": "Scan failed"}
    
    def _builtin_connect(self, host, port):
        """Simulate connection to remote host."""
        if self.network_manager:
            ip = self.network_manager.resolve_hostname(str(host))
            if ip:
                local_ip = self.network_manager.get_primary_ip()
                if local_ip:
                    conn = self.network_manager.create_connection(
                        local_ip, 40000 + len(self.network_manager.connections),
                        ip, int(port)
                    )
                    return {"connected": True, "conn_id": conn.id}
        return {"connected": False}
    
    def _builtin_exploit(self, target, exploit_name):
        """Simulate exploit execution."""
        return {"success": True, "message": f"Exploited {target} with {exploit_name}"}
    
    def _builtin_crack(self, hash_val, wordlist="rockyou"):
        """Simulate password cracking."""
        return {"cracked": True, "password": "password123", "time": 0.5}
    
    def _builtin_upload(self, local_path, remote_path):
        """Simulate file upload."""
        return {"success": True, "path": remote_path}
    
    def _builtin_download(self, remote_path, local_path):
        """Simulate file download."""
        return {"success": True, "path": local_path}
    
    def _builtin_exec(self, command):
        """Execute shell command (simulated)."""
        return {"output": f"Executed: {command}"}
    
    def interpret(self, program: ProgramNode) -> Any:
        """Interpret a program AST."""
        result = None
        for statement in program.statements:
            result = self.execute(statement)
            if self.return_value is not None:
                return self.return_value
        return result
    
    def execute(self, node: ASTNode) -> Any:
        """Execute an AST node."""
        if isinstance(node, NumberNode):
            return node.value
        
        elif isinstance(node, StringNode):
            return node.value
        
        elif isinstance(node, IdentifierNode):
            if node.name in self.variables:
                return self.variables[node.name]
            raise NameError(f"Undefined variable: {node.name}")
        
        elif isinstance(node, ListNode):
            return [self.execute(elem) for elem in node.elements]
        
        elif isinstance(node, BinaryOpNode):
            left = self.execute(node.left)
            right = self.execute(node.right)
            
            if node.op == '+':
                return left + right
            elif node.op == '-':
                return left - right
            elif node.op == '*':
                return left * right
            elif node.op == '/':
                return left / right
            elif node.op == '%':
                return left % right
            elif node.op == '==':
                return left == right
            elif node.op == '!=':
                return left != right
            elif node.op == '<':
                return left < right
            elif node.op == '>':
                return left > right
            elif node.op == '<=':
                return left <= right
            elif node.op == '>=':
                return left >= right
            elif node.op == 'and':
                return left and right
            elif node.op == 'or':
                return left or right
        
        elif isinstance(node, UnaryOpNode):
            operand = self.execute(node.operand)
            if node.op == '-':
                return -operand
            elif node.op == 'not':
                return not operand
        
        elif isinstance(node, AssignmentNode):
            value = self.execute(node.value)
            self.variables[node.name] = value
            return value
        
        elif isinstance(node, FunctionCallNode):
            if node.name in self.builtins:
                args = [self.execute(arg) for arg in node.args]
                return self.builtins[node.name](*args)
            elif node.name in self.functions:
                func = self.functions[node.name]
                # Save current scope
                old_vars = self.variables.copy()
                # Set parameters
                for param, arg in zip(func.params, node.args):
                    self.variables[param] = self.execute(arg)
                # Execute function body
                result = None
                self.return_value = None
                for stmt in func.body:
                    result = self.execute(stmt)
                    if self.return_value is not None:
                        ret_val = self.return_value
                        self.return_value = None
                        self.variables = old_vars
                        return ret_val
                self.variables = old_vars
                return result
            else:
                raise NameError(f"Undefined function: {node.name}")
        
        elif isinstance(node, FunctionDefNode):
            self.functions[node.name] = node
            return None
        
        elif isinstance(node, IfNode):
            condition = self.execute(node.condition)
            if condition:
                for stmt in node.then_block:
                    result = self.execute(stmt)
                    if self.return_value is not None:
                        return self.return_value
            else:
                for stmt in node.else_block:
                    result = self.execute(stmt)
                    if self.return_value is not None:
                        return self.return_value
            return None
        
        elif isinstance(node, WhileNode):
            old_in_loop = self.in_loop
            self.in_loop = True
            while self.execute(node.condition):
                self.loop_break = False
                self.loop_continue = False
                for stmt in node.body:
                    self.execute(stmt)
                    if self.loop_break:
                        break
                    if self.loop_continue:
                        continue
                if self.loop_break:
                    break
            self.in_loop = old_in_loop
            return None
        
        elif isinstance(node, ForNode):
            iterable = self.execute(node.iterable)
            old_in_loop = self.in_loop
            self.in_loop = True
            for item in iterable:
                self.variables[node.var] = item
                self.loop_break = False
                self.loop_continue = False
                for stmt in node.body:
                    self.execute(stmt)
                    if self.loop_break:
                        break
                    if self.loop_continue:
                        continue
                if self.loop_break:
                    break
            self.in_loop = old_in_loop
            return None
        
        elif isinstance(node, ReturnNode):
            if node.value:
                self.return_value = self.execute(node.value)
            else:
                self.return_value = None
            return None
        
        elif isinstance(node, PrintNode):
            value = self.execute(node.value)
            print(value)
            return None
        
        elif isinstance(node, BreakNode):
            if self.in_loop:
                self.loop_break = True
            else:
                raise SyntaxError("break outside loop")
            return None
        
        elif isinstance(node, ContinueNode):
            if self.in_loop:
                self.loop_continue = True
            else:
                raise SyntaxError("continue outside loop")
            return None
        
        elif isinstance(node, ProgramNode):
            result = None
            for stmt in node.statements:
                result = self.execute(stmt)
                if self.return_value is not None:
                    return self.return_value
            return result
        
        raise TypeError(f"Unknown node type: {type(node)}")


class KaliLang:
    """Main interface for KaliLang programming language."""
    
    def __init__(self, filesystem=None, network_manager=None):
        self.lexer = None
        self.parser = None
        self.interpreter = Interpreter(filesystem, network_manager)
    
    def run(self, source: str) -> Any:
        """Run KaliLang source code."""
        try:
            # Lexical analysis
            self.lexer = Lexer(source)
            tokens = self.lexer.tokenize()
            
            # Parsing
            self.parser = Parser(tokens)
            program = self.parser.parse()
            
            # Interpretation
            return self.interpreter.interpret(program)
        
        except Exception as e:
            raise RuntimeError(f"Runtime error: {e}")
    
    def run_file(self, filepath: str) -> Any:
        """Run KaliLang from a file."""
        with open(filepath, 'r') as f:
            source = f.read()
        return self.run(source)


# Convenience function
def run_kalilang(source: str, filesystem=None, network_manager=None) -> Any:
    """Run KaliLang code."""
    lang = KaliLang(filesystem, network_manager)
    return lang.run(source)
