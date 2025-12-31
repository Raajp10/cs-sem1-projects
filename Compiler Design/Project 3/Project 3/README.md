# Mini-Language Parser (Part 2)
## PL/I – Group Project
## Recursive-Descent LL(1) Parser (Engineering a Compiler, 3rd Edition – Chapter 3)

## 1. Overview
This project implements the Part 2 Parser for the Mini-Language using only the techniques allowed in the assignment:

###  Allowed  
- Recursive-descent parser (Chapter 3)  
- LL(1) grammar  
- Predictive parsing using single-token lookahead  
- Grammar rewriting: left recursion removal, left factoring, FIRST/FOLLOW reasoning  
- Recognizing valid vs invalid syntax  
- Logging production rules used  

###  Not Allowed  
- No AST  
- No Symbol Table  
- No Semantic Analysis  
- No Type Checking  
- No IR  
- No Static Analysis  

This parser ONLY checks syntax.

## 2. How to Run the Parser

### Run on a single .min file
```
python3 parser.py tests/valid/v1_simple_declare.min
```

### Run the full test suite
```
python3 run_tests.py
```

Expected output:
```
Running valid tests...
[PASS] v1_simple_declare.min
...
Running invalid tests...
[PASS] i1_missing_semicolon.min
...
```

## 3. Folder Structure
```
project/
  token_definitions.py
  pattern_matcher.py
  scanner.py
  parser.py
  run_tests.py
  tests/
    valid/
    invalid/
  README.md
```

## 4. Grammar Engineering (Chapter 3)

### 4.1 Left-Recursion Removal
Example:
```
arithmetic-expr → arithmetic-expr + term | term
```
Becomes:
```
ArithExpr → Term ArithExpr'
ArithExpr' → '+' Term ArithExpr' | '-' Term ArithExpr' | ε
```

### 4.2 Left Factoring
Used for IdList, ParamList, ArgList, etc.

### 4.3 FIRST/FOLLOW Conflict Fix
Comparison rule was simplified:
```
Comparison → ArithExpr (CompOp ArithExpr)?
```

### 4.4 Statement Selection (FIRST sets)

## 5. Final LL(1) Grammar
(Full grammar omitted here for brevity; same as previous message.)

## 6. Testing Strategy
Valid and invalid programs included in tests/.

## 7. Group Roles
Person 1 – Grammar & Theory  
Person 2 – Parser Implementation  
Person 3 – Testing & Documentation

## 8. AI Assistance Disclosure
Some grammar rewriting and documentation text were generated with ChatGPT. All code and final structure were validated by the group.
