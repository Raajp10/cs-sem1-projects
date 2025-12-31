# Project 3 – Symbol Table Generation and Abstract Syntax Tree Construction
**CS 51530 – Compiler Construction**  


---

# 1. Overview

This project extends the compiler front-end from Project 2 by implementing full semantic analysis, symbol table construction, and Abstract Syntax Tree (AST) generation based on *Engineering a Compiler (3rd Edition)*.

The implementation adds:

- Symbol table generation with nested scopes  
- Minimal AST construction (no declarations in the tree)  
- Static type checking with widening (int → long → double)  
- Function definitions and calls with inferred return types  
- An automated test harness that runs all valid and invalid programs  

---

## 1.1 Symbol Table Generation (Chapter 4)

- Supports **nested scopes**:
  - Global scope  
  - Function scope  
  - Block scope  
- Tracks:
  - Variable names  
  - Types  
  - Offsets  
  - Scope hierarchy  
- Detects:
  - Duplicate declarations  
  - Use of undeclared variables  
- Assigns memory offsets:
  - `int` → 4 bytes  
  - `long` → 8 bytes  
  - `double` → 8 bytes  
  - `bool` → 4 bytes  
  - `char` → 1 byte  

---

## 1.2 Minimal AST Construction (Chapter 5)

- Clean minimal AST (**declarations are not AST nodes**)  
- Program node is **flat**: one child per executable statement  
- AST includes:
  - Assignment nodes  
  - Function definitions  
  - Function call statements  
  - If-expressions  
  - Arithmetic and boolean operations  
  - Unary operations  
  - Literals and identifiers  

---

## 1.3 Static Type Checking

- Widening chain: `int → long → double`  
- Assignment requires RHS **widenable** to LHS  
- Comparison requires operands of identical type  
- Boolean operators (`andalso`, `orelse`) require `bool` operands  
- If-expression branches must be type-compatible  
- Function return types inferred from body expression  

---

## 1.4 Function Support

- Functions with typed parameters  
- Function-scope symbol tables  
- Function return type inference  
- Functions stored in global scope  
- Function call validation with type checking  

---

# 2. Repository Structure

```
Project3/
│
├── parser.py
├── scanner.py
├── token_definitions.py
├── ast_nodes.py
├── symbol_table.py
├── main.py
│
└── tests/
    ├── valid/
    └── invalid/
```

---

# 3. How to Run

### Run a single program:
```
python3 parser.py file.min
```

### Run the full test suite:
```
python3 main.py
```

This prints:
- Symbol tables (all scopes)  
- AST  
- PASS/FAIL results  

---

# 4. Grammar Supported

```
Program      → StmtList EOF
StmtList     → Stmt StmtList | ε

Stmt         → DeclareStmt
             | AssignStmt
             | FunctionDefStmt
             | FunctionCallStmt
             | Block

Block        → '{' StmtList '}'
...
```

---

# 5. Symbol Table Design

- Hierarchical linked scopes  
- Stores: name, type, offset  
- Lookup searches parent scopes  
- Functions stored in global scope with inferred type  

---

# 6. AST Design

- Minimal AST  
- Declarations excluded  
- Contains executable structure only  

---

# 7. Static Type Checking

- Widening applied to arithmetic  
- Assignment validation  
- Boolean/comparison operators enforced  
- If-expr result type widened between branches  

---

# 8. Testing

- Valid programs must parse and generate AST + symbol tables  
- Invalid programs must produce errors  
- Automated via `main.py`  

---

# 9. AI Usage Disclosure

AI assistance was used **only for documentation clarity, grammar improvement, and conceptual explanation**.  
All implementation code was manually written and verified by the student.

---

# 10. Summary

This Project 3 implementation provides a complete semantic front-end for the mini-language used in CS 51530:

- A recursive-descent parser based on Engineering a Compiler (3rd ed.)  
- Symbol tables with nested scopes, offsets, and error checking  
- A minimal AST capturing the essential program structure  
- Static type checking with widening and inferred function return types  
- A test harness that prints AST + symbol tables and validates all input programs  

This front-end now serves as a foundation for future stages such as intermediate code generation, optimization, and final code emission.

## 11. Group Roles
Parikshith Saraswathi – AST Nodes and Symbol table Theory  
Raaj Patel – Parser Implementation  
Jeevana Shruthi – Testing & Documentation