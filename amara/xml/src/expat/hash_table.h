#ifndef EXPAT_HASH_TABLE_H
#define EXPAT_HASH_TABLE_H

#ifdef __cplusplus
extern "C" {
#endif

#include "Python.h"
#include "xmlchar.h"

  typedef struct {
    long hash;
    XML_Char *key;
    size_t len;
    PyObject *value;
  } HashTableEntry;

  typedef struct {
    int used;

    /* The table contains (mask + 1)**2 slots.
     * We store the mask instead of the size because the mask is more
     * frequently needed.
     */
    int mask;

    HashTableEntry *table;
  } HashTable;

  HashTable *HashTable_New(void);
  void HashTable_Del(HashTable *table);
  PyObject *HashTable_Lookup(HashTable *table, const XML_Char *str, size_t len,
                             PyObject *(*buildvalue)(const XML_Char *str,
                                                     Py_ssize_t len, void *arg),
                             void *buildarg);

#ifdef __cplusplus
}
#endif

#endif /* EXPAT_HASH_TABLE_H */
