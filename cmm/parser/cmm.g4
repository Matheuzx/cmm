grammar cmm;

start : func* EOF
      ;

func : 'def' name=ID '(' args? ')'  (statms | lambda)
     ;

args : ID (',' ID)*
     ;

statms : '{' statm* '}'
       | statm
       ;

lambda : ('=>' | '->') expr ';' ;

statm : assignment ';'                                                # assign
      | TYPES assignment ';'                                          # attr
      | 'print' expr ';'                                              # print
      | 'if' cond=expr then=statms ('else' otherwise=statms)?         # if
      | 'while' cond=expr statms                                      # while
      | 'switch' cond=expr '{' switch_case+ switch_default? '}'       # switch
      | 'for' TYPES assignment ';' cond=expr ';' assignment statms    # for
      | 'return' expr ';'                                             # return
      ;

assignment : ID '=' expr
     ;

switch_case: ('case' TYPES_VALUES ':' statm ('break;'?))
     ;

switch_default: ('default:' statm ('break;'?))
     ;

call : name=ID '(' exprs? ')'
     ;

exprs : expr (',' expr)*
      ;

expr : left=summ (op=('>'|'<'|'>='|'<='|'=='|'!='|'&&'|'||') right=expr)*
     ;

summ : left=mult (op=('+'|'-') right=summ)*
     ;

mult : left=atom (op=('*'|'/') right=mult)*
     ;

atom : '(' expr ')'
     | TYPES_VALUES
     | ID
     | call
     ;

TYPES : 'int' | 'float' | 'bool';
TYPES_VALUES: INT | FLOAT | BOOL;
ID : [a-zA-Z]+[0-9a-zA-Z]*;
INT : [0-9]+;
FLOAT : INT[.]INT;
BOOL : 'true' | 'false';
WS : [ \r\n\t]+ -> skip;
