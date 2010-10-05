import os
import tempfile
class ASMInstruction(object):

    if os.uname()[0] == 'Darwin':
        asm = '~/Code/arm-jit/android/android-ndk-r4b//build/prebuilt/darwin-x86/arm-eabi-4.4.0/arm-eabi/bin/as'
    else:
        asm = 'as'
    asm_opts = '-mcpu=cortex-a8 -march=armv7'
    body = """.section .text
.arm
.global main
main:
    .ascii "START"
    %s
    .ascii "END"
"""
    begin_tag = 'START'
    end_tag = 'END'

    def __init__(self, instr):
        self.instr = instr
        self.file = tempfile.NamedTemporaryFile(mode='w')
        self.name = self.file.name
        self.tmpdir = os.path.dirname(self.name)

    def encode(self):
        f = open("%s/a.out" % (self.tmpdir),'rb')
        data = f.read()
        f.close()
        i = data.find(self.begin_tag)
        assert i>=0
        j = data.find(self.end_tag, i)
        assert j>=0
        as_code = data[i+len(self.begin_tag):j]
        return as_code



    def assemble(self, *args):
        res = self.body % (self.instr)
        self.file.write(res)
        self.file.flush()
        os.system("%s %s %s -o %s/a.out" % (self.asm, self.asm_opts, self.name, self.tmpdir))

    def __del__(self):
        self.file.close()

def assemble(instr):
    a = ASMInstruction(instr)
    a.assemble(instr)
    return a.encode()
