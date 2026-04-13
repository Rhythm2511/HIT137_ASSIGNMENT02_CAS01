# Token types
TT_NUM    = "NUM"
TT_OP     = "OP"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_END    = "END"

# Tokeniser

def tokenise(expr: str) -> list[tuple[str, str]]:
    tokens = []
    i = 0
    while i < len(expr):
        ch = expr[i]

        # Skip whitespace
        if ch.isspace():
            i += 1
            continue

        # Numeric literal (integer or decimal)
        if ch.isdigit() or (ch == '.' and i + 1 < len(expr) and expr[i + 1].isdigit()):
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append((TT_NUM, expr[i:j]))
            i = j
            continue

        # Operators
        if ch in '+-*/':
            tokens.append((TT_OP, ch))
            i += 1
            continue

        # Parentheses
        if ch == '(': # Corrected: removed 'p' and fixed indentation
            tokens.append((TT_LPAREN, '('))
            i += 1
            continue
        if ch == ')':
            tokens.append((TT_RPAREN, ')'))
            i += 1
            continue

        raise ValueError(f"Unexpected character: {ch!r}")

    tokens.append((TT_END, ""))
    return tokens


def format_tokens(tokens: list[tuple[str, str]]) -> str:
    """
    Format a token list as the output string, e.g.
    [NUM:3] [OP:+] [NUM:5] [END]
    """
    parts = []
    for tt, val in tokens:
        if tt == TT_END:
            parts.append("[END]")
        else:
            parts.append(f"[{tt}:{val}]")
    return " ".join(parts)

# AST node constructors  (plain dicts — no classes)

def node_num(value: float) -> dict:
    return {"kind": "num", "value": value}

def node_binop(op: str, left: dict, right: dict) -> dict:
    return {"kind": "binop", "op": op, "left": left, "right": right}

def node_neg(operand: dict) -> dict:
    return {"kind": "neg", "operand": operand}

# AST → tree string

def format_value(v: float) -> str:
    """Render a float: no decimal if whole, otherwise strip trailing zeros."""
    if v == int(v):
        return str(int(v))
    s = f"{v:.10f}".rstrip('0').rstrip('.')
    return s


def tree_to_str(node: dict) -> str:
    if node["kind"] == "num":
        return format_value(node["value"])
    if node["kind"] == "neg":
        return f"(neg {tree_to_str(node['operand'])})"
    if node["kind"] == "binop":
        return f"({node['op']} {tree_to_str(node['left'])} {tree_to_str(node['right'])})"
    raise ValueError(f"Unknown node kind: {node['kind']}")

# Evaluator


def eval_node(node: dict) -> float:
    if node["kind"] == "num":
        return node["value"]
    if node["kind"] == "neg":
        return -eval_node(node["operand"])
    if node["kind"] == "binop":
        left  = eval_node(node["left"])
        right = eval_node(node["right"])
        op    = node["op"]
        if op == '+': return left + right
        if op == '-': return left - right
        if op == '*': return left * right
        if op == '/':
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
    raise ValueError(f"Unknown node kind: {node['kind']}")



class _Parser:
    """Internal stateful parser; exposes only plain-function wrappers outside."""

    def __init__(self, tokens: list[tuple[str, str]]):
        self.tokens = tokens
        self.pos    = 0

    # helpers

    def peek(self) -> tuple[str, str]:
        return self.tokens[self.pos]

    def consume(self) -> tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, ttype: str) -> tuple[str, str]:
        tok = self.consume()
        if tok[0] != ttype:
            raise ValueError(f"Expected {ttype}, got {tok}")
        return tok

    # grammar rules

    def parse_expr(self) -> dict:
        """expr → term (('+' | '-') term)*"""
        left = self.parse_term()
        while self.peek()[0] == TT_OP and self.peek()[1] in '+-':
            op  = self.consume()[1]
            right = self.parse_term()
            left  = node_binop(op, left, right)
        return left

    def parse_term(self) -> dict:
        """term → implicit (('*' | '/') implicit)*"""
        left = self.parse_implicit()
        while self.peek()[0] == TT_OP and self.peek()[1] in '*/':
            op    = self.consume()[1]
            right = self.parse_implicit()
            left  = node_binop(op, left, right)
        return left

    def parse_implicit(self) -> dict:
        """implicit → unary (unary)*  — implicit multiplication"""
        left = self.parse_unary()
        # A following unary can start with '-' (OP) or NUM or LPAREN
        while self._starts_unary():
            right = self.parse_unary()
            left  = node_binop('*', left, right)
        return left

    def _starts_unary(self) -> bool:
        """
        True if the next token can begin a NEW implicit-multiplication operand.
        We do NOT include '-' here: a '-' following a complete primary/unary
        is always binary subtraction at the expr level, never implicit mult.
        This prevents '10 - 3' from being mis-parsed as '10 * (neg 3)'.
        """
        tt, _ = self.peek()
        return tt in (TT_NUM, TT_LPAREN)

    def parse_unary(self) -> dict:
        """unary → '-' unary  |  primary"""
        tt, val = self.peek()
        if tt == TT_OP and val == '-':
            self.consume()
            operand = self.parse_unary()
            return node_neg(operand)
        if tt == TT_OP and val == '+':
            raise ValueError("Unary '+' is not supported")
        return self.parse_primary()

    def parse_primary(self) -> dict:
        """primary → NUM  |  '(' expr ')'"""
        tt, val = self.peek()
        if tt == TT_NUM:
            self.consume()
            return node_num(float(val))
        if tt == TT_LPAREN:
            self.consume()          # consume '('
            node = self.parse_expr()
            self.expect(TT_RPAREN)  # consume ')'
            return node
        raise ValueError(f"Unexpected token: {tt}:{val!r}")


def parse(tokens: list[tuple[str, str]]) -> dict:
    """
    Parse a token list into an AST dict.
    Raises ValueError if the expression is syntactically invalid.
    """
    parser = _Parser(tokens)
    ast    = parser.parse_expr()
    tt, _  = parser.peek()
    if tt != TT_END:
        raise ValueError(f"Unexpected token after expression: {parser.peek()}")
    return ast

# Per-expression processing

def process_expression(expr: str) -> dict:
    """
    Tokenise, parse, and evaluate a single expression string.
    Returns a dict with keys: input, tree, tokens, result.
    """
    result_dict = {
        "input":  expr,
        "tree":   "ERROR",
        "tokens": "ERROR",
        "result": "ERROR",
    }

    try:
        toks = tokenise(expr)
    except ValueError:
        return result_dict

    result_dict["tokens"] = format_tokens(toks)

    try:
        ast    = parse(toks)
        result_dict["tree"] = tree_to_str(ast)
        value  = eval_node(ast)
        result_dict["result"] = value
    except (ValueError, ZeroDivisionError):
        result_dict["tree"]   = "ERROR"
        result_dict["result"] = "ERROR"

    return result_dict


# Output formatting

def format_result_value(v) -> str:
    """Format the result value for output.txt."""
    if v == "ERROR":
        return "ERROR"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:.4f}"
    return str(v)


def format_block(d: dict) -> str:
    """Format one expression's result dict into the four-line output block."""
    lines = [
        f"Input:  {d['input']}",
        f"Tree:   {d['tree']}",
        f"Tokens: {d['tokens']}",
        f"Result: {format_result_value(d['result'])}",
    ]
    return "\n".join(lines)



# Public interface

def evaluate_file(input_path: str) -> list[dict]:
    """
    Read expressions from input_path (one per line), evaluate each,
    write results to output.txt in the same directory as input_path,
    and return a list of result dicts.
    """
    input_path = os.path.abspath(input_path)
    output_path = os.path.join(os.path.dirname(input_path), "output.txt")

    with open(input_path, "r", encoding="utf-8") as fh:
        lines = fh.readlines()

    results = []
    blocks  = []

    for raw_line in lines:
        expr = raw_line.rstrip("\n")
        stripped = expr.strip()
        if not stripped:
            continue
        d = process_expression(stripped)
        d["input"] = stripped
        results.append(d)
        blocks.append(format_block(d))

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(blocks))
        if blocks:
            fh.write("\n")

    return results
