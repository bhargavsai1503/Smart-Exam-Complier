%{
/*
 * Parser Specification for Question Paper Analysis
 * Builds Abstract Syntax Tree from tokenized question paper
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int yylex();
extern int line_num;
void yyerror(const char *s);

FILE *ast_file;
char *session_id;
int indent_level = 0;

typedef struct Question {
    int number;
    char *text;
    int marks;
    char *difficulty;
    struct Question *subquestions;
    struct Question *next;
} Question;

typedef struct Paper {
    char *syllabus;
    int total_marks;
    int time_minutes;
    Question *questions;
} Paper;

Paper *current_paper;

void write_ast(const char *format, ...);
void init_ast_file(const char *sid);
void close_ast_file();

%}

%union {
    int num;
    char *str;
    struct Question *question;
    struct Paper *paper;
}

%token <str> TIME TOTAL_MARKS SYLLABUS QNUM SUBQ WORD EASY_KW MEDIUM_KW HARD_KW SECTION OR
%token <num> MARKS NUMBER
%token NEWLINE

%type <paper> paper header
%type <question> questions question question_text subquestions subquestion

%%

paper:
    header questions {
        $$ = $1;
        $$->questions = $2;
        current_paper = $$;
        
        fprintf(ast_file, "{\n");
        fprintf(ast_file, "  \"type\": \"paper\",\n");
        fprintf(ast_file, "  \"syllabus\": \"%s\",\n", $$->syllabus ? $$->syllabus : "Unknown");
        fprintf(ast_file, "  \"total_marks\": %d,\n", $$->total_marks);
        fprintf(ast_file, "  \"time_minutes\": %d,\n", $$->time_minutes);
        fprintf(ast_file, "  \"questions\": [\n");
        
        Question *q = $2;
        int first = 1;
        while (q) {
            if (!first) fprintf(ast_file, ",\n");
            first = 0;
            
            fprintf(ast_file, "    {\n");
            fprintf(ast_file, "      \"number\": %d,\n", q->number);
            fprintf(ast_file, "      \"text\": \"%s\",\n", q->text ? q->text : "");
            fprintf(ast_file, "      \"marks\": %d,\n", q->marks);
            fprintf(ast_file, "      \"difficulty\": \"%s\"\n", q->difficulty ? q->difficulty : "UNKNOWN");
            fprintf(ast_file, "    }");
            
            q = q->next;
        }
        
        fprintf(ast_file, "\n  ]\n");
        fprintf(ast_file, "}\n");
    }
    ;

header:
    header_items {
        $$ = (Paper*)malloc(sizeof(Paper));
        $$->syllabus = NULL;
        $$->total_marks = 0;
        $$->time_minutes = 0;
        $$->questions = NULL;
    }
    | /* empty */ {
        $$ = (Paper*)malloc(sizeof(Paper));
        $$->syllabus = NULL;
        $$->total_marks = 0;
        $$->time_minutes = 0;
        $$->questions = NULL;
    }
    ;

header_items:
    header_item
    | header_items header_item
    ;

header_item:
    TIME NEWLINE {
        if (current_paper) {
            /* Parse time from string */
            int time_val = 0;
            sscanf($1, "%*[^0-9]%d", &time_val);
            
            if (strstr($1, "hour") || strstr($1, "hr")) {
                time_val *= 60;
            }
            current_paper->time_minutes = time_val;
        }
    }
    | TOTAL_MARKS NEWLINE {
        if (current_paper) {
            int marks = 0;
            sscanf($1, "%*[^0-9]%d", &marks);
            current_paper->total_marks = marks;
        }
    }
    | SYLLABUS NEWLINE {
        if (current_paper) {
            current_paper->syllabus = strdup($1);
        }
    }
    | NEWLINE
    ;

questions:
    question {
        $$ = $1;
    }
    | questions question {
        Question *q = $1;
        while (q->next) q = q->next;
        q->next = $2;
        $$ = $1;
    }
    ;

question:
    QNUM question_text MARKS NEWLINE {
        $$ = (Question*)malloc(sizeof(Question));
        $$->number = atoi($1);
        $$->text = $2->text;
        $$->marks = $3;
        $$->difficulty = $2->difficulty;
        $$->subquestions = NULL;
        $$->next = NULL;
    }
    | QNUM question_text NEWLINE {
        $$ = (Question*)malloc(sizeof(Question));
        $$->number = atoi($1);
        $$->text = $2->text;
        $$->marks = 0;
        $$->difficulty = $2->difficulty;
        $$->subquestions = NULL;
        $$->next = NULL;
    }
    ;

question_text:
    text_elements {
        $$ = (Question*)malloc(sizeof(Question));
        $$->text = strdup("Question text");
        $$->difficulty = strdup("MEDIUM");
    }
    ;

text_elements:
    text_element
    | text_elements text_element
    ;

text_element:
    WORD
    | NUMBER
    | EASY_KW
    | MEDIUM_KW
    | HARD_KW
    | '.'
    | ','
    | ';'
    | ':'
    | '!'
    | '?'
    ;

subquestions:
    subquestion {
        $$ = $1;
    }
    | subquestions subquestion {
        Question *q = $1;
        while (q->next) q = q->next;
        q->next = $2;
        $$ = $1;
    }
    ;

subquestion:
    SUBQ question_text MARKS NEWLINE {
        $$ = (Question*)malloc(sizeof(Question));
        $$->number = 0;
        $$->text = $2->text;
        $$->marks = $3;
        $$->difficulty = $2->difficulty;
        $$->subquestions = NULL;
        $$->next = NULL;
    }
    ;

%%

void yyerror(const char *s) {
    fprintf(stderr, "Parse error at line %d: %s\n", line_num, s);
}

void init_ast_file(const char *sid) {
    char filename[256];
    session_id = strdup(sid);
    snprintf(filename, sizeof(filename), "../output/%s_ast.json", sid);
    ast_file = fopen(filename, "w");
    
    if (!ast_file) {
        fprintf(stderr, "Error: Cannot create AST file\n");
        exit(1);
    }
    
    current_paper = (Paper*)malloc(sizeof(Paper));
    current_paper->syllabus = NULL;
    current_paper->total_marks = 0;
    current_paper->time_minutes = 0;
    current_paper->questions = NULL;
}

void close_ast_file() {
    if (ast_file) {
        fclose(ast_file);
    }
}
