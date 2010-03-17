
/**************************************************************/
/***  this is included before any code produced by genc.py  ***/

#include "src/commondefs.h"

#ifndef AVR
#include "thread.h"   /* needs to be included early to define the
                         struct RPyOpaque_ThreadLock */
#endif

#include <stddef.h>


#ifdef __GNUC__       /* other platforms too, probably */
typedef _Bool bool_t;
#else
typedef unsigned char bool_t;
#endif


#include "src/align.h"
