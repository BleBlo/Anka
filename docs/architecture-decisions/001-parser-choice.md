# ADR 001: Parser Choice

## Status

Accepted

## Context

We need a parser generator for Anka that:
- Works with Python (our implementation language)
- Supports EBNF-style grammar definition
- Produces useful parse trees or ASTs
- Has good documentation and community support
- Is actively maintained

Options considered:
1. **Lark** — Python parser with EBNF grammar, automatic tree building
2. **PLY** — Python lex/yacc, older but battle-tested
3. **ANTLR** — Powerful but requires Java toolchain
4. **pyparsing** — Pure Python, combinator-style
5. **Hand-written recursive descent** — Maximum control, more work

## Decision

Use **Lark** as our parser generator.

## Consequences

### Positive

- **EBNF grammar syntax** — Clean, readable grammar files that serve as documentation
- **Automatic parse tree** — Lark builds trees automatically from grammar
- **Transformer pattern** — Built-in support for converting parse trees to ASTs
- **Good error messages** — Reasonable parse error reporting out of the box
- **Pure Python** — No external tools or Java dependency
- **Active maintenance** — Regular updates, responsive maintainers
- **Earley parser option** — Can handle ambiguous grammars if needed (we use LALR)

### Negative

- **Python-only** — If we ever want to port Anka to another language, grammar won't transfer
- **Runtime dependency** — Lark must be installed to run Anka
- **Learning curve** — Team needs to learn Lark-specific patterns
- **Parse tree overhead** — Extra transformation step from parse tree to AST

### Neutral

- Grammar file (`.lark`) becomes the single source of truth for syntax
- We commit to the Transformer pattern for AST construction

## References

- [Lark Documentation](https://lark-parser.readthedocs.io/)
- [Lark GitHub](https://github.com/lark-parser/lark)
- [Comparison of Python parsers](https://tomassetti.me/parsing-in-python/)
