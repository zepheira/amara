#include "hash_table.h"

/* A hashtable implementation for storing XML_Char keys */

/*
To ensure the lookup algorithm terminates, there must be at least one Unused
slot (NULL key) in the table.
used is the number of non-NULL keys (== the number of Active items).
To avoid slowing down lookups on a near-full table, we resize the table when
it's two-thirds full.
*/

/* Must be a power of 2 */
#define HashTable_INITIAL_SIZE 64

HashTable *HashTable_New(void)
{
  HashTable *self = PyMem_New(HashTable, 1);
  if (self == NULL)
    return (HashTable *) PyErr_NoMemory();

  self->table = PyMem_New(HashTableEntry, HashTable_INITIAL_SIZE);
  if (self->table == NULL)
    return (HashTable *) PyErr_NoMemory();

  memset(self->table, 0, sizeof(HashTableEntry) * HashTable_INITIAL_SIZE);
  self->used = 0;
  self->mask = HashTable_INITIAL_SIZE - 1;

  return self;
}

void HashTable_Del(HashTable *table)
{
  register HashTableEntry *ep;
  register int used;

  for (ep = table->table, used = table->used; used > 0; ep++) {
    if (ep->key) {
      used--;
      PyMem_Free(ep->key);
      Py_DECREF(ep->value);
    }
  }
  PyMem_Free(table->table);
  PyMem_Free(table);
}

#define CHECK_ENTRY(entry, key, len, hash)              \
  ((entry)->hash == (hash) &&                           \
   (entry)->len == (len) &&                             \
   memcmp((entry)->key, (key), (len)*sizeof(XML_Char)) == 0)

static HashTableEntry *lookup_entry(HashTable *self, const XML_Char *key,
                                    size_t len, register long hash)
{
  register int i;
  register unsigned int perturb;
  register unsigned int mask = self->mask;
  HashTableEntry *table = self->table;
  register HashTableEntry *ep;

  i = hash & mask;
  ep = &table[i];
  if (ep->key == NULL)
    return ep;
  if (CHECK_ENTRY(ep, key, len, hash))
    return ep;

  for (perturb = hash; ; perturb >>= 5) {
    i = (i << 2) + i + perturb + 1;
    ep = &table[i & mask];
    if (ep->key == NULL)
      return ep;
    if (CHECK_ENTRY(ep, key, len, hash))
      return ep;
  }
}

/* Restructure the table by allocating a new table and reinserting all
 * items again.
 */
static int table_resize(HashTable *self)
{
  int newsize = (self->mask + 1) << 2;
  HashTableEntry *oldtable, *newtable;
  HashTableEntry *oldentry, *newentry;
  int i;

  /* Get space for a new table. */
  newtable = PyMem_New(HashTableEntry, newsize);
  if (newtable == NULL) {
    PyErr_NoMemory();
    return -1;
  }

  /* Make the dict empty, using the new table. */
  oldtable = self->table;
  self->table = newtable;
  self->mask = newsize - 1;
  memset(newtable, 0, sizeof(HashTableEntry) * newsize);

  /* Copy the data over */
  for (oldentry = oldtable, i = self->used; i > 0; oldentry++) {
    if (oldentry->key != NULL) {
      i--;
      newentry = lookup_entry(self, oldentry->key, oldentry->len,
                              oldentry->hash);
      memcpy(newentry, oldentry, sizeof(HashTableEntry));
    }
  }

  PyMem_Free(oldtable);
  return 0;
}

PyObject *HashTable_Lookup(HashTable *self, const XML_Char *str, size_t len,
                           PyObject *(*buildvalue)(const XML_Char *str,
                                                   Py_ssize_t len, void *arg),
                           void *buildarg)
{
  register Py_ssize_t i = len;
  register const XML_Char *p = str;
  register long hash;
  HashTableEntry *entry;
  XML_Char *key;
  PyObject *value;

  /* Calcuate the hash value */
  hash = *p << 7;
  while (--i >= 0)
    hash = (1000003*hash) ^ *p++;
  hash ^= len;

  entry = lookup_entry(self, str, len, hash);
  if (entry->key) {
    return entry->value;
  }

  /* not found in table, populate the entry */
  key = PyMem_New(XML_Char, len + 1);
  if (key == NULL)
    return PyErr_NoMemory();
  memcpy(key, str, len * sizeof(XML_Char));
  key[len] = 0;

  if (buildvalue)
    value = buildvalue(str, len, buildarg);
  else
    value = XMLChar_DecodeSized(str, len);
  if (value == NULL) {
    PyMem_Free(key);
    return NULL;
  }

  entry->key = key;
  entry->len = len;
  entry->hash = hash;
  entry->value = value;

  /* Resize the table if it is more than 2/3 used */
  self->used++;
  if (self->used * 3 >= (self->mask + 1) * 2) {
    if (table_resize(self) == -1) {
      return NULL;
    }
  }

  return value;
}
