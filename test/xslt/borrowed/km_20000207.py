########################################################################
# test/xslt/km_20000207.py
# Extrapolated from an example from Michael Kay to ??? on 7 Feb 2000, 
# with numerous corrections: well-formedness and semantics

import os
import cStringIO
import unittest

from amara.lib import treecompare
from amara.test import test_main
from amara.test.xslt import xslt_test, filesource, stringsource

class test_xslt_row_num_km_20000207(xslt_test):
    source = ""
    transform = stringsource("""<xsl:transform
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 version="1.0"
>

<xsl:output method='html'/>

<xsl:template match="/">
  <table>
    <xsl:apply-templates/>
  </table>
</xsl:template>

<xsl:template match="table">
    <xsl:call-template name="one-row">
      <xsl:with-param name="row-num" select="1"/>
    </xsl:call-template>
</xsl:template>

<!-- From Michael Kay -->
<xsl:template name="one-row">
  <xsl:param name="row-num" select="1"/>
  <tr>
  <xsl:for-each select="row">
     <td><xsl:value-of select="*[$row-num]"/></td>
  </xsl:for-each>
  </tr>
  <xsl:if test="row/*[$row-num+1]">
    <xsl:call-template name="one-row">
      <xsl:with-param name="row-num" select="$row-num+1"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>
<!-- END From Michael Kay -->

</xsl:transform>""")
    parameters = {}
    expected = """<table>
  <tr>
    <td>1</td>
    <td>11</td>
    <td>21</td>
    <td>31</td>
    <td>41</td>
    <td>51</td>
    <td>61</td>
    <td>71</td>
    <td>81</td>
    <td>91</td>
  </tr>
  <tr>
    <td>2</td>
    <td>12</td>
    <td>22</td>
    <td>32</td>
    <td>42</td>
    <td>52</td>
    <td>62</td>
    <td>72</td>
    <td>82</td>
    <td>92</td>
  </tr>
  <tr>
    <td>3</td>
    <td>13</td>
    <td>23</td>
    <td>33</td>
    <td>43</td>
    <td>53</td>
    <td>63</td>
    <td>73</td>
    <td>83</td>
    <td>93</td>
  </tr>
  <tr>
    <td>4</td>
    <td>14</td>
    <td>24</td>
    <td>34</td>
    <td>44</td>
    <td>54</td>
    <td>64</td>
    <td>74</td>
    <td>84</td>
    <td>94</td>
  </tr>
  <tr>
    <td>5</td>
    <td>15</td>
    <td>25</td>
    <td>35</td>
    <td>45</td>
    <td>55</td>
    <td>65</td>
    <td>75</td>
    <td>85</td>
    <td>95</td>
  </tr>
  <tr>
    <td>6</td>
    <td>16</td>
    <td>26</td>
    <td>36</td>
    <td>46</td>
    <td>56</td>
    <td>66</td>
    <td>76</td>
    <td>86</td>
    <td>96</td>
  </tr>
  <tr>
    <td>7</td>
    <td>17</td>
    <td>27</td>
    <td>37</td>
    <td>47</td>
    <td>57</td>
    <td>67</td>
    <td>77</td>
    <td>87</td>
    <td>97</td>
  </tr>
  <tr>
    <td>8</td>
    <td>18</td>
    <td>28</td>
    <td>38</td>
    <td>48</td>
    <td>58</td>
    <td>68</td>
    <td>78</td>
    <td>88</td>
    <td>98</td>
  </tr>
  <tr>
    <td>9</td>
    <td>19</td>
    <td>29</td>
    <td>39</td>
    <td>49</td>
    <td>59</td>
    <td>69</td>
    <td>79</td>
    <td>89</td>
    <td>99</td>
  </tr>
  <tr>
    <td>10</td>
    <td>20</td>
    <td>30</td>
    <td>40</td>
    <td>50</td>
    <td>60</td>
    <td>70</td>
    <td>80</td>
    <td>90</td>
    <td>100</td>
  </tr>
</table>"""

    def test_transform(self):
        SIZE=10
        
        import sys
        from amara.xslt import transform

        #Create the matrix to be transposed
        from Ft.Xml.Domlette import implementation
        doc = implementation.createDocument(None, 'table', None)
        counter = 1
        for row in range(SIZE):
            row_elem = doc.createElementNS(None, 'row')
            doc.documentElement.appendChild(row_elem)
            for col in range(SIZE):
                col_elem = doc.createElementNS(None, 'column')
                row_elem.appendChild(col_elem)
                content = doc.createTextNode(str(counter))
                col_elem.appendChild(content)
                counter = counter + 1

        stream = cStringIO.StringIO()
        from Ft.Xml.Domlette import Print
        Print(doc,stream)

        self.source = stringsource(stream.getvalue())
        result = transform(self.source, self.transform, output=io)
        self.assert_(treecompare.html_compare(self.expected, io.getvalue()))
        return

if __name__ == '__main__':
    test_main()
