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

statm : ID '=' expr ';'                                       # assign
      | types ID '=' expr ';'                                 # attr
      | 'print' expr ';'                                      # print
      | 'if' cond=expr then=statms ('else' otherwise=statms)? # if
      | 'while' cond=expr statms                              # while
      | 'return' expr ';'                                     # return
      ;

call : name=ID '(' exprs? ')'
     ;

exprs : expr (',' expr)*
      ;

expr : left=summ (op=('>'|'<'|'>='|'<='|'=='|'!=') right=expr)*
     ;

summ : left=mult (op=('+'|'-') right=summ)*
     ;

mult : left=atom (op=('*'|'/') right=mult)*
     ;

atom : '(' expr ')'
     | INT
     | FLOAT
     | BOOL
     | ID
     | 'input'
     | call
     ;

types : INTEGER | FLOATING_POINT | BOOLEAN;

INPUT : 'input';
ELSE : 'else';
INTEGER : 'int';
FLOATING_POINT : 'float';
BOOLEAN : 'bool';
ID : [a-zA-Z]+[0-9a-zA-Z]*;
INT : [0-9]+;
FLOAT : INT[.]INT;
BOOL : 'true' | 'false';
WS : [ \r\n\t]+ -> skip;
