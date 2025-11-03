/*
 * compiler/ast_helpers.c
 * Implementation of AST helper functions.
 * This is where all the 'malloc' logic lives.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ast_helpers.h"

/* --- AST Creation Functions --- */

ASTNode* create_ast_node(char* subject, int marks, int time, char* syllabus_path, QuestionNode* questions) {
    ASTNode* node = (ASTNode*)malloc(sizeof(ASTNode));
    node->subject = strdup(subject);
    node->total_marks = marks;
    node->total_time = time;
    node->syllabus_path = strdup(syllabus_path);
    node->questions = questions;
    
    // Free the strings from the parser, as strdup made copies
    free(subject);
    free(syllabus_path);
    
    return node;
}

QuestionNode* create_question_node(char* text, int marks) {
    QuestionNode* node = (QuestionNode*)malloc(sizeof(QuestionNode));
    node->text = strdup(text);
    node->marks = marks;
    
    // --- Initialize all Phase 3 fields to NULL/0 ---
    node->difficulty = strdup("N/A");
    node->estimated_time = 0;
    node->syllabus_topic = strdup("N/A");
    node->status_flag = 0; // 0 = OK
    node->blooms_level = strdup("N/A");
    node->next = NULL;
    
    // Free the string from the parser
    free(text);
    
    return node;
}

QuestionNode* append_question(QuestionNode* list_head, QuestionNode* new_question) {
    if (list_head == NULL) {
        return new_question; // This is the first question in the list
    }
    
    // Find the end of the list and append
    QuestionNode* current = list_head;
    while (current->next != NULL) {
        current = current->next;
    }
    current->next = new_question;
    
    return list_head; // Return the head of the list
}

/* Stub for recursive AST freeing */
void free_ast(ASTNode* root) {
    if (root == NULL) return;
    // TODO: Free all strings and question nodes
    free(root);
}


/* --- Web Output Functions --- */

// Phase 2: Generates the ast.dot file
void export_ast_to_dot(ASTNode* root, const char* filepath) {
    printf("AST Helper: Exporting AST to %s\n", filepath);
    FILE* f = fopen(filepath, "w");
    if (f == NULL) {
        perror("Failed to open ast.dot");
        return;
    }

    fprintf(f, "digraph AST {\n");
    fprintf(f, "  node [shape=box, style=\"filled\", fillcolor=\"lightblue\"];\n");
    
    // Root node
    fprintf(f, "  root [label=\"Q-Verifier AST\\nSubject: %s\\nMarks: %d\\nTime: %d min\"];\n",
            root->subject, root->total_marks, root->total_time);

    // Question nodes
    QuestionNode* q = root->questions;
    int i = 0;
    while (q != NULL) {
        // Create a unique ID for each question node
        fprintf(f, "  q%d [label=\"Q_TEXT: %s...\\nQ_MARKS: %d\"];\n", 
                i, 
                "TODO: Substring", // Need a helper to show just first 20 chars
                q->marks);
        
        // Link root to question
        fprintf(f, "  root -> q%d;\n", i);
        
        q = q->next;
        i++;
    }
    
    fprintf(f, "}\n");
    fclose(f);
}