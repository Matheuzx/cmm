# Setup 

Install Python packages
```shell
pip install -r requirement.txt
```

> ANTLR requirers java to generate the parser.

# Usage

```shell
$ python -m cmm -h
usage: cmm [-h] [-l *.ll] [-s *.s] [-o] [--clang] input

C-- compiler

positional arguments:
  input       source code

optional arguments:
  -h, --help  show this help message and exit
  -l *.ll     llvm output
  -s *.s      native assembly output
  -o          binary output
  --clang     use clang instead of gcc to assemble
```
