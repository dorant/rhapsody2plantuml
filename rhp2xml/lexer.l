%option noyywrap

%{

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "parser.hpp"

%}

D                         [0-9]
E                         [Ee][+-]?{D}+

INT                       {D}+
FLOAT                     {D}+"."{D}+({E})?
GUID                      [a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}
GUID_STR                  "GUID"
OLDID_STR                 "OLDID"
TEXTRTF_STR               "_textRTF"
RPY_ARCHIVE_VERSION_NO    {D}+"."{D}+"."{D}+
RPY_ARCHIVE_VERSION_STR   "I-Logix-RPY-Archive version"
CPP_STR                   "C++"
RPY_RAW_CONTAINER_STR     "IRPYRawContainer"
SIZE                      "size"
VALUE                     "value"
STRING_LITERAL            \"(\\.|[^\\"])*\"
NAME                      [a-zA-Z0-9_]+
CGTIME                    {INT}"."{INT}"."{INT}::{INT}:{INT}:{INT}
OBRACE                    \{
EBRACE                    \}
TYPE_CHAR                 "'"[FT ]{1}"'"

%option yylineno

%%

{INT}                           {
                                    yylval.str_int = strdup(yytext);
                                    return _INT;
                                }

{FLOAT}                         {
                                    yylval.str_float = strdup(yytext);
                                    return _FLOAT;
                                }

{GUID}                          {
                                    yylval.str_string_literal = strdup(yytext);
                                    return _GUID;
                                }

{GUID_STR}                      return _GUID_STR;

{OLDID_STR}                     return _OLDID_STR;

{TEXTRTF_STR}                   return _TEXTRTF_STR;

{RPY_RAW_CONTAINER_STR}         return _RPY_RAW_CONTAINER_STR;

{SIZE}                          return _SIZE;

{VALUE}                         return _VALUE;

{STRING_LITERAL}                {
                                    yylval.str_string_literal = strdup(yytext);
                                    return _STRING_LITERAL;
                                }

{RPY_ARCHIVE_VERSION_NO}        return _RPY_ARCHIVE_VERSION_NO;

{RPY_ARCHIVE_VERSION_STR}       return _RPY_ARCHIVE_VERSION_STR;

{CPP_STR}                       return _CPP_STR;

{NAME}                          {
                                    yylval.str_name = strdup(yytext);
                                    return _NAME;
                                }

{CGTIME}                        {
                                    yylval.str_cgtime = strdup(yytext);
                                    return _CGTIME;
                                }

{OBRACE}                        return _OBRACE;

{EBRACE}                        return _EBRACE;

{TYPE_CHAR}                     {
                                    yylval.str_type_char = strdup(yytext);
                                    return _TYPE_CHAR;
                                }

[-=;]                           return *yytext;

[ \t\n\']+                      /* ignore whitespace */

%%
