/*
 * semantic.c - Optional C semantic analysis integration for SmartExam Compiler
 * You can compile this via: gcc -c semantic.c
 * Intended for use in the Yacc actions or as a validation utility
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Example structure for a parsed question
typedef struct Question {
    int number;
    char text[256];
    int marks;
    char difficulty[16];
    struct Question *next;
} Question;

// Validate sum of marks (very basic example)
int validate_marks(Question *head, int declared_total) {
    int sum = 0;
    Question *ptr = head;
    while (ptr) {
        sum += ptr->marks;
        ptr = ptr->next;
    }
    if (sum == declared_total) {
        printf("PASS: Marks sum matches declared total (%d)\n", declared_total);
        return 1;
    } else {
        printf("FAIL: Marks sum %d does not match declared total %d\n", sum, declared_total);
        return 0;
    }
}

// Classify difficulty (very basic, keyword-based)
const char* classify_difficulty(const char *text) {
    if (strstr(text, "define") || strstr(text, "state"))
        return "EASY";
    if (strstr(text, "explain") || strstr(text, "prove"))
        return "MEDIUM";
    if (strstr(text, "design") || strstr(text, "construct") || strstr(text, "optimize"))
        return "HARD";
    return "MEDIUM"; // Default
}

// Example usage
int main() {
    Question q1 = {1, "Define compiler and interpreter.", 10, "", NULL};
    Question q2 = {2, "Explain the phases of compiler design.", 10, "", NULL};
    Question q3 = {3, "Construct DFA for (a|b)*abb.", 12, "", NULL};
    q1.next = &q2;
    q2.next = &q3;
    int declared_total = 32;
    validate_marks(&q1, declared_total);
    printf("Q1 difficulty: %s\n", classify_difficulty(q1.text));
    printf("Q3 difficulty: %s\n", classify_difficulty(q3.text));
    return 0;
}