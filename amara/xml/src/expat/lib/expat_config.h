/* Minimal set of defines required for the Expat library */

#include "pyconfig.h"

/* pyconfig.h on Windows defines PREFIX instead of in the project file */
#ifdef PREFIX
# undef PREFIX
#endif

/* This value is provided via the setup.py script */
/* 1234 = LIL_ENDIAN, 4321 = BIGENDIAN */
#ifdef WORDS_BIGENDIAN
# define BYTEORDER 4321
#else
# define BYTEORDER 1234
#endif

/* Windows has memmove() available. */
#ifdef MS_WINDOWS
# define HAVE_MEMMOVE
#endif

/* Define to specify how much context to retain around the current parse
   point. */
#define XML_CONTEXT_BYTES 1024

/* Define to make parameter entity parsing functionality available. */
#define XML_DTD 1

/* Define to make XML Namespaces functionality available. */
#define XML_NS 1

/* On  Windows,  this  should  be  set  if  Expat is going to be linked 
   statically with the code that calls it; this is required to get all the
   right MSVC magic annotations correct. This is ignored on other platforms.
*/
#define XML_STATIC 1

/* Define to provide document information in UTF-16 rather than the
   default UTF-8.
*/
#ifdef Py_USING_UNICODE
# define XML_UNICODE 1
# define XML_UNICODE_SIZE Py_UNICODE_SIZE
#endif
