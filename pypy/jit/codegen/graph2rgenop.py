"""
For testing purposes.  Turns *simple enough* low-level graphs
into machine code by calling the rgenop interface.
"""
from pypy.rpython.lltypesystem import lltype
from pypy.objspace.flow import model as flowmodel
import random


def rcompile(rgenop, entrypoint, argtypes):
    from pypy.translator.translator import TranslationContext
    from pypy import conftest
    t = TranslationContext()
    t.buildannotator().build_types(entrypoint, argtypes)
    t.buildrtyper().specialize()
    if conftest.option.view:
        t.view()

    from pypy.translator.c.genc import CStandaloneBuilder
    cbuild = CStandaloneBuilder(t, entrypoint, config=t.config)
    db = cbuild.generate_graphs_for_llinterp()
    entrypointptr = cbuild.getentrypointptr()
    entrygraph = entrypointptr._obj.graph
    return compile_graph(rgenop, entrygraph)


def compile_graph(rgenop, graph, random_seed=0):
    FUNC = lltype.FuncType([v.concretetype for v in graph.getargs()],
                           graph.getreturnvar().concretetype)
    sigtoken = rgenop.sigToken(FUNC)
    builder, gv_entrypoint, args_gv = rgenop.newgraph(sigtoken,
                                         "compiled_%s" % (graph.name,))

    def varkind(v):
        return rgenop.kindToken(v.concretetype)

    def var2gv(v):
        if isinstance(v, flowmodel.Variable):
            return varmap[v]
        else:
            return rgenop.genconst(v.value)

    map(varkind, graph.getargs())    # for the py.test.skip() in some backends
    pending_blocks = [(graph.startblock, builder, args_gv)]
    more_pending_blocks = []
    entrymap = flowmodel.mkentrymap(graph)
    entrymap[graph.returnblock] = "force a label"
    labels = {graph.returnblock: None}
    r = random.Random(random_seed)

    while pending_blocks or more_pending_blocks:
        if not pending_blocks:
            r.shuffle(more_pending_blocks)
            pending_blocks = more_pending_blocks
            more_pending_blocks = []
        block, builder, args_gv = pending_blocks.pop()
        builder.start_writing()

        # the following loop generates a chain of blocks
        # (a branch in the graph)
        while True:
            assert len(args_gv) == len(block.inputargs)
            if len(entrymap[block]) > 1:
                # need a label at the start of this block
                if block in labels:
                    # already got one, jump to it
                    label = labels[block]
                    if label is not None:
                        builder.finish_and_goto(args_gv, labels[block])
                    else:
                        [retvar] = args_gv
                        builder.finish_and_return(sigtoken, retvar)
                    break    # done along this branch
                else:
                    # create a label and proceed
                    kinds = map(varkind, block.inputargs)
                    labels[block] = builder.enter_next_block(kinds, args_gv)

            # generate the operations
            varmap = dict(zip(block.inputargs, args_gv))
            for op in block.operations:
                gv_result = generate_operation(rgenop, builder, op, var2gv)
                varmap[op.result] = gv_result

            if block.exitswitch is None:
                [link] = block.exits
            else:
                if block.exitswitch.concretetype is not lltype.Bool:
                    raise NotImplementedError("XXX switches")
                i = r.randrange(0, 2)
                jumplink = block.exits[i]
                args_gv = map(var2gv, jumplink.args)
                if jumplink.exitcase:
                    meth = builder.jump_if_true
                else:
                    meth = builder.jump_if_false
                newbuilder = meth(varmap[block.exitswitch], args_gv)
                more_pending_blocks.append((jumplink.target,
                                            newbuilder,
                                            args_gv))
                link = block.exits[1-i]

            args_gv = map(var2gv, link.args)
            block = link.target

    builder.end()
    return gv_entrypoint


def generate_operation(rgenop, builder, op, var2gv):
    # XXX only supports some operations for now
    if op.opname == 'malloc':
        token = rgenop.allocToken(op.args[0].value)
        gv_result = builder.genop_malloc_fixedsize(token)
    elif op.opname == 'getfield':
        token = rgenop.fieldToken(op.args[0].concretetype.TO,
                                  op.args[1].value)
        gv_result = builder.genop_getfield(token,
                                           var2gv(op.args[0]))
    elif op.opname == 'setfield':
        token = rgenop.fieldToken(op.args[0].concretetype.TO,
                                  op.args[1].value)
        gv_result = builder.genop_setfield(token,
                                           var2gv(op.args[0]),
                                           var2gv(op.args[2]))
    elif op.opname == 'malloc_varsize':
        token = rgenop.varsizeAllocToken(op.args[0].value)
        gv_result = builder.genop_malloc_varsize(token,
                                                 var2gv(op.args[1]))
    elif op.opname == 'getarrayitem':
        token = rgenop.arrayToken(op.args[0].concretetype.TO)
        gv_result = builder.genop_getarrayitem(token,
                                               var2gv(op.args[0]),
                                               var2gv(op.args[1]))
    elif op.opname == 'setarrayitem':
        token = rgenop.arrayToken(op.args[0].concretetype.TO)
        gv_result = builder.genop_setarrayitem(token,
                                               var2gv(op.args[0]),
                                               var2gv(op.args[1]),
                                               var2gv(op.args[2]))
    elif op.opname == 'same_as':
        token = rgenop.kindToken(op.args[0].concretetype)
        gv_result = builder.genop_same_as(token, var2gv(op.args[0]))
    elif len(op.args) == 1:
        gv_result = builder.genop1(op.opname, var2gv(op.args[0]))
    elif len(op.args) == 2:
        gv_result = builder.genop2(op.opname, var2gv(op.args[0]),
                                              var2gv(op.args[1]))
    else:
        raise NotImplementedError(op.opname)
    return gv_result
