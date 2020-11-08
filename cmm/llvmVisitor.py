from .parser.cmmParser import cmmParser
from .parser.cmmVisitor import cmmVisitor
from llvmlite import binding
from llvmlite import ir
from typing import List

class llvmVisitor(cmmVisitor):
    def __init__(self, file_name):
        self.file_name = file_name # used for error messages

        self.module = ir.Module() # LLVM module

        self.func_table = {} 

        # Declare C printf and scanf in the module
        p_type = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer()], var_arg=True)
        self.func_table['printf'] = ir.Function(self.module, p_type, name='printf')
        self.func_table['__isoc99_scanf'] = ir.Function(self.module, p_type, name='__isoc99_scanf')
        #################################

        # Global variable for the printf first parameter
        fmt_str = '%d\n\0'
        fmt = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str)), bytearray(fmt_str.encode('utf8')))
        self.global_fmt = ir.GlobalVariable(self.module, fmt.type, 'fmt')
        self.global_fmt.linkage = 'internal'
        self.global_fmt.global_constant = True
        self.global_fmt.initializer = fmt
        #################################
        
        # Global variable for the scanf first parameter
        fmt_str_in = '%d'
        fmt_in = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str_in)), bytearray(fmt_str_in.encode('utf8')))
        self.global_fmt_in = ir.GlobalVariable(self.module, fmt_in.type, 'fmt_in')
        self.global_fmt_in.linkage = 'internal'
        self.global_fmt_in.global_constant = True
        self.global_fmt_in.initializer = fmt_in
        #################################
   

    def asm(self) -> str:
        """Return native assembly as str"""
        target_machine = binding.Target.from_default_triple().create_target_machine()
        llvm = binding.parse_assembly(str(self.module))
        return target_machine.emit_assembly(llvm)

    def visitFunc(self, ctx:cmmParser.FuncContext):
        """Build function"""
        args = self.visit(ctx.args()) if ctx.args() else [] # List or arguments
        func_type = ir.FunctionType(ir.IntType(32), [ir.IntType(32) for _ in args]) # Function type (similator to C)
        #                           ^Return type^^  ^Argument types (all i32)^^^^^ 

        # Add function to table and set the builder
        self.func_table[ctx.name.text] = ir.Function(self.module, func_type, name=ctx.name.text)
        self.func = self.func_table[ctx.name.text]
        self.block = self.func.append_basic_block(name='entry') # Initialize the first block
        self.builder = ir.IRBuilder(self.block)
        #################################

        self.id_table = {} # Function id table

        # Copy the arguments and populate the id table
        for i in range(len(args)):
            self.func.args[i].name = args[i]
            self.id_table[args[i]] = self.builder.alloca(ir.IntType(32), name=args[i])
            self.builder.store(self.func.args[i], self.id_table[args[i]])
        #################################

        return self.visit(ctx.statms()) # Build the function body

    def visitWhile(self, ctx:cmmParser.WhileContext):
        """Build while statement"""
        block_while = self.builder.append_basic_block(name='loop')
        block_next = self.builder.append_basic_block(name='next')

        self.builder.branch(block_while) # End the current block 
        
        # Switch contex for the loop block
        with self.builder.goto_block(block_while): 
            zero = ir.Constant(ir.IntType(32), 0)
            result = self.builder.icmp_signed('<', zero, self.visit(ctx.cond), name='tmp_w_cmp')
            with self.builder.if_then(result): # Execute if 0 < cond
                self.visit(ctx.statms()) # Build while body
                self.builder.branch(block_while) # Loop 
            self.builder.branch(block_next) # End loop
        #################################
        
        self.builder = ir.IRBuilder(block_next) # Set the builder for the next block out of the loop

    def visitIf(self, ctx:cmmParser.IfContext):
        """Build if statement"""
        zero = ir.Constant(ir.IntType(32), 0)
        result = self.builder.icmp_signed('<', zero, self.visit(ctx.cond), name='temp_if_cmp')
        if ctx.ELSE(): # if-then-else
            with self.builder.if_else(result) as (then, otherwise):
                with then:
                    self.visit(ctx.then) # Build then body
                with otherwise:
                    self.visit(ctx.otherwise) # Build else body
        else: # if-then
            with self.builder.if_then(result):
                self.visit(ctx.then) # Build then body
        
    def visitArgs(self, ctx:cmmParser.ArgsContext) -> List[str]:
        """Return the arguments id list"""
        return [str(x) for x in ctx.ID()]

    def visitCall(self, ctx:cmmParser.CallContext) -> ir.CallInstr:
        """Build call expression"""
        if not ctx.name.text in self.func_table:
            raise KeyError(self.file_name+':'+str(ctx.name.line)+':'+str(ctx.name.column)+' function '+ctx.name.text+' is not defined')
        return self.builder.call(self.func_table[ctx.name.text], self.visit(ctx.exprs()), name='tmp_call')

    def visitExprs(self, ctx:cmmParser.ExprsContext):
        """Build expresions and return the list of results"""
        return [self.visit(x) for x in ctx.expr()]

    def visitAssign(self, ctx:cmmParser.AssignContext):
        """Build assing statement"""
        expr = self.visit(ctx.expr())
        if not str(ctx.ID()) in self.id_table: # Create table entry if variable is not defined
            self.id_table[str(ctx.ID())] = self.builder.alloca(ir.IntType(32), name=str(ctx.ID())) 
        self.builder.store(expr, self.id_table[str(ctx.ID())])

    def visitReturn(self, ctx:cmmParser.ReturnContext):
        """Build return statement that ends the block"""
        self.builder.ret(self.visit(ctx.expr()))

    def visitAtom(self, ctx:cmmParser.AtomContext):
        """Build atomic expressions"""
        if ctx.expr(): # Parentheses
            return self.visit(ctx.expr())
        elif ctx.ID(): # Load variable 
            if not str(ctx.ID()) in self.id_table:
                symbol = ctx.ID().getSymbol()
                raise KeyError(self.file_name+':'+str(symbol.line)+':'+str(symbol.column)+' variable '+str(ctx.ID())+' is not defined')
            return self.builder.load(self.id_table[str(ctx.ID())], name='tmp_'+str(ctx.ID()))
        elif ctx.INT(): # Constant
            return ir.Constant(ir.IntType(32), int(str(ctx.INT())))
        elif ctx.call():
            return self.visit(ctx.call())
        elif ctx.INPUT(): # Use scanf to input an i32
            ret = self.builder.alloca(ir.IntType(32), name='tmp_in_ptr')
            self.builder.call(self.func_table["__isoc99_scanf"], (self.global_fmt_in.bitcast(ir.IntType(8).as_pointer()), ret), name='scanf_ret')
            return self.builder.load(ret, name='tmp_in')

    def visitExpr(self, ctx:cmmParser.ExprContext):
        """Build lowest priority expresions"""
        left = self.visit(ctx.left)
        if ctx.right: # >, <, >=, <=, ==, != 
            right = self.visit(ctx.right)
            result = self.builder.icmp_signed(ctx.op.text, left, right, name='tmp_cmp_b')
            return self.builder.zext(result, ir.IntType(32), name='tmp_cmp') # as result is i1, zero-extend it to i32
        else: # higher priority expsetion 
             return left 

    def visitSumm(self, ctx:cmmParser.SummContext):
        """Build + and - exprestions"""
        left = self.visit(ctx.left)
        if ctx.right:
            right = self.visit(ctx.right)
            if ctx.op.text == '+':
                return self.builder.add(left, right, name='tmp_add')
            elif ctx.op.text == '-':
                return self.builder.sub(left, right, name='tmp_sub')
        return left

    def visitMult(self, ctx:cmmParser.MultContext):
        """Build * and / exprestions"""
        left = self.visit(ctx.left)
        if ctx.right:
            right = self.visit(ctx.right)
            if ctx.op.text == '*':
                return self.builder.mul(left, right, name='tmp_mul')
            elif ctx.op.text  == '/':
                return self.builder.sdiv(left, right, name='tmp_div')
        return left

    def visitPrint(self, ctx:cmmParser.PrintContext):
        """Build print expresion"""
        self.builder.call(self.func_table['printf'], (self.global_fmt.bitcast(ir.IntType(8).as_pointer()), self.visit(ctx.expr())), name='printf_ret')

