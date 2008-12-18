/***********************************************************************
 * amara/xslt/functions/src/decimal_format.c
 ***********************************************************************/

static char module_doc[] = "\
Optimized functions for XSLT\n\
";

#include "Python.h"

#define MODULE_NAME "amara.xslt.functions._functions"
#define MODULE_INITFUNC init_functions

/* Floating-point classification macros */
#if __STDC_VERSION__ < 199901L
#  if defined(_WIN32) || defined(__WIN32__)
#    ifdef __MINGW32__
#      include <math.h>
#    else
#      include <float.h>
#      define isnan(x) _isnan(x)
#      define isfinite(x) _finite(x)
#      define isinf(x) (!isfinite(x) && !isnan(x))
#    endif
#  elif (defined(__sun) || defined(__sgi) || defined(__svr4__) || \
         defined(__osf__))
#    include <ieeefp.h>
#    define isfinite(x) finite(x)
#    define isinf(x) (!isfinite(x) && !isnan(x))
#  else
#    ifndef isnan
#      define isnan(x) ((x) != (x))
#    endif
#    ifndef isinf
#      define isinf(x) ((x) && (x)*0.5 == (x))
#    endif
#    ifndef isfinite
#      define isfinite(x) (isnan(x) == isinf(x))
#    endif
#  endif
#endif

#define EXTRA 100
#define QUOTE '\''

#define DOUBLE_INTEGER_DIGITS  309
#define DOUBLE_FRACTION_DIGITS 340

typedef struct {
  char digits[DOUBLE_FRACTION_DIGITS];
  short count;
  short decimalAt;
} DigitList;

typedef struct {
  PyObject *pattern;
  Py_UNICODE *prefix, *suffix;
  Py_ssize_t prefixSize, suffixSize;
} PatternParts;

typedef struct {
  PatternParts positive;
  PatternParts negative;

  int minIntegerDigits, maxIntegerDigits;
  int minFractionDigits, maxFractionDigits;

  int multiplier;
  int groupingSize;

  /* boolean */
  char groupingUsed, showDecimalPoint;
} FormatInfo;

typedef struct DecimalFormatSymbols {
  Py_UNICODE zeroDigit;
  Py_UNICODE groupingSeparator;
  Py_UNICODE decimalSeparator;
  Py_UNICODE percent;
  Py_UNICODE perMille;
  Py_UNICODE digit;
  Py_UNICODE separator;
  Py_UNICODE minus;
} DecimalFormatSymbols;

/*
 * `decimal_format` provides decimal formatting for the XSLT format-number()
 * function.  It is modeled on the Java DecimalFormat (as per XSLT spec).
 *
 * See:
 *   http://java.sun.com/products/jdk/1.1/docs/api/java.text.DecimalFormat.html
*/

Py_LOCAL_INLINE(int)
unpack_unichar(PyObject *format, const char *name, Py_ssize_t i, Py_UNICODE *p)
{
  PyObject *arg;

  assert(PyTuple_Check(format));
  assert(i >= 0 && i < PyTuple_GET_SIZE(format));

  arg = PyTuple_GET_ITEM(format, i);
  if (PyUnicode_Check(arg)) {
    if (PyUnicode_GetSize(arg) != 1) {
      PyErr_Format(PyExc_TypeError,
                   "%s, item %zd must be unicode of length 1, not %zd",
                   name == NULL ? "unpacked tuple" : name, i,
                   PyUnicode_GetSize(arg));
      return 0;
    }
    *p = PyUnicode_AsUnicode(arg)[0];
  } else if (PyString_Check(arg)) {
    if (PyString_Size(arg) != 1) {
      PyErr_Format(PyExc_TypeError,
                   "%s, item %zd must be unicode of length 1, not %zd",
                   name == NULL ? "unpacked tuple" : name, i,
                   PyString_Size(arg));
      return 0;
    }
    *p = (Py_UNICODE)PyString_AsString(arg)[0];
  } else {
    PyErr_Format(PyExc_TypeError,
                 "%s, item %zd must be unicode of length 1, not %s",
                 name == NULL ? "unpacked tuple" : name, i,
                 arg == Py_None ? "None" : arg->ob_type->tp_name);
    return 0;
  }
  return 1;
}

Py_LOCAL_INLINE(int)
unpack_unicode(PyObject *format, const char *name, Py_ssize_t i, PyObject **p)
{
  PyObject *arg;

  assert(PyTuple_Check(format));
  assert(i >= 0 && i < PyTuple_GET_SIZE(format));

  arg = PyTuple_GET_ITEM(format, i);
  if (PyUnicode_Check(arg) || PyString_Check(arg)) {
    arg = PyUnicode_FromObject(arg);
    if (arg == NULL) {
      if (PyErr_ExceptionMatches(PyExc_TypeError))
        PyErr_Format(PyExc_TypeError,
                     "%s, item %zd must be unicode, not %s",
                     name == NULL ? "unpacked tuple" : name, i,
                     arg == Py_None ? "None" : arg->ob_type->tp_name);
      return 0;
    }
    *p = arg;
  } else {
    PyErr_Format(PyExc_TypeError,
                 "%s, item %zd must be unicode, not %s",
                 name == NULL ? "unpacked tuple" : name, i,
                 arg == Py_None ? "None" : arg->ob_type->tp_name);
    return 0;
  }
  return 1;
}

Py_LOCAL_INLINE(int)
unpack_format(PyObject *format, const char *name,
              DecimalFormatSymbols *symbols, PyObject **pinf, PyObject **pnan)
{
  PyObject *infinity=NULL, *not_a_number=NULL;

  if (!PyTuple_Check(format)) {
    PyErr_Format(PyExc_TypeError,
                 "%s must be 10-item tuple, not %s",
                 name == NULL ? "unpacked tuple" : name,
                 format == Py_None ? "None" : format->ob_type->tp_name);
    return 0;
  }
  if (PyTuple_GET_SIZE(format) != 10) {
    PyErr_Format(PyExc_TypeError,
                "%s must be tuple of length 10, not %zd",
                name == NULL ? "unpacked tuple" : name,
                PyTuple_GET_SIZE(format));
    return 0;
  }
  if (!unpack_unichar(format, name, 0, &symbols->decimalSeparator))
    goto error;
  if (!unpack_unichar(format, name, 1, &symbols->groupingSeparator))
    goto error;
  /* stores new reference; caller is responsible to decref */
  if (!unpack_unicode(format, name, 2, &infinity))
    goto error;
  if (!unpack_unichar(format, name, 3, &symbols->minus))
    goto error;
  /* stores new reference; caller is responsible to decref */
  if (!unpack_unicode(format, name, 4, &not_a_number))
    goto error;
  if (!unpack_unichar(format, name, 5, &symbols->percent))
    goto error;
  if (!unpack_unichar(format, name, 6, &symbols->perMille))
    goto error;
  if (!unpack_unichar(format, name, 7, &symbols->zeroDigit))
    goto error;
  if (!unpack_unichar(format, name, 8, &symbols->digit))
    goto error;
  if (!unpack_unichar(format, name, 9, &symbols->separator))
    goto error;
  /* success */
  *pinf = infinity;
  *pnan = not_a_number;
  return 1;

error:
  Py_XDECREF(infinity);
  Py_XDECREF(not_a_number);
  return 0;
}

/* constants for phases */
#define PREFIX_PHASE 0
#define PATTERN_PHASE 1
#define SUFFIX_PHASE 2

/* returns error message */
static char *parse_pattern(PyObject *fullpattern, FormatInfo *info,
                           DecimalFormatSymbols *symbols)
{
  Py_UNICODE *pattern = PyUnicode_AS_UNICODE(fullpattern);
  char inPositive = 1;     /* boolean */
  char hasNegative = 0;    /* boolean */

  Py_ssize_t start = 0;
  Py_ssize_t end = PyUnicode_GET_SIZE(fullpattern);

  do {
    char inQuote = 0;
    int decimalPos = -1;
    int multiplier = 1;
    int digitLeftCount = 0;
    int zeroDigitCount = 0;
    int digitRightCount = 0;
    int groupingCount = -1;

    /* The phase ranges from 0 to 2.  Phase 0 is the prefix.  Phase 1 is
     * the section of the pattern with digits, decimal separator,
     * grouping characters.  Phase 2 is the suffix.  In phases 0 and 2,
     * percent, permille, and currency symbols are recognized and
     * translated.  The separation of the characters into phases is
     * strictly enforced; if phase 1 characters are to appear in the
     * suffix, for example, they must be quoted. */
    int phase = PREFIX_PHASE;

    /* Two variables are used to record the subrange of the pattern
     * occupied by phase 1.  This is used during the processing of the
     * second pattern (the one representing negative numbers) to ensure
     * that no deviation exists in phase 1 between the two patterns. */
    Py_ssize_t phaseOneStart = 0;
    Py_ssize_t phaseOneLength = 0;

    /* The affix is either the prefix or the suffix. */
    Py_UNICODE *prefix = pattern + start;
    Py_UNICODE *suffix = pattern + end;
    Py_UNICODE *affix = prefix;
    Py_UNICODE *prefixEnd = NULL;
    Py_UNICODE *suffixEnd = suffix;

    Py_ssize_t pos;

    for (pos = start; pos < end; pos++) {
      Py_UNICODE ch = pattern[pos];
      switch (phase) {
      case PREFIX_PHASE:
      case SUFFIX_PHASE:
        /* Process the prefix/suffix characters */
        if (inQuote) {
          /* A quote within quotes indicates either the closing
           * quote or two quotes, which is a quote literal.    That is,
           * we have the second quote in 'do' or 'don''t'. */
          if (ch == QUOTE) {
            if ((pos+1) < end && pattern[pos+1] == QUOTE) {
              pos++;
              *affix++ = ch;
            } else {
              inQuote = 0;                /* 'do' */
            }
            continue;
          }
        } else {
          /* Process unquoted characters seen in prefix or suffix phase. */
          if (ch == symbols->digit ||
              ch == symbols->zeroDigit ||
              ch == symbols->groupingSeparator ||
              ch == symbols->decimalSeparator) {
            /* Any of these characters implicitly begins the next
             * phase.    If we are in phase 2, there is no next phase,
             * so these characters are illegal. */
            phaseOneStart = pos;
            phaseOneLength = 0;
            prefixEnd = affix;
            phase = PATTERN_PHASE;
            pos--;                        /* Reprocess this character */
            continue;
          } else if (ch == QUOTE) {
            /* A quote outside quotes indicates either the opening
             * quote or two quotes, which is a quote literal.    That is,
             * we have the first quote in 'do' or o''clock. */
            if (ch == QUOTE) {
              if ((pos+1) < end && pattern[pos+1] == QUOTE) {
                pos++;
                *affix++ = ch;
              } else {
                inQuote = 1;
              }
              continue;
            }
          } else if (ch == symbols->separator) {
            /* Don't allow separators before we see digit characters of phase
             * 1, and don't allow separators in the second pattern. */
            if (phase == PREFIX_PHASE || !inPositive)
              return "too many pattern separators";
            suffixEnd = affix;
            start = pos + 1;
            pos = end;
            hasNegative++;
            continue;
          }

          /* Next handle characters which are appended directly. */
          else if (ch == symbols->percent) {
            if (multiplier != 1)
              return "too many percent/permille symbols";
            multiplier = 100;
          } else if (ch == symbols->perMille) {
            if (multiplier != 1)
              return "too many percent/permille symbols";
            multiplier = 1000;
          }
        }
        *affix++ = ch;
        break;
      case PATTERN_PHASE:
        if (inPositive) {
          /* Process the digits, decimal, and grouping characters.  We
           * record five pieces of information.  We expect the digits
           * to occur in the pattern ####0000.####, and we record the
           * number of left digits, zero (central) digits, and right
           * digits.  The position of the last grouping character is
           * recorded (should be somewhere within the first two blocks
           * of characters), as is the position of the decimal point,
           * if any (should be in the zero digits).  If there is no
           * decimal point, then there should be no right digits. */
          if (ch == symbols->digit) {
            if (zeroDigitCount > 0)
              digitRightCount++;
            else
              digitLeftCount++;
            if (groupingCount >= 0 && decimalPos < 0)
              groupingCount++;
          } else if (ch == symbols->zeroDigit) {
            if (digitRightCount > 0)
              return "unexpected zero digit";
            zeroDigitCount++;
            if (groupingCount >= 0 && decimalPos < 0)
              groupingCount++;
          } else if (ch == symbols->groupingSeparator) {
            groupingCount = 0;
          } else if (ch == symbols->decimalSeparator) {
            if (decimalPos >= 0)
              return "multiple decimal separators";
            decimalPos = digitLeftCount + zeroDigitCount + digitRightCount;
          } else {
            /* Save this position as start of suffix */
            suffix = pattern + pos;
            affix = suffix;
            phase = SUFFIX_PHASE;
            pos--;
            continue;
          }
        } else {
          /* Phase one must be identical in the two sub-patterns.  We
           * enforce this by doing a direct comparison.  While
           * processing the second, we compare characters. */
          if (ch != pattern[phaseOneStart + phaseOneLength])
            return "subpattern mismatch";

          /* Ignore formating in the negative pattern */
          if (ch == symbols->digit ||
              ch == symbols->zeroDigit ||
              ch == symbols->groupingSeparator ||
              ch == symbols->decimalSeparator) {
            phaseOneLength++;
          } else {
            suffix = pattern + pos;
            affix = suffix;
            phase = SUFFIX_PHASE;
            pos--;
            continue;
          }
        }
        break;
      }
    } /* subpattern for-loop */

    /* Handle patterns with no '0' pattern character.  These patterns
     * are legal, but must be interpreted.  "##.###" -> "#0.###".
     * ".###" -> ".0##".
     * We allow patterns of the form "####" to produce a zeroDigitCount of
     * zero (got that?); although this seems like it might make it possible
     * for format() to produce empty strings, format() checks for this
     * condition and outputs a zero digit in this situation.  Having a
     * zeroDigitCount of zero yields a minimum integer digits of zero, which
     * allows proper round-trip patterns.  That is, we don't want "#" to
     * become "#0" when toPattern() is called (even though that's what it
     * really is, semantically).  */
    if (zeroDigitCount == 0 && digitLeftCount > 0 && decimalPos >= 0) {
      /* Handle "###.###" and "###." and ".###" */
      int n = decimalPos;
      if (n == 0) ++n; /* Handle ".###" */
      digitRightCount = digitLeftCount - n;
      digitLeftCount = n - 1;
      zeroDigitCount = 1;
    }

    /* Do syntax checking on the digits. */
    if ((decimalPos < 0 && digitRightCount > 0) ||
        (decimalPos >= 0 && (decimalPos < digitLeftCount ||
                             decimalPos > (digitLeftCount + zeroDigitCount))) ||
        groupingCount == 0 || inQuote)
      return "malformed pattern";

    if (inPositive) {
      int digitTotalCount = digitLeftCount + zeroDigitCount + digitRightCount;
      int effectiveDecimalPos = decimalPos >= 0 ? decimalPos : digitTotalCount;
      if (prefix != prefixEnd) {
        info->positive.prefix = prefix;
        info->positive.prefixSize = prefixEnd - prefix;
      }
      if (suffix != suffixEnd) {
        info->positive.suffix = suffix;
        info->positive.suffixSize = suffixEnd - suffix;
      }
      /* The effectiveDecimalPos is the position the decimal is at or
       * would be at if there is no decimal.  Note that if decimalPos<0,
       * then digitTotalCount == digitLeftCount + zeroDigitCount.  */
      info->minIntegerDigits = effectiveDecimalPos - digitLeftCount;
      info->maxIntegerDigits = DOUBLE_INTEGER_DIGITS;
      if (decimalPos >= 0) {
        info->maxFractionDigits = digitTotalCount - decimalPos;
        info->minFractionDigits = digitLeftCount + zeroDigitCount - decimalPos;
      } else {
        info->minFractionDigits = 0;
        info->maxFractionDigits = 0;
      }
      info->groupingUsed = (groupingCount > 0);
      info->groupingSize = (groupingCount > 0) ? groupingCount : 0;
      info->showDecimalPoint = (decimalPos == 0 ||
                                decimalPos == digitTotalCount);
      info->multiplier = multiplier;
    } else {
      if (prefix != prefixEnd) {
        info->negative.prefix = prefix;
        info->negative.prefixSize = prefixEnd - prefix;
      }
      if (suffix != suffixEnd) {
        info->negative.suffix = suffix;
        info->negative.suffixSize = suffixEnd - suffix;
      }
    }

    inPositive--;
  } while (hasNegative--);

  return NULL; /* SUCCESS */
}

void parse_number(double number, int maximumDigits, DigitList *dl)
{
  int i;
  int printedDigits;
  char ch;
  char nonZeroFound = 0;  /* boolean */
  char rounding;
  int zerosSkipped = 0;

  /* One more decimal digit than required for rounding */
  printedDigits = PyOS_snprintf(dl->digits, DOUBLE_FRACTION_DIGITS, "%.*f",
                                maximumDigits + 1, number);

  dl->decimalAt = -1;
  dl->count = 0;
  for (i = 0; i < printedDigits; i++) {
    ch = dl->digits[i];
    if (ch == '.') {
      dl->decimalAt = dl->count;
      zerosSkipped = 0;
    } else {
      if (!nonZeroFound) {
        nonZeroFound = (ch != '0'); zerosSkipped ++;
      }
      if (nonZeroFound) {
        dl->digits[dl->count++] = ch - '0';
      }
    }
  }

  if (zerosSkipped != 0) {
    dl->decimalAt -= (zerosSkipped - 1);
  }

  i = dl->count;
  rounding = 0;
  do {
    i--;
    if (!rounding && dl->digits[i] >= 5) {
      rounding = 1;
    } else if (rounding) {
      if (dl->digits[i] == 9) {
        /* continue rounding up */
        dl->digits[i] = 0;
      } else {
        dl->digits[i]++;
        rounding = 0;
      }
    }
  } while (rounding);


  /* Remove the rounding digit */
  dl->count--;

  /* Remove any trailing zeros from the decimal part */
  for (i = dl->count-1; i > dl->decimalAt; i--) {
    if (dl->digits[i] == 0)
      dl->count--;
    else
      break;
  }
}

static PyObject *format_number(double number, FormatInfo *info,
                               DecimalFormatSymbols *symbols)
{
  DigitList digitList;
  Py_UNICODE temp[DOUBLE_FRACTION_DIGITS*2];
  int i, count, digitIndex = 0;
  size_t pos = 0;
  char fractionPresent; /* boolean */

  /* allocate a new unicode object large enough to hold formatter number */

  parse_number(number, info->maxFractionDigits, &digitList);

  count = info->minIntegerDigits;

  if (digitList.decimalAt > 0 && count < digitList.decimalAt)
    count = digitList.decimalAt;

  /* Handle the case where maxIntegerDigits is smaller
    * than the real number of integer digits.  If this is so, we
    * output the least significant max integer digits.  For example,
    * the value 1997 printed with 2 max integer digits is just "97". */
  if (count > info->maxIntegerDigits) {
    count = info->maxIntegerDigits;
    digitIndex = digitList.decimalAt - count;
  }

  for (i = count - 1; i >= 0; i--) {
    if (i < digitList.decimalAt && digitIndex < digitList.count)
      /* Output a real digit */
      temp[pos++] = digitList.digits[digitIndex++] + symbols->zeroDigit;
    else
      /* Output a leading zero */
      temp[pos++] = symbols->zeroDigit;

    /* Output grouping separator if necessary.  Don't output a
      * grouping separator if i==0 though; that's at the end of
      * the integer part. */
    if (info->groupingUsed && i > 0 && (info->groupingSize != 0) &&
        (i % info->groupingSize == 0))
      temp[pos++] = symbols->groupingSeparator;
  }

  /* Determine whether or not there are any printable fractional
    * digits.  If we've used up the digits we know there aren't. */
  fractionPresent = ((info->minFractionDigits > 0) ||
                      (digitIndex < digitList.count));

  /* If there is no fraction present, and we haven't printed any
    * integer digits, then print a zero.  Otherwise we won't print
    * _any_ digits, and we won't be able to parse this string. */
  if (!fractionPresent && pos == 0) {
    temp[pos++] = symbols->zeroDigit;
  }

  /* Output the decimal separator if we always do so. */
  if (info->showDecimalPoint || fractionPresent) {
    temp[pos++] = symbols->decimalSeparator;
  }

  for (i = 0; i < info->maxFractionDigits; i++) {
    /* Here is where we escape from the loop.  We escape if we've output
      * the maximum fraction digits (specified in the for expression above).
      * We also stop when we've output the minimum digits and either:
      * we have an integer, so there is no fractional stuff to display,
      * or we're out of significant digits. */
    if (i >= info->minFractionDigits && (digitIndex >= digitList.count))
      break;

    /* Output leading fractional zeros.  These are zeros that come after
      * the decimal but before any significant digits.  These are only
      * output if abs(number being formatted) < 1.0. */
    if (-1 - i > (digitList.decimalAt - 1)) {
      temp[pos++] = symbols->zeroDigit;
      continue;
    }
    /* Output a digit, if we have any precision left, or a
      * zero if we don't.  We don't want to output noise digits. */
    if (digitIndex < digitList.count)
      temp[pos++] = digitList.digits[digitIndex++] + symbols->zeroDigit;
    else
      temp[pos++] = symbols->zeroDigit;
  }

  return PyUnicode_FromUnicode(temp, pos);
}

/** Module Methods ****************************************************/

static char decimal_format_doc[] = "\
decimal_format(number, pattern[, symbols]) -> string\n\
\n\
Converts the `number` argument to a string using the format pattern string\n\
from the `pattern` argument.  The `symbols` argument is a 10-item tuple which\n\
specifies the special characters used from interpreting the format pattern.\n\
The tuple format is (decimal-separator, grouping-separator, infinity,\n\
minus-sign, NaN, percent, per-mille, zero-digit, digit, pattern-separator).\n\
See the XSLT 1.0 Recommendation Section 12.3 for the meanings of these.";

static PyObject *decimal_format(PyObject *self, PyObject *args)
{
  PyObject *pattern, *format=Py_None;
  PyObject *negativePattern = NULL;
  PyObject *infinity = NULL;
  PyObject *not_a_number = NULL;
  PyObject *numberString;

  char *errormsg;

  double number;
  FormatInfo info;
  DecimalFormatSymbols symbols;
  PatternParts *parts;

  PyObject *result=NULL;
  Py_UNICODE *p;
  Py_ssize_t numberSize;

  /* boolean */
  char isNegative;

  /* initialize default symbols */

  if (!PyArg_ParseTuple(args, "dU|O", &number, &pattern, &format))
    return NULL;
  if (format == Py_None) {
    symbols.decimalSeparator = '.';
    symbols.groupingSeparator = ',';
    symbols.minus = '-';
    symbols.percent = '%';
    symbols.perMille = 0x2030;
    symbols.zeroDigit = '0';
    symbols.digit = '#';
    symbols.separator = ';';
    infinity = PyUnicode_DecodeASCII("Infinity", 8, NULL);
    not_a_number = PyUnicode_DecodeASCII("NaN", 3, NULL);
    if (infinity == NULL || not_a_number == NULL) {
      Py_XDECREF(infinity);
      Py_XDECREF(not_a_number);
      return NULL;
    }
  } else {
    if (!unpack_format(format, "argument 3", &symbols, &infinity, &not_a_number))
      return NULL;
  }

  if (isnan(number)) {
    Py_DECREF(infinity);
    return not_a_number;
  }

  /* start out clean */
  info.positive.prefix = info.positive.suffix = NULL;
  info.positive.prefixSize = info.positive.suffixSize = 0;
  info.negative.prefix = info.negative.suffix = NULL;
  info.negative.prefixSize = info.negative.suffixSize = 0;

  if (PyUnicode_GET_SIZE(pattern) > 0) {
    errormsg = parse_pattern(pattern, &info, &symbols);
  } else {
    errormsg = "missing integer portion";
  }
  if (errormsg) {
    PyObject *repr = PyObject_Repr(pattern);
    if (repr) {
      PyErr_Format(PyExc_SyntaxError, "%s in pattern %s", errormsg,
                   PyString_AsString(repr));
      Py_DECREF(repr);
    } else {
      PyErr_SetString(PyExc_SyntaxError, errormsg);
    }
    /* There was an error while parsing pattern */
    Py_DECREF(infinity);
    Py_DECREF(not_a_number);
    return NULL;
  }

  /* Detecting whether a double is negative is easy with the exception of
   * the value -0.0.  This is a double which has a zero mantissa (and
   * exponent), but a negative sign bit.  It is semantically distinct from
   * a zero with a positive sign bit, and this distinction is important
   * to certain kinds of computations.  However, it's a little tricky to
   * detect, since (-0.0 == 0.0) and !(-0.0 < 0.0).  How then, you may
   * ask, does it behave distinctly from +0.0?  Well, 1/(-0.0) == -Inf. */

  isNegative = ((number < 0.0) || (number == 0.0 && 1/number) < 0.0);

  if (isNegative) {
    number = -number;
    parts = &info.negative;
    if (!info.negative.prefix && !info.negative.suffix) {
      negativePattern =
        PyUnicode_FromUnicode(NULL, PyUnicode_GET_SIZE(pattern)+1);
      p = PyUnicode_AS_UNICODE(negativePattern);
      *p++ = symbols.minus;
      Py_UNICODE_COPY(p, PyUnicode_AS_UNICODE(pattern),
                      PyUnicode_GET_SIZE(pattern));

      info.negative.prefix = PyUnicode_AS_UNICODE(negativePattern);
      info.negative.prefixSize = 1;
      if (info.positive.prefix) {
        p = PyUnicode_AS_UNICODE(pattern);
        info.negative.prefix += info.positive.prefix - p + 1;
      }
      if (info.positive.suffix) {
          info.negative.suffix = PyUnicode_AS_UNICODE(negativePattern);
        p = PyUnicode_AS_UNICODE(pattern);
        info.negative.suffix += info.positive.suffix - p + 1;
      }
    }
  } else {
    parts = &info.positive;
  }

  /* Make sure the result string starts empty */

  if (isinf(number)) {
    numberString = infinity;
    Py_INCREF(infinity);
  } else {
    /* mutate for percent/per-mille */
    if (info.multiplier != 1)
        number *= info.multiplier;
    numberString = format_number(number, &info, &symbols);
  }
  numberSize = PyUnicode_GetSize(numberString);

  /* by passing NULL as the unicode data, we create an empty Unicode object
   * of the specified size.
   */

  result = PyUnicode_FromUnicode(NULL, numberSize + parts->prefixSize + parts->suffixSize);
  if (result == NULL) {
    Py_XDECREF(negativePattern);
    Py_DECREF(numberString);
    Py_DECREF(infinity);
    Py_DECREF(not_a_number);
    return NULL;
  }
  p = PyUnicode_AS_UNICODE(result);
  if (parts->prefix) {
    Py_UNICODE_COPY(p, parts->prefix, parts->prefixSize);
    p += parts->prefixSize;
  }
  Py_UNICODE_COPY(p, PyUnicode_AS_UNICODE(numberString), numberSize);
  if (parts->suffix) {
    /* suffix is the start index of the suffix */
    p += numberSize;
    Py_UNICODE_COPY(p, parts->suffix, parts->suffixSize);
  }
  Py_XDECREF(negativePattern);
  Py_DECREF(numberString);
  Py_DECREF(infinity);
  Py_DECREF(not_a_number);
  return result;
}

static PyMethodDef module_methods[] = {
  { "decimal_format", decimal_format, METH_VARARGS, decimal_format_doc },
  { NULL }
};

PyMODINIT_FUNC MODULE_INITFUNC(void)
{
    PyObject *module;

    module = Py_InitModule3(MODULE_NAME, module_methods, module_doc);
};
