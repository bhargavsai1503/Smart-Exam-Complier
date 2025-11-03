/*
 * compiler/main.c
 * The main driver for the Q-Verifier C/C++ compiler.
 * This is the executable that app.py calls.
 */

#include <stdio.h>
#include <stdlib.h>
#include "ast.h"
#include "ast_helpers.h"

/* --- External Globals & Functions --- */

// From lexer.l (lex.yy.c)
extern FILE* yyin;
void lexer_init(const char* job_dir);
void lexer_cleanup();

// From parser.y (y.tab.c)
extern int yyparse();
extern ASTNode* root; // The global pointer to our AST root

// Global path to the job directory
char* job_dir_path = NULL;

/*
 * Main Entry Point
 * argv[0] will be "./q_compiler"
 * argv[1] will be the path to the job (e.g., "jobs/d4a5c68e...")
 */
int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <path_to_job_directory>\n", argv[0]);
        return 1;
    }
    
    job_dir_path = argv[1]; // Set global job path
    printf("Compiler worker started for job: %s\n", job_dir_path);

    // --- 1. Set up input file ---
    char input_path[1024];
    sprintf(input_path, "%s/input.qp", job_dir_path);

    yyin = fopen(input_path, "r");
    if (yyin == NULL) {
        fprintf(stderr, "Fatal Error: Cannot open input file %s\n", input_path);
        return 1;
    }

    // --- 2. Run Phase 1 (Lexer) & Phase 2 (Parser) ---
    
    // Initialize the lexer's JSON log
    lexer_init(job_dir_path);
    printf("Phases 1 (Lex) & 2 (Parse) running...\n");

    // yyparse() runs the lexer and parser, building the AST
    // It will return 0 on success
    int parse_result = yyparse();
    
    fclose(yyin); // Close the input file
    
    // Finalize the tokens.json log
    lexer_cleanup();

    if (parse_result != 0 || root == NULL) {
        fprintf(stderr, "Fatal Error: Parsing failed. Check syntax of input.qp.\n");
        return 1; // Exit with an error
    }

    printf("Phases 1 & 2 Complete. AST built successfully.\n");

    // --- 3. Run Phase 2 (Web Output) ---
    char dot_path[1024];
    sprintf(dot_path, "%s/ast.dot", job_dir_path);
    export_ast_to_dot(root, dot_path);
    printf("Phase 2 (Web Output) Complete. ast.dot generated.\n");

    // --- 4. (STUBS for future phases) ---
    // run_phase_3_semantic(root, job_dir_path);
    // IR_List* ir = run_phase_4_ir_gen(root);
    // run_phase_5_optimize(ir, job_dir_path);
    // run_phase_6_code_gen(ir, job_dir_path);
    // printf("Phases 3-6 (STUBS) complete.\n");


    // --- 5. Clean up ---
    free_ast(root); // Free the memory we allocated
    printf("Compiler worker finished for job: %s\n", job_dir_path);

    return 0; // Success!
}