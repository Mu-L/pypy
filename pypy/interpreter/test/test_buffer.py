import py
from pypy.interpreter.buffer import Buffer
from rpython.tool.udir import udir

testdir = udir.ensure('test_buffer', dir=1)


class TestBuffer:

    def test_buffer_w(self):
        space = self.space
        w_hello = space.wrapbytes('hello world')
        buf = space.buffer_w(w_hello)
        assert isinstance(buf, Buffer)
        assert buf.getlength() == 11
        assert buf.as_str() == 'hello world'
        assert buf.getslice(1, 6, 1, 5) == 'ello '
        assert space.buffer_w(space.wrap(buf)) is buf
        assert space.bufferstr_w(w_hello) == 'hello world'
        assert space.bufferstr_w(space.buffer(w_hello)) == 'hello world'
        space.raises_w(space.w_TypeError, space.buffer_w, space.wrap(5))
        e = space.raises_w(space.w_TypeError, space.buffer, space.wrap(5))
        message = space.unwrap(e.value.get_w_value(space))
        assert "'int' does not support the buffer interface" == message

    def test_file_write(self):
        space = self.space
        w_buffer = space.buffer(space.wrapbytes('hello world'))
        filename = str(testdir.join('test_file_write'))
        space.appexec([w_buffer, space.wrap(filename)], """(buffer, filename):
            f = open(filename, 'wb')
            f.write(buffer)
            f.close()
        """)
        f = open(filename, 'rb')
        data = f.read()
        f.close()
        assert data == 'hello world'

# Note: some app-level tests for buffer are in module/__builtin__/test/.
