Grammars are required for Grammatical Evolution (GE) problems to map the integer-valued genomes to executable phenomes. In esec, GE individuals must map to valid Python code, since the Python interpreter is used for execution. The code must define a function `Eval` with a parameter `T` (list) for terminals, but other parameters and return values are specified by the evaluator.

Grammars are specified in a BNF-link notation, but use a Python dictionary and lists rather than a single block of text.

The dictionary contains the set of rules. The key of each element is the unique, case-sensitive name of the rule. The starting rule must be named with an asterisk (`*`). Rule names may not contain spaces or double-quote characters.

The value of each dictionary element is a list of rule productions. Each rule production is a string. The string is a space-delimited sequence of literal elements and references to other rules. Literal elements are enclosed in double-quote characters and, when encountered, are directly inserted into the final code. Rule references are followed to the rule within the same dictionary.

Where multiple productions are available, a gene is read from the genome to select which production to use.

The following rules are always available:

| **Rule Name** | **Productions** |
|:--------------|:----------------|
| `TERMINAL` | One for each of the terminals available |
| `INDENT` | The current indent level in spaces (one space per level) |
| `INC_INDENT` | Increases the indent level by one |
| `DEC_INDENT` | Decreases the indent level by one |
| `NEWLINE` | A newline character |

Evaluators should provide a suitable grammar, which also allows new grammars to be derived easily retaining the same interface.

The following example shows the rules and instantiates a `Grammar` object for a Boolean function.

```
rules = {
    '*': [ '"def Eval(T):" NEWLINE INC_INDENT INDENT V0,V1,V2=0,0,0 NEWLINE Body Return DEC_INDENT' ],
    'Body': [ 'INDENT Line NEWLINE',] + ['INDENT Line NEWLINE Body'],
    'Line': [ 'Variable "=" Expr',
              '"if " Expr ":" NEWLINE INC_INDENT Body DEC_INDENT' ],
    'Return': [ 'INDENT "return " Variable' ],
    'Variable': [ '"V0"', '"V1"', '"V2"' ],
    'Expr': [ 'Source', '"(" Expr BinaryOp Expr ")"', '"(" UnaryOp Expr ")"' ],
    'Source': [ 'TERMINAL', 'Variable' ],
    'UnaryOp': [ '" not "' ],
    'BinaryOp': [ '" and "', '" or "', '" ^ "' ],
}

from esec.species.ge import Grammar
grammar = Grammar(rules)
```