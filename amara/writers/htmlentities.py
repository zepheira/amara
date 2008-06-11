########################################################################
# amara/writers/htmlentities.py
"""
This module defines the entities for HTML 3.2, HTML 4.0 and XHTML 1.0.
"""

__all__ = ['ENTITIES_HTML_32', 'ENTITIES_HTML_40', 'ENTITIES_XHTML_10']

# HTML 3.2 defined character entities
ENTITIES_HTML_32 = {
    # Sect 24.2 -- ISO 8859-1
    u'\u00A0' : '&nbsp;',
    u'\u00A1' : '&iexcl;',
    u'\u00A2' : '&cent;',
    u'\u00A3' : '&pound;',
    u'\u00A4' : '&curren;',
    u'\u00A5' : '&yen;',
    u'\u00A6' : '&brvbar;',
    u'\u00A7' : '&sect;',
    u'\u00A8' : '&uml;',
    u'\u00A9' : '&copy;',
    u'\u00AA' : '&ordf;',
    u'\u00AB' : '&laquo;',
    u'\u00AC' : '&not;',
    u'\u00AD' : '&shy;',
    u'\u00AE' : '&reg;',
    u'\u00AF' : '&macr;',
    u'\u00B0' : '&deg;',
    u'\u00B1' : '&plusmn;',
    u'\u00B2' : '&sup2;',
    u'\u00B3' : '&sup3;',
    u'\u00B4' : '&acute;',
    u'\u00B5' : '&micro;',
    u'\u00B6' : '&para;',
    u'\u00B7' : '&middot;',
    u'\u00B8' : '&cedil;',
    u'\u00B9' : '&sup1;',
    u'\u00BA' : '&ordm;',
    u'\u00BB' : '&raquo;',
    u'\u00BC' : '&frac14;',
    u'\u00BD' : '&frac12;',
    u'\u00BE' : '&frac34;',
    u'\u00BF' : '&iquest;',
    u'\u00C0' : '&Agrave;',
    u'\u00C1' : '&Aacute;',
    u'\u00C2' : '&Acirc;',
    u'\u00C3' : '&Atilde;',
    u'\u00C4' : '&Auml;',
    u'\u00C5' : '&Aring;',
    u'\u00C6' : '&AElig;',
    u'\u00C7' : '&Ccedil;',
    u'\u00C8' : '&Egrave;',
    u'\u00C9' : '&Eacute;',
    u'\u00CA' : '&Ecirc;',
    u'\u00CB' : '&Euml;',
    u'\u00CC' : '&Igrave;',
    u'\u00CD' : '&Iacute;',
    u'\u00CE' : '&Icirc;',
    u'\u00CF' : '&Iuml;',
    u'\u00D0' : '&ETH;',
    u'\u00D1' : '&Ntilde;',
    u'\u00D2' : '&Ograve;',
    u'\u00D3' : '&Oacute;',
    u'\u00D4' : '&Ocirc;',
    u'\u00D5' : '&Otilde;',
    u'\u00D6' : '&Ouml;',
    u'\u00D7' : '&times;',
    u'\u00D8' : '&Oslash;',
    u'\u00D9' : '&Ugrave;',
    u'\u00DA' : '&Uacute;',
    u'\u00DB' : '&Ucirc;',
    u'\u00DC' : '&Uuml;',
    u'\u00DD' : '&Yacute;',
    u'\u00DE' : '&THORN;',
    u'\u00DF' : '&szlig;',
    u'\u00E0' : '&agrave;',
    u'\u00E1' : '&aacute;',
    u'\u00E2' : '&acirc;',
    u'\u00E3' : '&atilde;',
    u'\u00E4' : '&auml;',
    u'\u00E5' : '&aring;',
    u'\u00E6' : '&aelig;',
    u'\u00E7' : '&ccedil;',
    u'\u00E8' : '&egrave;',
    u'\u00E9' : '&eacute;',
    u'\u00EA' : '&ecirc;',
    u'\u00EB' : '&euml;',
    u'\u00EC' : '&igrave;',
    u'\u00ED' : '&iacute;',
    u'\u00EE' : '&icirc;',
    u'\u00EF' : '&iuml;',
    u'\u00F0' : '&eth;',
    u'\u00F1' : '&ntilde;',
    u'\u00F2' : '&ograve;',
    u'\u00F3' : '&oacute;',
    u'\u00F4' : '&ocirc;',
    u'\u00F5' : '&otilde;',
    u'\u00F6' : '&ouml;',
    u'\u00F7' : '&divide;',
    u'\u00F8' : '&oslash;',
    u'\u00F9' : '&ugrave;',
    u'\u00FA' : '&uacute;',
    u'\u00FB' : '&ucirc;',
    u'\u00FC' : '&uuml;',
    u'\u00FD' : '&yacute;',
    u'\u00FE' : '&thorn;',
    u'\u00FF' : '&yuml;',
    }

# HTML 4.01 defined character entities
ENTITIES_HTML_40 = {
    # Sect 24.3 -- Symbols, Mathematical Symbols, and Greek Letters
    # Latin Extended-B
    u'\u0192' : '&fnof;',
    # Greek
    u'\u0391' : '&Alpha;',
    u'\u0392' : '&Beta;',
    u'\u0393' : '&Gamma;',
    u'\u0394' : '&Delta;',
    u'\u0395' : '&Epsilon;',
    u'\u0396' : '&Zeta;',
    u'\u0397' : '&Eta;',
    u'\u0398' : '&Theta;',
    u'\u0399' : '&Iota;',
    u'\u039A' : '&Kappa;',
    u'\u039B' : '&Lambda;',
    u'\u039C' : '&Mu;',
    u'\u039D' : '&Nu;',
    u'\u039E' : '&Xi;',
    u'\u039F' : '&Omicron;',
    u'\u03A0' : '&Pi;',
    u'\u03A1' : '&Rho;',
    u'\u03A3' : '&Sigma;',
    u'\u03A4' : '&Tau;',
    u'\u03A5' : '&Upsilon;',
    u'\u03A6' : '&Phi;',
    u'\u03A7' : '&Chi;',
    u'\u03A8' : '&Psi;',
    u'\u03A9' : '&Omega;',
    u'\u03B1' : '&alpha;',
    u'\u03B2' : '&beta;',
    u'\u03B3' : '&gamma;',
    u'\u03B4' : '&delta;',
    u'\u03B5' : '&epsilon;',
    u'\u03B6' : '&zeta;',
    u'\u03B7' : '&eta;',
    u'\u03B8' : '&theta;',
    u'\u03B9' : '&iota;',
    u'\u03BA' : '&kappa;',
    u'\u03BB' : '&lambda;',
    u'\u03BC' : '&mu;',
    u'\u03BD' : '&nu;',
    u'\u03BE' : '&xi;',
    u'\u03BF' : '&omicron;',
    u'\u03C0' : '&pi;',
    u'\u03C1' : '&rho;',
    u'\u03C2' : '&sigmaf;',
    u'\u03C3' : '&sigma;',
    u'\u03C4' : '&tau;',
    u'\u03C5' : '&upsilon;',
    u'\u03C6' : '&phi;',
    u'\u03C7' : '&chi;',
    u'\u03C8' : '&psi;',
    u'\u03C9' : '&omega;',
    u'\u03D1' : '&thetasym;',
    u'\u03D2' : '&upsih;',
    u'\u03D6' : '&piv;',
    # General Punctuation
    u'\u2022' : '&bull;',      # bullet
    u'\u2026' : '&hellip;',    # horizontal ellipsis
    u'\u2032' : '&prime;',     # prime (minutes/feet)
    u'\u2033' : '&Prime;',     # double prime (seconds/inches)
    u'\u203E' : '&oline;',     # overline (spacing overscore)
    u'\u203A' : '&frasl;',     # fractional slash
    # Letterlike Symbols
    u'\u2118' : '&weierp;',    # script capital P (power set/Weierstrass p)
    u'\u2111' : '&image;',     # blackletter capital I (imaginary part)
    u'\u211C' : '&real;',      # blackletter capital R (real part)
    u'\u2122' : '&trade;',     # trademark
    u'\u2135' : '&alefsym;',   # alef symbol (first transfinite cardinal)
    # Arrows
    u'\u2190' : '&larr;',      # leftwards arrow
    u'\u2191' : '&uarr;',      # upwards arrow
    u'\u2192' : '&rarr;',      # rightwards arrow
    u'\u2193' : '&darr;',      # downwards arrow
    u'\u2194' : '&harr;',      # left right arrow
    u'\u21B5' : '&crarr;',     # downwards arrow with corner leftwards
    u'\u21D0' : '&lArr;',      # leftwards double arrow
    u'\u21D1' : '&uArr;',      # upwards double arrow
    u'\u21D2' : '&rArr;',      # rightwards double arrow
    u'\u21D3' : '&dArr;',      # downwards double arrow
    u'\u21D4' : '&hArr;',      # left right double arrow
    # Mathematical Operators
    u'\u2200' : '&forall;',    # for all
    u'\u2202' : '&part;',      # partial differential
    u'\u2203' : '&exist;',     # there exists
    u'\u2205' : '&empty;',     # empty set, null set, diameter
    u'\u2207' : '&nabla;',     # nabla, backward difference
    u'\u2208' : '&isin;',      # element of
    u'\u2209' : '&notin;',     # not an element of
    u'\u220B' : '&ni;',        # contains as member
    u'\u220F' : '&prod;',      # n-ary product, product sign
    u'\u2211' : '&sum;',       # n-ary sumation
    u'\u2212' : '&minus;',     # minus sign
    u'\u2217' : '&lowast;',    # asterisk operator
    u'\u221A' : '&radic;',     # square root, radical sign
    u'\u221D' : '&prop;',      # proportional to
    u'\u221E' : '&infin;',     # infinity
    u'\u2220' : '&ang;',       # angle
    u'\u2227' : '&and;',       # logical and, wedge
    u'\u2228' : '&or;',        # logical or, vee
    u'\u2229' : '&cap;',       # intersection, cap
    u'\u222A' : '&cup;',       # union, cup
    u'\u222B' : '&int;',       # integral
    u'\u2234' : '&there4;',    # therefore
    u'\u223C' : '&sim;',       # tilde operator, varies with, similar to
    u'\u2245' : '&cong;',      # approximately equal to
    u'\u2248' : '&asymp;',     # almost equal to, asymptotic to
    u'\u2260' : '&ne;',        # not equal to
    u'\u2261' : '&equiv;',     # identical to
    u'\u2264' : '&le;',        # less-than or equal to
    u'\u2265' : '&ge;',        # greater-than or equal to
    u'\u2282' : '&sub;',       # subset of
    u'\u2283' : '&sup;',       # superset of
    u'\u2284' : '&nsub;',      # not subset of
    u'\u2286' : '&sube;',      # subset of or equal to
    u'\u2287' : '&supe;',      # superset of or equal to
    u'\u2295' : '&oplus;',     # circled plus, direct sum
    u'\u2297' : '&otimes;',    # circled times, vector product
    u'\u22A5' : '&perp;',      # up tack, orthogonal to, perpendicular
    u'\u22C5' : '&sdot;',      # dot operator
    u'\u2308' : '&lceil;',     # left ceiling, apl upstile
    u'\u2309' : '&rceil;',     # right ceiling
    u'\u230A' : '&lfloor;',    # left floor, apl downstile
    u'\u230B' : '&rfloor;',    # right floor
    u'\u2329' : '&lang;',      # left-pointing angle bracket, bra
    u'\u232A' : '&rang;',      # right-pointing angle bracket, ket
    u'\u25CA' : '&loz;',       # lozenge
    # Miscellaneous Symbols
    u'\u2660' : '&spades;',
    u'\u2663' : '&clubs;',
    u'\u2665' : '&hearts;',
    u'\u2666' : '&diams;',

    # Sect 24.4 -- Markup Significant and Internationalization
    # Latin Extended-A
    u'\u0152' : '&OElig;',      # capital ligature OE
    u'\u0153' : '&oelig;',      # small ligature oe
    u'\u0160' : '&Scaron;',     # capital S with caron
    u'\u0161' : '&scaron;',     # small s with caron
    u'\u0178' : '&Yuml;',       # capital Y with diaeresis
    # Spacing Modifier Letters
    u'\u02C6' : '&circ;',       # circumflexx accent
    u'\u02DC' : '&tidle;',      # small tilde
    # General Punctuation
    u'\u2002' : '&ensp;',      # en space
    u'\u2003' : '&emsp;',      # em space
    u'\u2009' : '&thinsp;',    # thin space
    u'\u200C' : '&zwnj;',      # zero-width non-joiner
    u'\u200D' : '&zwj;',       # zero-width joiner
    u'\u200E' : '&lrm;',       # left-to-right mark
    u'\u200F' : '&rlm;',       # right-to-left mark
    u'\u2013' : '&ndash;',     # en dash
    u'\u2014' : '&mdash;',     # em dash
    u'\u2018' : '&lsquo;',     # left single quotation mark
    u'\u2019' : '&rsquo;',     # right single quotation mark
    u'\u201A' : '&sbquo;',     # single low-9 quotation mark
    u'\u201C' : '&ldquo;',     # left double quotation mark
    u'\u201D' : '&rdquo;',     # right double quotation mark
    u'\u201E' : '&bdquo;',     # double low-9 quotation mark
    u'\u2020' : '&dagger;',    # dagger
    u'\u2021' : '&Dagger;',    # double dagger
    u'\u2030' : '&permil;',    # per mille sign
    u'\u2039' : '&lsaquo;',    # single left-pointing angle quotation mark
    u'\u203A' : '&rsaquo;',    # single right-pointing angle quotation mark
    u'\u20AC' : '&euro;',      # euro sign
}
ENTITIES_HTML_40.update(ENTITIES_HTML_32)

ENTITIES_XHTML_10 = ENTITIES_HTML_40.copy()
