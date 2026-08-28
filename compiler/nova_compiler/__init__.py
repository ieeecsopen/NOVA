"""The NOVA Native Compiler.

Pipeline:
  Source -> Lexer -> Parser -> AST -> Name Resolution -> Type & Effect Checking
         -> HIR -> MIR -> C/LLVM Backend -> Native Executable
"""

__version__ = "0.1.0"
