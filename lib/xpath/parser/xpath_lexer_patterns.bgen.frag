<?xml version="1.0"?>
<fragment>
    <states>
      <exclusive>OPERATOR</exclusive>
    </states>

    <scope state='OPERATOR'>
      <pattern expression='or'>
        <begin>INITIAL</begin>
        <token>OR_OP</token>
      </pattern>

      <pattern expression='and'>
        <begin>INITIAL</begin>
        <token>AND_OP</token>
      </pattern>

      <pattern expression='\*|mod|div'>
        <begin>INITIAL</begin>
        <token>MULTIPLICATIVE_OP</token>
      </pattern>

      <!-- ignore whitespace, defined here for speed -->
      <pattern expression='{S}+'/>

      <pattern expression='.'>
        <begin>INITIAL</begin>
      </pattern>
    </scope>

    <pattern expression='\)|\]'>
      <begin>OPERATOR</begin>
      <token>@ASCII@</token>
    </pattern>

    <pattern expression='::'>
      <token>DOUBLE_COLON</token>
    </pattern>

    <pattern expression='"//"'>
      <token>DOUBLE_SLASH</token>
    </pattern>

    <pattern expression='=|!='>
      <token>EQUALITY_OP</token>
    </pattern>

    <pattern expression='&lt;=|&lt;|&gt;=|&gt;'>
      <token>RELATIONAL_OP</token>
    </pattern>

    <!-- node types -->
    <pattern expression='{NodeType}/{S}*\('>
      <token>NodeType</token>
    </pattern>

    <!-- axis specifiers -->
    <pattern expression='{NCName}/{S}*::'>
      <token>AxisName</token>
    </pattern>

    <!-- primary expressions -->
    <pattern expression='{Literal}'>
      <begin>OPERATOR</begin>
      <token>Literal</token>
    </pattern>

    <pattern expression='({Digits}(\.({Digits})?)?)|(\.{Digits})'>
      <begin>OPERATOR</begin>
      <token>Number</token>
    </pattern>

    <pattern expression='\${QName}'>
      <begin>OPERATOR</begin>
      <token>VariableReference</token>
    </pattern>

    <pattern expression='{QName}/{S}*\('>
      <token>FunctionName</token>
    </pattern>

    <pattern expression='({NCName}:\*)|({QName})|\*'>
      <begin>OPERATOR</begin>
      <token>NameTest</token>
    </pattern>

    <pattern expression='".."'>
      <begin>OPERATOR</begin>
      <token>DOUBLE_DOT</token>
    </pattern>

    <!-- needs to be separate since what follows could be an operator name -->
    <pattern expression='"."'>
      <begin>OPERATOR</begin>
      <token>@ASCII@</token>
    </pattern>

    <!-- ignore all whitespace -->
    <pattern expression='{S}+'/>

</fragment>