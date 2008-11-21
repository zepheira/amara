########################################################################
# amara/xslt/tree/number_element.py
"""
Implementation of the `xsl:number` element.
"""

from amara import tree
from amara.namespaces import XSL_NAMESPACE
from amara.xslt import XsltError, numbers
from amara.xslt.tree import xslt_element, content_model, attribute_types

DEFAULT_LANG = 'en'
DEFAULT_FORMAT = '1'

SINGLE = 0
MULTIPLE = 1
ANY = 2
SIMPLE = 3  # no count or from

class number_element(xslt_element):

    content_model = content_model.empty
    attribute_types = {
        'level': attribute_types.choice(('single', 'multiple', 'any'),
                                        default='single'),
        'count': attribute_types.pattern(),
        'from': attribute_types.pattern(),
        'value': attribute_types.expression(),
        'format': attribute_types.string_avt(default='1'),
        'lang': attribute_types.nmtoken_avt(),
        'letter-value': attribute_types.choice_avt(('alphabetic',
                                                    'traditional'),
                                                   default='traditional'),
        'grouping-separator': attribute_types.char_avt(),
        'grouping-size': attribute_types.number_avt(),
        }

    def setup(self):
        if self._level == 'single':
            if not self._count and not self._from:
                self._level = SIMPLE
            else:
                self._level = SINGLE
        elif self._level == 'multiple':
            self._level = MULTIPLE
        elif self._level == 'any':
            self._level = ANY

        if self._format.constant and self._lang.constant:
            format = self._format.evaluate_as_string(None)
            lang = self._lang.evaluate_as_string(None)
            self._formatter = numbers.formatter(lang, format)
        else:
            self._formatter = None
        return

    def instantiate(self, context):
        context.instruction = self
        context.namespaces = self.namespaces

        formatter = self._formatter
        if not formatter:
            format = self._format
            if format:
                format = format.evaluate_as_string(context)
            if not format:
                format = DEFAULT_FORMAT
            lang = self._lang
            if lang:
                lang = lang.evaluate_as_string(context)
            if not lang:
                lang = DEFAULT_LANG
            formatter = numbers.formatter(lang, format)

        letter_value = self._letter_value.evaluate_as_string(context)
        if self._grouping_separator and self._grouping_size:
            separator = self._grouping_separator.evaluate_as_string(context)
            grouping = int(self._grouping_size.evaluate_as_number(context))
        else:
            separator = grouping = None

        # get the formatted value(s)
        if self._value:
            value = self._value.evaluate_as_number(context)
            # XSLT 1.0, Section 7.7, Paragraph 1
            # ERROR: the number is NaN, infinite or less than 0.5
            # RECOVERY: convert to string and insert into the result tree
            if not value.isfinite() or value < 0.5:
                result = datatypes.string(value)
            else:
                value = int(round(value))
                result = formatter.format(value, letter_value, grouping,
                                          separator)
        else:
            node = context.node
            if self._level == SINGLE:
                value = self._single_value(context, node, self._count,
                                           self._from)
                if value == 0:
                    value = None
                result = formatter.format(value, letter_value, separator,
                                          grouping)
            elif self._level == MULTIPLE:
                values = self._multiple_values(context, node)
                result = formatter.formatmany(values, letter_value, grouping,
                                              separator)
            elif self._level == ANY:
                value = self._any_value(context, node)
                if value == 0:
                    value = None
                result = formatter.format(value, letter_value, grouping,
                                          separator)
            else:
                # 'single' without count or from attributes
                value = 1
                prev = node.xml_preceding_sibling
                node_type = node.xml_type
                node_name = node.xml_name
                while prev:
                    if prev.xml_type == node_type and \
                       prev.xml_name == node_name:
                        value += 1
                    prev = prev.xml_preceding_sibling
                result = formatter.format(value, letter_value, grouping,
                                          separator)
        # add the resulting formatted value(s) to the result tree
        context.text(result)
        return

    def _single_value(self, context, node, countPattern, fromPattern):
        if not countPattern:
            if not node.xml_local:
                # text, comment and processing instruction
                countPattern = NodeTypeTest(node)
            else:
                countPattern = NameTest(node)

        if fromPattern:
            start = node.xml_parent
            while start and not fromPattern.match(context, start):
                start = start.xml_parent
        else:
            start = node.xml_root

        while not countPattern.match(context, node):
            node = node.xml_parent
            if node is None or node == start:
                return 0

        value = 0
        while node:
            value += 1
            node = node.xml_preceding_sibling
            while node and not countPattern.match(context, node):
                node = node.xml_preceding_sibling
        return value

    def _multiple_values(self, context, node):
        count = self._count
        if not count:
            if isinstance(node, (tree.element, tree.attribute)):
                count = name_pattern(node.xml_type, node.xml_name)
            else:
                count = type_pattern(node.xml_type)

        values = []
        while node:
            if count.match(context, node):
                value = self._single_value(context, node, count,  None)
                values.insert(0, value)
            node = node.xml_parent
            if node and self._from and self._from.match(context, node):
                break
        return values

    def _any_value(self, context, node):
        count = self._count
        if not count:
            if isinstance(node, (tree.element, tree.attribute)):
                count = name_pattern(node.xml_type, node.xml_name)
            else:
                count = type_pattern(node.xml_type)

        value = 0
        while node:
            if self._from and self._from.match(context, node):
                break
            if count.match(context, node):
                value += 1
            next = node.xml_preceding_sibling
            if not next:
                node = node.xml_parent
            else:
                node = next
                next = getattr(node, 'xml_last_child', None)
                while next:
                    node = next
                    next = getattr(node, 'xml_last_child', None)
        return value


class type_pattern:
    def __init__(self, xml_type):
        self.xml_type = xml_type
        return

    def match(self, context, node):
        return (node.xml_type == self.xml_type)


class name_pattern:
    def __init__(self, xml_type, xml_name):
        self.xml_type = xml_type
        self.xml_name = xml_name
        return

    def match(self, context, node):
        return (node.xml_type == self.xml_type and
                node.xml_name == self.xml_name)

##Note: emacs can uncomment the ff automatically.

##To: xsl-list@mulberrytech.com
##Subject: Re: number format test
##From: MURAKAMI Shinyu <murakami@nadita.com>
##Date: Thu, 3 Aug 2000 01:18:10 +0900 (Wed 10:18 MDT)

##Kay Michael <Michael.Kay@icl.com> wrote:
##>> 5. Saxon
##>>   - Fullwidth 1 (#xff11) are supported.
##>>   - Hiragana/Katakana/Kanji format generates incorrect result.
##>>     (Unicode codepoint order, such as #x3042, #x3043, #x3044,...)
##>>     useless and trouble with Non-European style processing.
##>>     fix it please!!
##>
##>If you could tell me what the correct sequence is, I'll be happy to include
##>it. Help me please!


##XSLT 1.0 spec says:

##    7.7.1 Number to String Conversion Attributes
##    ...

##    - Any other format token indicates a numbering sequence that starts
##      with that token.  If an implementation does not support a numbering
##      sequence that starts with that token, it must use a format token of 1.

##The last sentence is important.  ...it must use a format token of 1.

##If Saxon will support... the following are Japanese Hiragana/Katakana sequences
##-- modern(A...) and traditional(I...) -- and Kanji(CJK ideographs) numbers.

##format="&#x3042;" (Hiragana A)
##&#x3042;&#x3044;&#x3046;&#x3048;&#x304a;&#x304b;&#x304d;&#x304f;&#x3051;&#x3053;
##&#x3055;&#x3057;&#x3059;&#x305b;&#x305d;&#x305f;&#x3061;&#x3064;&#x3066;&#x3068;
##&#x306a;&#x306b;&#x306c;&#x306d;&#x306e;&#x306f;&#x3072;&#x3075;&#x3078;&#x307b;
##&#x307e;&#x307f;&#x3080;&#x3081;&#x3082;&#x3084;&#x3086;&#x3088;&#x3089;&#x308a;
##&#x308b;&#x308c;&#x308d;&#x308f;&#x3092;&#x3093;

##format="&#x30a2;" (Katakana A)
##&#x30a2;&#x30a4;&#x30a6;&#x30a8;&#x30aa;&#x30ab;&#x30ad;&#x30af;&#x30b1;&#x30b3;
##&#x30b5;&#x30b7;&#x30b9;&#x30bb;&#x30bd;&#x30bf;&#x30c1;&#x30c4;&#x30c6;&#x30c8;
##&#x30ca;&#x30cb;&#x30cc;&#x30cd;&#x30ce;&#x30cf;&#x30d2;&#x30d5;&#x30d8;&#x30db;
##&#x30de;&#x30df;&#x30e0;&#x30e1;&#x30e2;&#x30e4;&#x30e6;&#x30e8;&#x30e9;&#x30ea;
##&#x30eb;&#x30ec;&#x30ed;&#x30ef;&#x30f2;&#x30f3;

##format="&#x3044;" (Hiragana I)
##&#x3044;&#x308d;&#x306f;&#x306b;&#x307b;&#x3078;&#x3068;&#x3061;&#x308a;&#x306c;
##&#x308b;&#x3092;&#x308f;&#x304b;&#x3088;&#x305f;&#x308c;&#x305d;&#x3064;&#x306d;
##&#x306a;&#x3089;&#x3080;&#x3046;&#x3090;&#x306e;&#x304a;&#x304f;&#x3084;&#x307e;
##&#x3051;&#x3075;&#x3053;&#x3048;&#x3066;&#x3042;&#x3055;&#x304d;&#x3086;&#x3081;
##&#x307f;&#x3057;&#x3091;&#x3072;&#x3082;&#x305b;&#x3059;

##format="&#x30a4;" (Katakana I)
##&#x30a4;&#x30ed;&#x30cf;&#x30cb;&#x30db;&#x30d8;&#x30c8;&#x30c1;&#x30ea;&#x30cc;
##&#x30eb;&#x30f2;&#x30ef;&#x30ab;&#x30e8;&#x30bf;&#x30ec;&#x30bd;&#x30c4;&#x30cd;
##&#x30ca;&#x30e9;&#x30e0;&#x30a6;&#x30f0;&#x30ce;&#x30aa;&#x30af;&#x30e4;&#x30de;
##&#x30b1;&#x30d5;&#x30b3;&#x30a8;&#x30c6;&#x30a2;&#x30b5;&#x30ad;&#x30e6;&#x30e1;
##&#x30df;&#x30b7;&#x30f1;&#x30d2;&#x30e2;&#x30bb;&#x30b9;

##format="&#x4e00;" (Kanji 1) (decimal notation)
##&#x4e00;(=1) &#x4e8c;(=2) &#x4e09;(=3) &#x56db;(=4) &#x4e94;(=5)
##&#x516d;(=6) &#x4e03;(=7) &#x516b;(=8) &#x4e5d;(=9) &#x3007;(=0)
##e.g. &#x4e00;&#x3007;(=10)  &#x4e8c;&#x4e94;&#x516d;(=256)
##There are more ideographic(kanji)-number formats, but the above will be sufficient.


##Thanks,
##MURAKAMI Shinyu
##murakami@nadita.com


