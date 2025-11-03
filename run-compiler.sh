#!/bin/bash

# SmartExam Compiler Build and Run Script
# Compiles Lex and Yacc specifications and runs the compiler

set -e  # Exit on error

echo "=================================="
echo "SmartExam Compiler - Build Script"
echo "=================================="

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <input_file> <session_id>"
    exit 1
fi

INPUT_FILE=$1
SESSION_ID=$2

echo "Input file: $INPUT_FILE"
echo "Session ID: $SESSION_ID"

# Step 1: Generate lexer from Lex specification
echo ""
echo "[1/5] Running Flex (Lex)..."
flex lexer.l

if [ ! -f "lex.yy.c" ]; then
    echo "Error: Flex failed to generate lex.yy.c"
    exit 1
fi
echo "✓ Lexer generated successfully"

# Step 2: Generate parser from Yacc specification
echo ""
echo "[2/5] Running Bison (Yacc)..."
bison -d parser.y

if [ ! -f "parser.tab.c" ]; then
    echo "Error: Bison failed to generate parser.tab.c"
    exit 1
fi
echo "✓ Parser generated successfully"

# Step 3: Compile C code
echo ""
echo "[3/5] Compiling with GCC..."
gcc -o compiler lex.yy.c parser.tab.c -lfl

if [ ! -f "compiler" ]; then
    echo "Error: GCC compilation failed"
    exit 1
fi
echo "✓ Compilation successful"

# Step 4: Run the compiler
echo ""
echo "[4/5] Running compiler on input..."
if [ -f "$INPUT_FILE" ]; then
    ./compiler "$SESSION_ID" < "$INPUT_FILE"
else
    echo "Error: Input file not found: $INPUT_FILE"
    exit 1
fi
echo "✓ Compiler executed successfully"

# Step 5: Verify output files
echo ""
echo "[5/5] Verifying output files..."
TOKEN_FILE="../output/${SESSION_ID}_tokens.txt"
AST_FILE="../output/${SESSION_ID}_ast.json"

if [ -f "$TOKEN_FILE" ]; then
    echo "✓ Token file created: $TOKEN_FILE"
else
    echo "⚠ Warning: Token file not found"
fi

if [ -f "$AST_FILE" ]; then
    echo "✓ AST file created: $AST_FILE"
else
    echo "⚠ Warning: AST file not found"
fi

# Cleanup intermediate files
echo ""
echo "Cleaning up intermediate files..."
rm -f lex.yy.c parser.tab.c parser.tab.h compiler

echo ""
echo "=================================="
echo "Compilation Complete!"
echo "=================================="
