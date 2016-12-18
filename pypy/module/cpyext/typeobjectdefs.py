from pypy.module.cpyext.api import object_h


freefunc = object_h.definitions['freefunc']
destructor = object_h.definitions['destructor']
printfunc = object_h.definitions['printfunc']
getattrfunc = object_h.definitions['getattrfunc']
getattrofunc = object_h.definitions['getattrofunc']
setattrfunc = object_h.definitions['setattrfunc']
setattrofunc = object_h.definitions['setattrofunc']
cmpfunc = object_h.definitions['cmpfunc']
reprfunc = object_h.definitions['reprfunc']
hashfunc = object_h.definitions['hashfunc']
richcmpfunc = object_h.definitions['richcmpfunc']
getiterfunc = object_h.definitions['getiterfunc']
iternextfunc = object_h.definitions['iternextfunc']
descrgetfunc = object_h.definitions['descrgetfunc']
descrsetfunc = object_h.definitions['descrsetfunc']
initproc = object_h.definitions['initproc']
newfunc = object_h.definitions['newfunc']
allocfunc = object_h.definitions['allocfunc']

unaryfunc = object_h.definitions['unaryfunc']
binaryfunc = object_h.definitions['binaryfunc']
ternaryfunc = object_h.definitions['ternaryfunc']
inquiry = object_h.definitions['inquiry']
lenfunc = object_h.definitions['lenfunc']
coercion = object_h.definitions['coercion']
intargfunc = object_h.definitions['intargfunc']
intintargfunc = object_h.definitions['intintargfunc']
ssizeargfunc = object_h.definitions['ssizeargfunc']
ssizessizeargfunc = object_h.definitions['ssizessizeargfunc']
intobjargproc = object_h.definitions['intobjargproc']
intintobjargproc = object_h.definitions['intintobjargproc']
ssizeobjargproc = object_h.definitions['ssizeobjargproc']
ssizessizeobjargproc = object_h.definitions['ssizessizeobjargproc']
objobjargproc = object_h.definitions['objobjargproc']

objobjproc = object_h.definitions['objobjproc']
visitproc = object_h.definitions['visitproc']
traverseproc = object_h.definitions['traverseproc']

getter = object_h.definitions['getter']
setter = object_h.definitions['setter']

#wrapperfunc = object_h.definitions['wrapperfunc']
#wrapperfunc_kwds = object_h.definitions['wrapperfunc_kwds']

readbufferproc = object_h.definitions['readbufferproc']
writebufferproc = object_h.definitions['writebufferproc']
segcountproc = object_h.definitions['segcountproc']
charbufferproc = object_h.definitions['charbufferproc']
getbufferproc = object_h.definitions['getbufferproc']
releasebufferproc = object_h.definitions['releasebufferproc']


PyGetSetDef = object_h.definitions['PyGetSetDef']
PyNumberMethods = object_h.definitions['PyNumberMethods']
PySequenceMethods = object_h.definitions['PySequenceMethods']
PyMappingMethods = object_h.definitions['PyMappingMethods']
PyBufferProcs = object_h.definitions['PyBufferProcs']
PyMemberDef = object_h.definitions['PyMemberDef']
