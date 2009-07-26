########################################################################
# $Header: /var/local/cvsroot/4Suite/Ft/Xml/XPath/MathFunctions.py,v 1.4.6.1 2006-12-04 07:06:59 jkloth Exp $
"""
4XPath-specific math extension functions

Copyright 2005 Fourthought, Inc. (USA).
Detailed license and copyright information: http://4suite.org/COPYRIGHT
Project home, documentation, distributions: http://4suite.org/
"""

import math

from Ft.Xml.XPath import Conversions, FT_EXT_NAMESPACE
from Ft.Xml.XPath import XPathTypes as Types


def Sin(context, x):
    "math.sin"
    return math.sin(Conversions.NumberValue(x))
Sin.arguments = (Types.NumberType,)
Sin.result = Types.NumberType


def Cos(context, x):
    "math.cos"
    return math.cos(Conversions.NumberValue(x))
Cos.arguments = (Types.NumberType,)
Cos.result = Types.NumberType


def DegreesToRads(context, x):
    "Convert degrees to radians"
    return Conversions.NumberValue(x)/180*math.pi
DegreesToRads.arguments = (Types.NumberType,)
DegreesToRads.result = Types.NumberType


def Fact(context, x):
    "Factorial"
    x = Conversions.NumberValue(x)
    if x > 1:
        return reduce(lambda x,y: x*y, xrange(1,x+1), 1)
    return 1
Fact.arguments = (Types.NumberType,)
Fact.result = Types.NumberType


ExtNamespaces = {
    FT_EXT_NAMESPACE : 'f',
    }

ExtFunctions = {
    (FT_EXT_NAMESPACE, 'cos'): Cos,
    (FT_EXT_NAMESPACE, 'sin'): Sin,
    (FT_EXT_NAMESPACE, 'degrees-to-rads'): DegreesToRads,
    (FT_EXT_NAMESPACE, 'fact'): Fact,
    }

