import py
import pytest
from rpython.tool.udir import udir
from pypy.interpreter.gateway import interp2app, unwrap_spec, W_Root
from pypy.tool.cpyext.extbuild import c_compile
from pypy.module.cpyext.test.test_cpyext import AppTestCpythonExtensionBase
from pypy.module._hpy_universal.llapi import BASE_DIR
from pypy.module._hpy_universal.test._vendored import support as _support

COMPILER_VERBOSE = False

class HPyDevel(object):
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.include_dir = base_dir / 'include'
        self.src_dir = base_dir / 'src' / 'runtime'
        # extra_sources are needed both in CPython and Universal mode
        self._extra_sources = [
            self.src_dir / 'argparse.c',
            ]


class HPyExtensionCompiler(_support.ExtensionCompiler):
    def compile_module(self, main_template, name, extra_templates):
        """
        Create and compile a HPy module from the template
        """
        filename = self._expand(name, main_template)
        sources = [str(filename)]
        for i, template in enumerate(extra_templates):
            extra_filename = self._expand('extmod_%d' % i, template)
            sources.append(extra_filename)
        #
        compile_args = [
            '-g', '-O0',
            '-Wfatal-errors',    # stop after one error (unrelated to warnings)
            '-Werror',           # turn warnings into errors (all, for now)
            '-DHPY_UNIVERSAL_ABI',
        ]
        link_args = [
            '-g',
        ]
        #
        modname = name.split('.')[-1]
        so_filename = c_compile(
            sources + map(str, self.hpy_devel._extra_sources),
            outputfilename=self.tmpdir / modname,
            compile_extra=compile_args,
            link_extra=link_args,
            include_dirs=[str(self.hpy_devel.include_dir)] + self.extra_include_dirs)
        return str(so_filename)


class HPyAppTest(object):
    """
    Base class for HPy app tests
    """
    spaceconfig = {'usemodules': ['_hpy_universal']}

    @pytest.fixture
    def compiler(self):
        # see setup_method below
        return 'The fixture "compiler" is not used on pypy'

    def setup_class(cls):
        if cls.runappdirect:
            pytest.skip()

    def setup_method(self, meth):
        if self.space.config.objspace.usemodules.cpyext:
            from pypy.module import cpyext
            cpython_include_dirs = cpyext.api.include_dirs
        else:
            cpython_include_dirs = []
        #
        # it would be nice to use the 'compiler' fixture to provide
        # make_module as the std HPyTest do. However, we don't have the space
        # yet, so it is much easier to prove make_module() here
        tmpdir = py.path.local.make_numbered_dir(rootdir=udir,
                                                 prefix=meth.__name__ + '-',
                                                 keep=0)  # keep everything
        compiler = HPyExtensionCompiler(tmpdir, HPyDevel(BASE_DIR), 'universal',
                                              compiler_verbose=COMPILER_VERBOSE,
                                              extra_include_dirs=cpython_include_dirs)
        #
        @unwrap_spec(source_template='text', name='text', w_extra_templates=W_Root)
        def descr_make_module(space, source_template, name='mytest',
                              w_extra_templates=None):
            if w_extra_templates is None:
                extra_templates = ()
            else:
                items_w = space.unpackiterable(w_extra_templates)
                extra_templates = [space.text_w(item) for item in items_w]
            so_filename = compiler.compile_module(source_template, name, extra_templates)
            w_mod = space.appexec([space.newtext(so_filename), space.newtext(name)],
                """(path, modname):
                    import _hpy_universal
                    return _hpy_universal.load(modname, path)
                """
            )
            return w_mod
        self.w_make_module = self.space.wrap(interp2app(descr_make_module))

        def should_check_refcount(space):
            return space.w_False
        self.w_should_check_refcount = self.space.wrap(interp2app(should_check_refcount))


class HPyCPyextAppTest(AppTestCpythonExtensionBase, HPyAppTest):
    """
    Base class for hpy tests which also need cpyext
    """
    # mmap is needed because it is imported by LeakCheckingTest.setup_class
    spaceconfig = {'usemodules': ['_hpy_universal', 'cpyext', 'mmap']}

    def setup_class(cls):
        AppTestCpythonExtensionBase.setup_class.im_func(cls)
        HPyAppTest.setup_class.im_func(cls)

    def setup_method(self, meth):
        AppTestCpythonExtensionBase.setup_method(self, meth)
        HPyAppTest.setup_method(self, meth)