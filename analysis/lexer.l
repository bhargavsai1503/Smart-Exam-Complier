%{
/*
 * Lexer Specification for Question Paper Analysis
 * Tokenizes question paper text into meaningful tokens
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "y.tab.h"

int line_num = 1;
char token_buffer[1024];
FILE *token_file;

void write_token(const char* type, const char* value) {
    if (token_file) {
        fprintf(token_file, "%s: %s\n", type, value);
    }
}
%}

%option noyywrap
%option case-insensitive

DIGIT       [0-9]
LETTER      [a-zA-Z]
SPACE       [ \t]
NEWLINE     [\n\r]

%%

    /* Header Tokens */
"Time"{SPACE}*":"{SPACE}*{DIGIT}+{SPACE}*(hours?|hrs?|minutes?|mins?)  {
    write_token("TIME", yytext);
    yylval.str = strdup(yytext);
    return TIME;
}

("Total"|"Maximum"|"Max"){SPACE}*"Marks"?{SPACE}*":"{SPACE}*{DIGIT}+  {
    write_token("TOTAL_MARKS", yytext);
    yylval.str = strdup(yytext);
    return TOTAL_MARKS;
}

("Syllabus"|"Subject"|"Course"){SPACE}*":"{SPACE}*[^\n]+  {
    write_token("SYLLABUS", yytext);
    yylval.str = strdup(yytext);
    return SYLLABUS;
}

    /* Question Number Tokens */
("Q"|"Question"){SPACE}*\.?{SPACE}*{DIGIT}+[\.\)]?  {
    write_token("QNUM", yytext);
    yylval.str = strdup(yytext);
    return QNUM;
}

{DIGIT}+[\.\)]  {
    write_token("QNUM", yytext);
    yylval.str = strdup(yytext);
    return QNUM;
}

    /* Sub-question Tokens */
[a-z][\.\)]  {
    write_token("SUBQ", yytext);
    yylval.str = strdup(yytext);
    return SUBQ;
}

[ivxIVX]+[\.\)]  {
    write_token("SUBQ", yytext);
    yylval.str = strdup(yytext);
    return SUBQ;
}

    /* Marks Tokens */
[\[\(]{DIGIT}+[\]\)]  {
    write_token("MARKS", yytext);
    yylval.num = atoi(yytext + 1);
    return MARKS;
}

    /* Difficulty Keywords */
"define"|"state"|"list"|"identify"|"name"|"mention"  {
    write_token("EASY_KW", yytext);
    yylval.str = strdup(yytext);
    return EASY_KW;
}

"explain"|"prove"|"derive"|"compare"|"discuss"|"describe"|"illustrate"  {
    write_token("MEDIUM_KW", yytext);
    yylval.str = strdup(yytext);
    return MEDIUM_KW;
}

"design"|"construct"|"develop"|"implement"|"optimize"|"synthesize"|"analyze"|"evaluate"  {
    write_token("HARD_KW", yytext);
    yylval.str = strdup(yytext);
    return HARD_KW;
}

    /* Section markers */
"Section"{SPACE}*[A-Z]  {
    write_token("SECTION", yytext);
    yylval.str = strdup(yytext);
    return SECTION;
}

"OR"  {
    write_token("OR", yytext);
    return OR;
}

    /* General text */
{LETTER}+  {
    write_token("WORD", yytext);
    yylval.str = strdup(yytext);
    return WORD;
}

{DIGIT}+  {
    write_token("NUMBER", yytext);
    yylval.num = atoi(yytext);
    return NUMBER;
}

    /* Punctuation */
[.,;:!?]  {
    write_token("PUNCT", yytext);
    return yytext[0];
}

    /* Whitespace and newlines */
{SPACE}+  {
    /* Ignore spaces */
}

{NEWLINE}  {
    line_num++;
    return NEWLINE;
}

    /* Catch-all for other characters */
.  {
    /* Ignore other characters */
}

%%

int main(int argc, char **argv) {
    char token_filename[256];
    char ast_filename[256];
    
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <session_id>\n", argv[0]);
        return 1;
    }
    
    snprintf(token_filename, sizeof(token_filename), "../output/%s_tokens.txt", argv[1]);
    snprintf(ast_filename, sizeof(ast_filename), "../output/%s_ast.json", argv[1]);
    
    token_file = fopen(token_filename, "w");
    if (!token_file) {
        fprintf(stderr, "Error: Cannot create token file\n");
        return 1;
    }
    
    printf("Starting lexical analysis...\n");
    yyparse();
    
    fclose(token_file);
    printf("Tokens written to %s\n", token_filename);
    printf("AST written to %s\n", ast_filename);
    
    return 0;
}
