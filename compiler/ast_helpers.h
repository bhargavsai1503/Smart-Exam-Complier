/*
 * compiler/ast_helpers.h
 * Prototypes for AST helper functions (creation, traversal, export)
 */

#ifndef AST_HELPERS_H
#define AST_HELPERS_H

#include "ast.h" // Include our data structure definitions

/* --- AST Creation Functions (called by parser) --- */

ASTNode* create_ast_node(char* subject, int marks, int time, char* syllabus_path, QuestionNode* questions);
QuestionNode* create_question_node(char* text, int marks);
QuestionNode* append_question(QuestionNode* list_head, QuestionNode* new_question);
void free_ast(ASTNode* root);


/* --- Web Output Functions (called by main.c) --- */

// Phase 2: Generates the ast.dot file for the web UI
void export_ast_to_dot(ASTNode* root, const char* filepath);

#endif // AST_HELPERS_H