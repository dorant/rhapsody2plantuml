/********************************************
sbs2xml

Based on:
    https://github.com/jruffin/sbs2xml-conv
    SBS to XML simple converter.
    Author: Przemyslaw Wirkus

Improvements done:
  - Handling { CGIClass
  - C++ CMake

Known issues:
  - m_direction = ' ';
  <m_direction></m_direction>

********************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int yyparse();
extern int yydebug;

void yyerror(const char* str)
{
    printf("%s", str);
}



char* strip_string_quotes(char* str)
{
    const int len = strlen(str);
    str[len - 1] = '\0';
    return str + 1;
}

// Creates a copy of the string with unescaped strings (backslashes removed).
char* process_string_literal(const char* str)
{
    char* output = (char*) malloc(strlen(str)+1);
    const char* inPtr = str;
    char* outPtr = output;
    
    // Skip the initial "
    if (*inPtr == '\"') {
        ++inPtr;
    }
    
    while (*inPtr != '\0')
    {
        // If we encounter a backslash and we're not at the end of the string:
        // skip it and blindly write the character directly after it
        if ( (*inPtr == '\\') && (*(inPtr+1) != '\0') ) {
            ++inPtr;
        }
        
        // Copy the char
        *outPtr++ = *inPtr++;
    }
    
    // Remove the final "
    if ( (outPtr > output) && (*(outPtr-1) == '\"') ) {
        --outPtr;
    }
    
    // Terminate the modified string.
    *outPtr = '\0';
    
    return output;
}

void print_xml_special_characters(const char* str)
{
    const int len = strlen(str);
    for (int i = 0; i < len; i++)
    {
        const char c = str[i];
        switch (c)
        {
            case '"':  printf("&quot;"); break;
            case '&':  printf("&amp;");  break;
            case '\'': printf("&apos;"); break;
            case '<':  printf("&lt;");   break;
            case '>':  printf("&gt;");   break;
            default: printf("%c", c);
        }
    }
}

void print_text_element(const char* element, const char* content) {
    char* unescapedStr = process_string_literal(content);
    printf("<%s>", element);
    print_xml_special_characters(unescapedStr);
    printf("</%s>\n", element);
    free(unescapedStr);
}

// Creates new string with prefix
char* string_add_front(const char* prefix, const char* delimiter, const char* str)
{
    const int total_len = strlen(prefix) + strlen(str) + strlen(delimiter) + 1;
    char* result = (char*)malloc(total_len * sizeof(char));
    strcpy(result, prefix);
    strcat(result, delimiter);
    strcat(result, str);
    return result;
}


int main(int argc, char *argv[])
{
    int ret = yyparse();
    return ret;
}
