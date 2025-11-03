/*
 * compiler/ast.h
 * Defines the core Abstract Syntax Tree (AST) structures.
 */

#ifndef AST_H
#define AST_H

// As specified in the RFD
typedef struct QuestionNode {
    char* text;
    int marks;
    
    // --- Phase 3 Annotations (will be filled in later) ---
    char* difficulty;     // "Easy", "Medium", "Hard"
    int estimated_time;   // in minutes
    char* syllabus_topic; // "Trees", "Sorting", "N/A"
    int status_flag;      // 0=OK, 1=DUPLICATE, 2=OUT_OF_SYLLABUS
    char* blooms_level;   // "Remembering", "Analyzing", etc. (From LLM Ideation)
    
    struct QuestionNode* next; // for linked list
} QuestionNode;

typedef struct ASTNode {
    char* subject;
    int total_marks;
    int total_time;
    char* syllabus_path;
    
    QuestionNode* questions; // Head of the question list
} ASTNode;

#endif // AST_H