import os


# --- Token types ---
TT_NUM    = "NUM"
TT_OP     = "OP"
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_END    = "END"

# --- Tokeniser ---

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

# --- AST node constructors  (plain dicts — no classes) ---

def node_num(value: float) -> dict:
    return {"kind": "num", "value": value}

def node_binop(op: str, left: dict, right: dict) -> dict:
    return {"kind": "binop", "op": op, "left": left, "right": right}

def node_neg(operand: dict) -> dict:
    return {"kind": "neg", "operand": operand}

# --- AST → tree string ---

def format_value(v: float) -> str:

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

# --- Evaluator ---

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


def parse(tokens: list[tuple[str, str]]) -> dict:
    """
    REFACTORED: This replaces the '_Parser' class. 
    We use a dictionary 'ctx' to track the position instead of 'self.pos'.
    """
    ctx = {"pos": 0}

    def peek(): return tokens[ctx["pos"]]
    def consume():
        tok = tokens[ctx["pos"]]
        ctx["pos"] += 1
        return tok
    def expect(ttype):
        tok = consume()
        if tok[0] != ttype: raise ValueError(f"Expected {ttype}, got {tok}")
        return tok

    # Grammar rules are now nested functions (no 'self' needed)
    def parse_expr():
        left = parse_term()
        while peek()[0] == TT_OP and peek()[1] in '+-':
            op  = consume()[1]
            right = parse_term()
            left  = node_binop(op, left, right)
        return left

    def parse_term():
        left = parse_implicit()
        while peek()[0] == TT_OP and peek()[1] in '*/':
            op = consume()[1]
            right = parse_implicit()
            left = node_binop(op, left, right)
        return left

    def parse_implicit():
        left = parse_unary()
        while peek()[0] in (TT_NUM, TT_LPAREN):
            right = parse_unary()
            left = node_binop('*', left, right)
        return left

    def parse_unary():
        tt, val = peek()
        if tt == TT_OP and val == '-':
            consume()
            return node_neg(parse_unary())
        if tt == TT_OP and val == '+':
            raise ValueError("Unary '+' is not supported")
        return parse_primary()

    def parse_primary():
        tt, val = peek()
        if tt == TT_NUM:
            consume()
            return node_num(float(val))
        if tt == TT_LPAREN:
            consume()
            node = parse_expr()
            expect(TT_RPAREN)
            return node
        raise ValueError(f"Unexpected token: {tt}:{val!r}")

    ast = parse_expr()
    if peek()[0] != TT_END: raise ValueError("Unexpected token after expression")
    return ast
           

# --- Per-expression processing ---

def process_expression(expr: str) -> dict:
    res = {"input": expr, "tree": "ERROR", "tokens": "ERROR", "result": "ERROR"}
    try:
        toks = tokenise(expr)
        parts = []
        for tt, val in toks:
            parts.append("[END]" if tt == TT_END else f"[{tt}:{val}]")
        res["tokens"] = " ".join(parts)

        ast = parse(toks)
         
        res["tree"] = tree_to_str(ast)
        res["result"] = eval_node(ast)
    except (ValueError, ZeroDivisionError):
        pass
    return res


# --- Output formatting ---

def format_result_value(v) -> str:
    if v == "ERROR":
        return "ERROR"
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return f"{v:.4f}"
    return str(v)


def format_block(d: dict) -> str:
    lines = [
        f"Input:  {d['input']}",
        f"Tree:   {d['tree']}",
        f"Tokens: {d['tokens']}",
        f"Result: {format_result_value(d['result'])}",
    ]
    return "\n".join(lines)



# --- Public interface ---

def evaluate_file(input_path: str) -> list[dict]:

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

results = evaluate_file('sample_input.txt')

for res in results:
    print(f"Input: {res['input']}")
    print(f"Tokens: {res['tokens']}")
    print(f"Tree: {res['tree']}")
    print(f"Result: {format_result_value(res['result'])}")
    print("----------------------------------------")

print("Output written to output.txt")
