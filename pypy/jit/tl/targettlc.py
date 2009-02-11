import time
import py
py.magic.autopath()
from pypy.jit.tl.tlc import interp, interp_eval, interp_nonjit, ConstantPool
from pypy.jit.codegen.hlinfo import highleveljitinfo


def entry_point(args):
    """Main entry point of the stand-alone executable:
    takes a list of strings and returns the exit code.
    """
    # store args[0] in a place where the JIT log can find it (used by
    # viewcode.py to know the executable whose symbols it should display)
    exe = args[0]
    args = args[1:]
    highleveljitinfo.sys_executable = exe
    if len(args) < 2:
        print "Usage: %s [--onlyjit] filename x" % (exe,)
        return 2

    onlyjit = False
    if args[0] == '--onlyjit':
        onlyjit = True
        args = args[1:]
        
    filename = args[0]
    x = int(args[1])
    bytecode, pool = load_bytecode(filename)

    if not onlyjit:
        start = time.clock()
        res = interp_nonjit(bytecode, inputarg=x, pool=pool)
        stop = time.clock()
        print 'Non jitted:    %d (%f seconds)' % (res, stop-start)

    start = time.clock()
    res = interp(bytecode, inputarg=x, pool=pool)
    stop = time.clock()
    print 'Warmup jitted: %d (%f seconds)' % (res, stop-start)

    start = time.clock()
    res = interp(bytecode, inputarg=x, pool=pool)
    stop = time.clock()
    print 'Warmed jitted: %d (%f seconds)' % (res, stop-start)

    return 0


def load_bytecode(filename):
    from pypy.rlib.streamio import open_file_as_stream
    from pypy.jit.tl.tlopcode import decode_program
    f = open_file_as_stream(filename)
    return decode_program(f.readall())

def target(driver, args):
    return entry_point, None

# ____________________________________________________________

from pypy.jit.hintannotator.policy import HintAnnotatorPolicy

class MyHintAnnotatorPolicy(HintAnnotatorPolicy):
    novirtualcontainer = True
    oopspec = True

def portal(driver):
    """Return the 'portal' function, and the hint-annotator policy.
    The portal is the function that gets patched with a call to the JIT
    compiler.
    """
    return interp_eval, MyHintAnnotatorPolicy()

if __name__ == '__main__':
    import sys
    sys.exit(entry_point(sys.argv))
