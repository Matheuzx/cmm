from .assemble import assemble
from antlr4 import FileStream, CommonTokenStream
from llvmlite import binding
from os import path
import argparse

try:
    from .parser.cmmLexer import cmmLexer
    from .parser.cmmParser import cmmParser
except ImportError:
    # Generate ANTLR parser from g4 file
    from .generate_parser import generate_parser
    generate_parser(path.join(path.dirname(__file__), 'parser/cmm.g4'))

    from .parser.cmmLexer import cmmLexer
    from .parser.cmmParser import cmmParser

# import llvmVisitor after the try-except
from .llvmVisitor import llvmVisitor

def main():
    # Initialize LLVM Core and others 
    binding.initialize()
    binding.initialize_native_target() 
    binding.initialize_native_asmprinter()
    #################################

    # Argument parser
    parser_args = argparse.ArgumentParser(prog='cmm', description='C-- compiler')
    parser_args.add_argument('input', type=str, help='source code')
    parser_args.add_argument('-l', metavar='*.ll', type=str, help='llvm output')
    parser_args.add_argument('-s', metavar='*.s', type=str, help='native assembly output')
    parser_args.add_argument('-o', metavar='', type=str, default='a.out', help='binary output')
    parser_args.add_argument('--clang', action='store_const', const=True, help='use clang instead of gcc to assemble')

    args = parser_args.parse_args() 
    #################################

    input_stream = FileStream(args.input)

    lexer = cmmLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = cmmParser(stream)

    tree = parser.start() # Get AST

    # Transverse AST to generate llvm 
    ll = llvmVisitor(args.input)
    ll.visitStart(tree)
    #################################


    # Output llvm 
    if args.l: 
        with open(args.l, 'w') as lout:
            lout.write(str(ll.module))
    #################################
    
    # Output native assembly
    if args.s:
        with open(args.s, 'w') as asm:
            asm.write(ll.asm())
    #################################
    
    # Assemble and link 
    assemble(str(ll.module) if args.clang else ll.asm(),
             args.o,
             gcc=not args.clang)
    #################################
    
    binding.shutdown() # Shotdown LLVM core
    
if __name__ == '__main__':
    main()