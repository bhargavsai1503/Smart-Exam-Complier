/*
 * compiler/parser.y
 * Grammar for the Q-Verifier DSL (input.qp)
 * Builds the Abstract Syntax Tree (AST)
 */

%{
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include "ast.h"
    #include "ast_helpers.h" // Our new helper functions

    // External functions from lexer
    extern int yylex();
    extern FILE* yyin;

    void yyerror(const char *s);

    // The root of our AST, which main.c will use
    ASTNode* root = NULL;
%}

/* * %union defines all the data types our grammar rules can hold.
 */
%union {
    int ival;            // For T_NUMBER
    char *sval;          // For T_STRING
    QuestionNode* q_node;  // For a single 'question' rule
    QuestionNode* q_list;  // For 'question_list_body'
    ASTNode* ast_node;     // For 'header' and 'paper'
}

/* --- Token Definitions (from lexer.l) --- */
%token T_HEADER_START T_HEADER_END T_QUESTION_LIST_START T_QUESTION_LIST_END
%token T_QUESTION_START T_QUESTION_END
%token T_SUBJECT T_TOTAL_MARKS T_TOTAL_TIME T_SYLLABUS_PATH
%token T_Q_TEXT T_Q_MARKS
%token T_COLON
%token <ival> T_NUMBER  /* Token T_NUMBER holds an integer */
%token <sval> T_STRING  /* Token T_STRING holds a string */

/* --- Grammar Rule Type Definitions --- */
/* Tells Bison what type from the %union a rule returns */
%type <ast_node> paper header
%type <ival> marks_rule time_rule q_marks_rule
%type <sval> subject_rule syllabus_rule q_text_rule
%type <q_list> question_list question_list_body
%type <q_node> question

%%

/* --- Grammar Rules (The CFG) --- */

/* * Rule 1: A 'paper' is a 'header' followed by a 'question_list'
 */
paper: header question_list
    {
        // $1 is the ASTNode from 'header', $2 is the QuestionNode* from 'question_list'
        $1->questions = $2; // Link the question list to the AST root
        $$ = $1;            // The final AST is the header node
        root = $$;          // Set the global AST root for main.c
    }
    ;

/* * Rule 2: A 'header' is the block of 4 header rules
 */
header: T_HEADER_START subject_rule marks_rule time_rule syllabus_rule T_HEADER_END
    {
        // $2=subject, $3=marks, $4=time, $5=syllabus
        // Create the root ASTNode
        $$ = create_ast_node($2, $3, $4, $5, NULL);
    }
    ;

/* Rules for key-value pairs in the header */
subject_rule: T_SUBJECT T_COLON T_STRING 
    { $$ = $3; } /* Return the string value */
    ;
marks_rule: T_TOTAL_MARKS T_COLON T_NUMBER 
    { $$ = $3; } /* Return the integer value */
    ;
time_rule: T_TOTAL_TIME T_COLON T_NUMBER   
    { $$ = $3; } /* Return the integer value */
    ;
syllabus_rule: T_SYLLABUS_PATH T_COLON T_STRING 
    { $$ = $3; } /* Return the string value */
    ;


/*
 * Rule 3: A 'question_list' is a body of questions
 */
question_list: T_QUESTION_LIST_START question_list_body T_QUESTION_LIST_END
    {
        $$ = $2; // Pass up the completed list
    }
    ;

/* This is how we build a linked list */
question_list_body: /* empty */
    {
        $$ = NULL; // Base case: no questions
    }
    | question_list_body question
    {
        // $1 is the existing list, $2 is the new question node
        $$ = append_question($1, $2); // Add new question to end of list
    }
    ;

/*
 * Rule 4: A 'question' is its text and marks
 */
question: T_QUESTION_START q_text_rule q_marks_rule T_QUESTION_END
    {
        // $2 is the text string, $3 is the marks integer
        $$ = create_question_node($2, $3); // Create the question node
    }
    ;

/* Rules for key-value pairs in a question */
q_text_rule: T_Q_TEXT T_COLON T_STRING  
    { $$ = $3; }
    ;
q_marks_rule: T_Q_MARKS T_COLON T_NUMBER  
    { $$ = $3; }
    ;

%%

/* --- C Code Footer --- */

/* Error handling function */
void yyerror(const char *s) {
    /* * We'd write this to a 'parser_errors.txt' in a real app,
     * but for now, stderr is fine.
     */
    extern int yylineno;
    fprintf(stderr, "Parse Error on line %d: %s\n", yylineno, s);
}