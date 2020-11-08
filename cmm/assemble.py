import tempfile
import subprocess

def assemble(asm_input, bin_output, gcc):
    """Call gcc or clang to assemble and link"""
    suffix = '.s' if gcc else '.ll'
    asm = tempfile.NamedTemporaryFile('w', delete=False, suffix=suffix)
    asm.write(asm_input)
    asm.close()

    subprocess.call(['gcc' if gcc else 'clang', asm.name, '-o', bin_output])
