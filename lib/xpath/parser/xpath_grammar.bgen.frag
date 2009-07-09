<?xml version='1.0'?>
<fragment>
<production name="1">
  <non-terminal>LocationPath</non-terminal>
  <rule>
    <symbol>RelativeLocationPath</symbol>
  </rule>
  <rule>
    <symbol>AbsoluteLocationPath</symbol>
  </rule>
</production>

<production name="2">
  <non-terminal>AbsoluteLocationPath</non-terminal>
  <rule>
    <symbol>'/'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(absolute_location_path, "O", Py_None);
    </code>
    <code language="python">
      $$ = absolute_location_path(None)
    </code>
  </rule>
  <rule>
    <symbol>'/'</symbol>
    <symbol>RelativeLocationPath</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(absolute_location_path, "O", $2);
    </code>
    <code language="python">
      $$ = absolute_location_path($2)
    </code>
  </rule>
  <rule>
    <symbol>AbbreviatedAbsoluteLocationPath</symbol>
  </rule>
</production>

<production name="3">
  <non-terminal>RelativeLocationPath</non-terminal>
  <rule>
    <symbol>Step</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(relative_location_path, "O", $1);
    </code>
    <code language="python">
      $$ = relative_location_path($1)
    </code>
  </rule>
  <rule>
    <symbol>RelativeLocationPath</symbol>
    <symbol>'/'</symbol>
    <symbol>Step</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(relative_location_path, "OO", $1, $3);
    </code>
    <code language="python">
      $$ = relative_location_path($1, $3)
    </code>
  </rule>
  <rule>
    <symbol>AbbreviatedRelativeLocationPath</symbol>
  </rule>
</production>

<production name="4">
  <non-terminal>Step</non-terminal>
  <rule>
    <symbol>AxisSpecifier</symbol>
    <symbol>NodeTest</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(location_step, "OO", $1, $2);
    </code>
    <code language="python">
      $$ = location_step($1, $2)
    </code>
  </rule>
  <rule>
    <symbol>AxisSpecifier</symbol>
    <symbol>NodeTest</symbol>
    <symbol>Predicate.list</symbol>
    <code language="c">
      $3 = PyObject_CallFunction(predicates, "N", $3);
      $$ = PyObject_CallFunction(location_step, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = location_step($1, $2, predicates($3))
    </code>
  </rule>
  <rule>
    <symbol>AbbreviatedStep</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(abbreviated_step, "O", $1);
    </code>
    <code language="python">
      $$ = abbreviated_step($1)
    </code>
  </rule>
</production>

<production name="4a">
  <non-terminal>Predicate.list</non-terminal>
  <rule>
    <symbol>Predicate</symbol>
    <code language="c">
      $$ = PyList_New(1);
      Py_INCREF($1);
      /* Steals a reference */
      PyList_SET_ITEM($$, 0, $1);
    </code>
    <code language="python">
      $$ = [$1]
    </code>
  </rule>
  <rule>
    <symbol>Predicate.list</symbol>
    <symbol>Predicate</symbol>
    <code language="c">
      PyList_Append($1, $2);
      Py_INCREF($1);
      $$ = $1;
    </code>
    <code language="python">
      $1.append($2)
      $$ = $1
    </code>
  </rule>
</production>

<production name="5">
  <non-terminal>AxisSpecifier</non-terminal>
  <rule>
    <symbol>AxisName</symbol>
    <symbol>DOUBLE_COLON</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(axis_specifier, "O", $1);
    </code>
    <code language="python">
      $$ = axis_specifier($1)
    </code>
  </rule>
  <rule>
    <symbol>AbbreviatedAxisSpecifier</symbol>
  </rule>
</production>

<!--
<production name="6">
  <non-terminal>AxisName</non-terminal>
  <rule>
    <symbol>AxisName</symbol>
  </rule>
  <code language="python">
  </code>
</production>
-->

<production name="7">
  <non-terminal>NodeTest</non-terminal>
  <rule>
    <symbol>NameTest</symbol>
    <code language="C">
      $$ = PyObject_CallFunction(name_test, "O", $1);
    </code>
    <code language="python">
      $$ = name_test($1)
    </code>
  </rule>
  <rule>
    <symbol>NodeType</symbol>
    <symbol>'('</symbol>
    <symbol>')'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(node_type, "O", $1);
    </code>
    <code language="python">
      $$ = node_type($1)
    </code>
  </rule>
  <rule>
    <symbol>NodeType</symbol>
    <symbol>'('</symbol>
    <symbol>Literal</symbol>
    <symbol>')'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(node_type, "OO", $1, $3);
    </code>
    <code language="python">
      $$ = node_type($1, $3)
    </code>
  </rule>
</production>

<production name="8">
  <non-terminal>Predicate</non-terminal>
  <rule>
    <symbol>'['</symbol>
    <symbol>PredicateExpr</symbol>
    <symbol>']'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(predicate, "O", $2);
    </code>
    <code language="python">
      $$ = predicate($2)
    </code>
  </rule>
</production>

<production name="9">
  <non-terminal>PredicateExpr</non-terminal>
  <rule>
    <symbol>Expr</symbol>
  </rule>
</production>

<production name="10">
  <non-terminal>AbbreviatedAbsoluteLocationPath</non-terminal>
  <rule>
    <symbol>DOUBLE_SLASH</symbol>
    <symbol>RelativeLocationPath</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(abbreviated_absolute_location_path, "O", $2);
    </code>
    <code language="python">
      $$ = abbreviated_absolute_location_path($2)
    </code>
  </rule>
</production>

<production name="11">
  <non-terminal>AbbreviatedRelativeLocationPath</non-terminal>
  <rule>
    <symbol>RelativeLocationPath</symbol>
    <symbol>DOUBLE_SLASH</symbol>
    <symbol>Step</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(abbreviated_relative_location_path, "OO", $1, $3);
    </code>
    <code language="python">
      $$ = abbreviated_relative_location_path($1, $3)
    </code>
  </rule>
</production>

<production name="12">
  <non-terminal>AbbreviatedStep</non-terminal>
  <rule>
    <symbol>'.'</symbol>
  </rule>
  <rule>
    <symbol>DOUBLE_DOT</symbol>
  </rule>
</production>

<production name="13">
  <non-terminal>AbbreviatedAxisSpecifier</non-terminal>
  <rule>
    <symbol>'@'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(axis_specifier, "s", "attribute");
    </code>
    <code language="python">
      $$ = axis_specifier("attribute")
    </code>
  </rule>
  <rule>
    <code language="c">
      $$ = PyObject_CallFunction(axis_specifier, "s", "child");
    </code>
    <code language="python">
      $$ = axis_specifier("child")
    </code>
  </rule>
</production>

<production name="14">
  <non-terminal>Expr</non-terminal>
  <!-- Bypass -->
  <rule>
    <symbol>OrExpr</symbol>
  </rule>
</production>

<production name="15">
  <non-terminal>PrimaryExpr</non-terminal>
  <rule>
    <symbol>VariableReference</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(variable_reference, "O", $1);
    </code>
    <code language="python">
      $$ = variable_reference($1)
    </code>
  </rule>
  <rule>
    <symbol>'('</symbol>
    <symbol>Expr</symbol>
    <symbol>')'</symbol>
    <code language="c">
      $$ = $2;
      Py_INCREF($2);
    </code>
    <code language="python">
      $$ = $2
    </code>
  </rule>
  <rule>
    <symbol>Literal</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(string_literal, "O", $1);
    </code>
    <code language="python">
      $$ = string_literal($1)
    </code>
  </rule>
  <rule>
    <symbol>Number</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(number_literal, "O", $1);
    </code>
    <code language="python">
      $$ = number_literal($1)
    </code>
  </rule>
  <!-- Bypass -->
  <rule>
    <symbol>FunctionCall</symbol>
  </rule>
</production>

<production name="16">
  <non-terminal>FunctionCall</non-terminal>
  <rule>
    <symbol>FunctionName</symbol>
    <symbol>'('</symbol>
    <symbol>')'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(function_call, "O[]", $1);
    </code>
    <code language="python">
      $$ = function_call($1, [])
    </code>
  </rule>
  <rule>
    <symbol>FunctionName</symbol>
    <symbol>'('</symbol>
    <symbol>Argument.list</symbol>
    <symbol>')'</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(function_call, "OO", $1, $3);
    </code>
    <code language="python">
      $$ = function_call($1, $3)
    </code>
  </rule>
</production>

<production name="16a">
  <non-terminal>Argument.list</non-terminal>
  <rule>
    <symbol>Argument</symbol>
    <code language="c">
      $$ = PyList_New(1);
      /* Steals a reference */
      PyList_SET_ITEM($$, 0, $1);
      Py_INCREF($1);
    </code>
    <code language="python">
      $$ = [$1]
    </code>
  </rule>
  <rule>
    <symbol>Argument.list</symbol>
    <symbol>','</symbol>
    <symbol>Argument</symbol>
    <code language="c">
      PyList_Append($1, $3);
      Py_INCREF($1);
      $$ = $1;
    </code>
    <code language="python">
      $1.append($3)
      $$ = $1
    </code>
  </rule>
</production>

<production name="17">
  <non-terminal>Argument</non-terminal>
  <!-- Bypass -->
  <rule>
    <symbol>Expr</symbol>
  </rule>
</production>

<production name="18">
  <non-terminal>UnionExpr</non-terminal>
  <rule>
    <symbol>PathExpr</symbol>
  </rule>
  <rule>
    <symbol>UnionExpr</symbol>
    <symbol>'|'</symbol>
    <symbol>PathExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(union_expr, "OO", $1, $3);
    </code>
    <code language="python">
      $$ = union_expr($1, $3)
    </code>
  </rule>
</production>

<production name="19">
  <non-terminal>PathExpr</non-terminal>
  <rule>
    <symbol>LocationPath</symbol>
  </rule>
  <rule>
    <symbol>FilterExpr</symbol>
  </rule>
  <rule>
    <symbol>FilterExpr</symbol>
    <symbol>'/'</symbol>
    <symbol>RelativeLocationPath</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(path_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = path_expr($1, $2, $3)
    </code>
  </rule>
  <rule>
    <symbol>FilterExpr</symbol>
    <symbol>DOUBLE_SLASH</symbol>
    <symbol>RelativeLocationPath</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(path_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = path_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="20">
  <non-terminal>FilterExpr</non-terminal>
  <!-- Bypass -->
  <rule>
    <symbol>PrimaryExpr</symbol>
  </rule>
  <rule>
    <symbol>PrimaryExpr</symbol>
    <symbol>Predicate.list</symbol>
    <code language="c">
      $2 = PyObject_CallFunction(predicates, "N", $2);
      $$ = PyObject_CallFunction(filter_expr, "OO", $1, $2);
    </code>
    <code language="python">
      $$ = filter_expr($1, $2)
    </code>
  </rule>
</production>

<production name="21">
  <non-terminal>OrExpr</non-terminal>
  <rule>
    <symbol>AndExpr</symbol>
  </rule>
  <rule>
    <symbol>OrExpr</symbol>
    <symbol>OR_OP</symbol>
    <symbol>AndExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(or_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = or_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="22">
  <non-terminal>AndExpr</non-terminal>
  <rule>
    <symbol>EqualityExpr</symbol>
  </rule>
  <rule>
    <symbol>AndExpr</symbol>
    <symbol>AND_OP</symbol>
    <symbol>EqualityExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(and_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = and_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="23">
  <non-terminal>EqualityExpr</non-terminal>
  <rule>
    <symbol>RelationalExpr</symbol>
  </rule>
  <rule>
    <symbol>EqualityExpr</symbol>
    <symbol>EQUALITY_OP</symbol>
    <symbol>RelationalExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(equality_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = equality_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="24">
  <non-terminal>RelationalExpr</non-terminal>
  <rule>
    <symbol>AdditiveExpr</symbol>
  </rule>
  <rule>
    <symbol>RelationalExpr</symbol>
    <symbol>RELATIONAL_OP</symbol>
    <symbol>AdditiveExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(relational_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = relational_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="25">
  <non-terminal>AdditiveExpr</non-terminal>
  <rule>
    <symbol>MultiplicativeExpr</symbol>
  </rule>
  <rule>
    <symbol>AdditiveExpr</symbol>
    <symbol>'+'</symbol>
    <symbol>MultiplicativeExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(additive_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = additive_expr($1, $2, $3)
    </code>
  </rule>
  <rule>
    <symbol>AdditiveExpr</symbol>
    <symbol>'-'</symbol>
    <symbol>MultiplicativeExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(additive_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = additive_expr($2, $1, $3)
    </code>
  </rule>
</production>

<production name="26">
  <non-terminal>MultiplicativeExpr</non-terminal>
  <rule>
    <symbol>UnaryExpr</symbol>
  </rule>
  <rule>
    <symbol>MultiplicativeExpr</symbol>
    <symbol>MULTIPLICATIVE_OP</symbol>
    <symbol>UnaryExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(multiplicative_expr, "OOO", $1, $2, $3);
    </code>
    <code language="python">
      $$ = multiplicative_expr($1, $2, $3)
    </code>
  </rule>
</production>

<production name="27">
  <non-terminal>UnaryExpr</non-terminal>
  <rule>
    <symbol>UnionExpr</symbol>
  </rule>
  <rule>
    <symbol>'-'</symbol>
    <symbol>UnionExpr</symbol>
    <code language="c">
      $$ = PyObject_CallFunction(unary_expr, "O", $2);
    </code>
    <code language="python">
      $$ = unary_expr($2)
    </code>
  </rule>
</production>

</fragment>
