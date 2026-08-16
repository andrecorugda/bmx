# BMX 0.1 — the grammar

**BMX is markdown with one unambiguous reading and a typed hole in it.**

Two properties define it, and everything below serves one of them:

1. **It always fails loudly.** Markdown's defining property is that nothing is ever a syntax
   error — `*bold` with no closing star renders as the characters `*bold`, and three dialects
   disagree about the rest. BMX has no such reading. Input that is not valid BMX is an error
   with a code, never output that looks nearly right.
2. **The expression slot belongs to the host language.** BMX says *where* an expression appears
   and how it is delimited. It says nothing about what an expression is. That is
   [`BOUNDARY.md`](BOUNDARY.md), and it is what lets a language with types and contracts check a
   BMX document that a language without them can still render.

This document is normative. Where it and an implementation disagree, the implementation is
wrong; where it and [`tests/`](tests/) disagree, **the tests win** — they are the specification's
executable half, and a claim not in them is a claim no implementation has to honour.

---

## 1. Input

A BMX document is a sequence of **bytes**, and the parser is byte-oriented. UTF-8 passes
through unexamined — BMX never decodes a codepoint, so it never has an opinion about
normalisation, width or case.

**Line endings.** `\n` ends a line. A `\r` immediately before it is consumed with it. A lone
`\r` is an ordinary byte and does *not* end a line. Rationale: a file written on Windows must
parse identically, and a lone `\r` in the middle of a line is far more likely to be data than
intent.

**Tabs are an error** (`BMX-E010`) anywhere a line's leading whitespace is significant. A tab is
where every markdown dialect diverges — four columns, eight columns, or one — and a format that
promises one reading cannot have a byte whose width is a matter of opinion.

**The final line need not end with `\n`.**

## 2. Blocks

A document is a sequence of blocks. A **blank line** — a line whose bytes are zero or more
spaces — ends the block in progress and is otherwise not content.

### 2.1 Heading

```
# Title
###### Six is the limit
```

One to six `#` at the start of a line, then **exactly one space**, then the heading's inline
content to the end of the line.

- `#Title` (no space) is `BMX-E011`. It is not a paragraph beginning with `#`, because that
  reading is the one that silently turns a typo'd heading into body text.
- Seven or more `#` is `BMX-E011`.
- A heading may not be empty: `# ` alone is `BMX-E011`.
- **There is no setext heading** (`Title` underlined with `===`). Two spellings of one concept
  is the thing this format exists to not have.
- Trailing `#` characters are content, not decoration. `# Title #` has the heading text
  `Title #`.

### 2.2 Paragraph

One or more consecutive non-blank lines that begin no other block. Lines are joined with a
single `\n`; no other whitespace is inserted or removed at the join.

**Trailing spaces on a line are stripped.** There is no two-space line break — an invisible
character that changes the output is unreviewable by construction.

### 2.3 List

```
- one
- two

1. first
2. second
```

A list item begins with `- ` (unordered) or `<digits>. ` (ordered) at the start of a line, with
exactly one space after the marker. Consecutive item lines form one list. A blank line ends it.

- **`-` is the only unordered marker.** Not `*`, not `+`.
- An ordered list's numbers are **content, not instructions**: a renderer emits them as written.
  A list numbered `1. 1. 1.` renders as `1. 1. 1.`, because a format that silently renumbers is
  a format whose output does not match its source.
- A list item's content is inline content. **Nesting is not in 0.1** — a line beginning with
  spaces then `- ` is `BMX-E012`, refused rather than guessed at, and the trigger for adding it
  is a real document that needs it.

### 2.4 Code block

````
```burxt
let x: Int = 1;
```
````

Exactly three backticks at the start of a line, an optional **info string** to end of line, then
lines of content, then exactly three backticks at the start of a line.

- The info string is passed through verbatim and BMX assigns it no meaning.
- Content is **never** parsed for inline content, slots included. A `{{` inside a code block is
  the characters `{{`.
- An unterminated fence at end of document is `BMX-E003`. Markdown closes it for you at EOF,
  which is the single most common way a document renders as one giant code block and nobody is
  told why.
- There is no indented code block. It is the other half of the tab problem.

### 2.5 Block quote

```
> quoted
> still quoted
```

`> ` at the start of a line. Consecutive lines form one quote; the content of each is inline
content. **No nesting in 0.1** — `> > ` is `BMX-E012`.

## 3. Inline content

Parsed left to right. Four constructs, and each **must** be closed on the same line.

| Written | Node |
|---|---|
| `` `code` `` | `code` |
| `**strong**` | `strong` |
| `*emphasis*` | `emphasis` |
| `[text](target)` | `link` |
| `{{ expression }}` | `slot` — see §4 |

- **One spelling each.** No `_emphasis_`, no `__strong__`.
- An unclosed marker is an error, never literal text: `BMX-E002` for `*` and `**`, `BMX-E020`
  for `` ` ``, `BMX-E004` for a link, `BMX-E001` for a slot. **This is the rule that separates
  BMX from markdown**, and it is why an agent that produces a truncated document gets told
  rather than getting a page with a stray asterisk in it.
- Emphasis and strong may contain other inline content. A code span may not — its bytes are
  literal to the closing backtick.
- A link's target is bytes to the closing `)`. It may not contain `)`. Escaping rules for
  targets are deferred to 0.2 rather than guessed at now.

**The escape.** `\` makes the next byte literal, and is the only way to write a `` ` ``, `*`,
`[`, `{` or `\` that is not markup. `\` before any other byte is `BMX-E021` — a backslash that
sometimes escapes and sometimes is a backslash is how every markdown dialect ends up with a
different answer.

## 4. The expression slot

```
Hello {{ user.name }}, your total is {{ order.total }}.
```

`{{`, then bytes, then `}}`. The bytes between are the **expression text**, and BMX:

- **trims leading and trailing spaces and tabs** from it, so `{{ x }}` and `{{x}}` carry the
  same expression;
- requires it to be non-empty after trimming (`BMX-E022`);
- requires `}}` on the same line (`BMX-E001`);
- otherwise **does not look at it at all.**

A slot node carries the expression text and its byte offset in the source. What that text means,
whether it type-checks, and what it is allowed to touch are the host's questions —
[`BOUNDARY.md`](BOUNDARY.md).

**`offset` is the byte index of the first byte of the trimmed expression** — not of the `{{`.
For `Hello {{ user.name }}.` it is 9, the `u`. A host reporting a bad expression underlines the
expression, which is the only reason the field exists.

*(This sentence used to read "its byte offset in the source", and three of the conformance cases
had been written to three different readings of it. The suite caught it on its first run against
a real parser. A format whose whole claim is one unambiguous reading cannot afford a field
described that loosely, and the fix is recorded here rather than quietly applied.)*

`{{{` is not a special form. It is `{` followed by a slot, per the escape rule.

**There is no slot in a code block, and no block-level slot in 0.1** — no `{{#if}}`, no loops.
Control flow inside a template is the thing that turns a view into a program that no type system
is watching; the host has `if` and `while` already, and a view is a function. The trigger for
reconsidering is a document that cannot be expressed as host code calling BMX fragments.

## 5. The AST

One canonical shape, because two implementations agreeing on rendering while disagreeing on
structure is the drift this format exists to prevent. JSON here is the interchange form; an
implementation may build whatever it likes in memory.

```json
{"type": "document", "children": [ … ]}
```

| Node | Fields |
|---|---|
| `document` | `children` |
| `heading` | `level` (1–6), `children` |
| `paragraph` | `children` |
| `list` | `ordered` (bool), `items` — each an array of inline nodes |
| `code` | `info` (string, `""` if absent), `value` (string) |
| `quote` | `children` |
| `text` | `value` |
| `emphasis` \| `strong` \| `link` | `children`; `link` also `target` |
| `code_span` | `value` |
| `slot` | `expression`, `offset` |

Adjacent `text` nodes are **always merged**. A parser that emits `text("a")`,`text("b")` where
another emits `text("ab")` fails the conformance suite, and rightly: they are the same document.

## 6. Errors

Every error carries a code, a byte offset, and a message. The **code** is the conformance
surface — a message is an implementation's own words and may be better in some languages than
others.

| Code | Meaning |
|---|---|
| `BMX-E001` | unterminated slot |
| `BMX-E002` | unterminated emphasis or strong |
| `BMX-E003` | unterminated code fence |
| `BMX-E004` | unterminated link |
| `BMX-E010` | tab in significant whitespace |
| `BMX-E011` | malformed heading |
| `BMX-E012` | nesting, which 0.1 does not have |
| `BMX-E020` | unterminated code span |
| `BMX-E021` | invalid escape |
| `BMX-E022` | empty slot expression |

A conforming parser **stops at the first error**. Recovery is a 0.2 question and it is a real
one — an editor wants every error at once — but recovery that differs between implementations is
worse than no recovery.

## 7. What 0.1 deliberately does not have

Named with the trigger that would earn each one a version, because a list of omissions with no
reasons is a list somebody will "fix" at random.

| Absent | Trigger to add it |
|---|---|
| Nested lists and quotes | a real document that needs one; the AST already nests, only the parser refuses |
| Tables | the same; they are the most-requested markdown extension and the least uniform |
| Images | a decision about whether a target is a URL or a host expression — probably the latter, which makes it a slot question |
| Raw HTML passthrough | it would put an unescaped hole in the format, and [`ESCAPING.md`](ESCAPING.md) says why that is the host's `raw` to grant, not the format's |
| Block-level slots, loops, conditionals | §4. A view is a function; the host already has control flow |
| Error recovery | §6 |
| Front matter | it is how a host will declare a view's signature, and it must be designed WITH a host rather than guessed at — the first real question for 0.2 |
