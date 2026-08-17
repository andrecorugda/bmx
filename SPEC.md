# BMX 0.8 — the grammar

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

**Leading spaces are not content and carry no meaning.** They are removed before a line is
classified, so these two documents have the same AST:

```
:card:
# Today
:!card:
```

```
:card:
  # Today
:!card:
```

A block already nests by **containment** — its opening and closing fences say where it ends. Letting
leading space nest things too would give one document two nesting rules that can disagree, which is
the defect markdown's indented-list handling is famous for. So indentation here is what it is in HTML:
a courtesy to the reader, invisible to the parser. Write it or do not; the answer does not change.

Two consequences worth stating, because both are places a reader could reasonably expect otherwise:

- **A list and a quote still may not nest — but indentation is not how you nest them.** 0.6 read *any*
  indented `- ` or `> ` as an attempted nest and refused it, which made the readable form of the most
  motivating example illegal: `:for:` with its list indented one level. The rules that replace it say
  what nesting actually is:
  - **A list nests when a marker is DEEPER than the list already open** — `- one` / `  - two` is
    `BMX-E012`. A marker with no list open starts a list, in whatever column it stands.
  - **A quote nests as `> > `**, and indentation plays no part in it, so an indented `> ` is just an
    indented quote.

  This was found by round-tripping the conformance suite through `tools/fmt.py`: indenting a fixture
  produced *a list may not nest* about a document containing one list. **The tool that consumes a rule
  is what finds the rule too broad**, and no fixture had a list inside an indented block because nobody
  writes a case asserting that something they believe illegal actually works.
- **A code block's content keeps its own shape.** Content lines have the *opening fence's* indentation
  removed and nothing more, so a fence indented inside a block still holds exactly the code you wrote,
  relative indentation included. Content is never reinterpreted (§2.4).

**Tabs are an error** (`BMX-E010`) in a line's leading whitespace. A tab is where every markdown
dialect diverges — four columns, eight columns, or one — and a format that promises one reading cannot
have a byte whose width is a matter of opinion. This holds even though the *spaces* around it are
insignificant: the reason to refuse a tab is that a reader aligning by eye and a parser counting bytes
would disagree about what they are looking at, and that is true whether or not the count means
anything.

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
- A list item's content is inline content. **List nesting is not in 0.8** — a line beginning with
  spaces then `- ` is `BMX-E012`, refused rather than guessed at, and the trigger for adding it
  is a real document that needs it.
- **The sentence above is narrower than it looks, and two releases read it too widely.** What is refused
  is a marker **deeper than the list already open** — `- one` / `  - two`. A marker with no list open
  starts a list, in whatever column it stands, so `:for:` with its items indented one level is ordinary.
  Everywhere else leading space is simply discarded (§1).

  Both misreadings shipped. Every version through 0.5.1 refused *any* indented line at all, and told
  anyone who indented a paragraph that their list may not nest. 0.6 and 0.7 narrowed it to markers but
  still refused them with no list open — which made the readable form of a loop over a list illegal in
  the release whose purpose was allowing it. **A rule stated as a property of a line, when it is really
  a property of a line's relationship to another line, will be implemented too widely every time.**

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
- There is no indented code block. It is the other half of the tab problem — indentation opens
  nothing, so four spaces are four spaces.
- **A fence may itself be indented**, and then its content lines lose that same indentation and keep
  the rest. `value` is what you would have written at column 0.

### 2.5 Block quote

```
> quoted
> still quoted
```

`> ` at the start of a line, after any leading spaces (§1). Consecutive lines form one quote; the
content of each is inline content. **No nested quotes in 0.8** — `> > ` is `BMX-E012`. An indented `> `
is **not** a nest and never was: nesting is spelled with a second `> `, so indentation has no part to
play and an indented quote is just a quote a formatter moved.

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

**There is no slot in a code block.** That is what makes it possible to document BMX in BMX.

For repetition and conditional structure, see §4a: those are **blocks**, not slot syntax. There is
no `{{#if}}` and no `{{#each}}` — a slot is always a value, and anything that opens and closes is a
fence.

## 4a. Blocks

A **block** is the format's one extension point for structure, and it is the same move as a slot:
BMX captures a name and some text, and refuses to interpret the text.

```
:for: line in order.lines
- {{ line.sku }} x {{ to_string(line.qty) }}
:!for:
```

That is a block named `for` with the head `line in order.lines` and a body of ordinary BMX.
**BMX does not know what `for` means.** The host declares it, exactly as the host declares what
`order.lines` means — see [`BOUNDARY.md`](BOUNDARY.md).

This is why the grammar does not grow when a host gains a feature. `for`, `if`, `match` and a
component named `card` are not four constructs; they are one construct used four times.

### 4a.1 Opening and closing

A block **opens** with `:name:` and **closes** with `:!name:`, each on its own line:

```
:card: title="Pricing"
Any **markdown** in here.
:!card:
```

- A name is a letter, then letters, digits, `-` and `_`. A `:something:` whose something is not a
  name is `BMX-E030` — refused rather than left to render as a paragraph starting with a colon.
- The head is the bytes after the closing colon of the marker, with leading and trailing spaces and
  tabs removed. It may be empty.
- **The head is never parsed.** It is captured with its byte offset, like a slot's expression.
- **A closer names its block, and a mismatch is `BMX-E035`.** `:!for:` against an open `button` is
  refused, and the message carries BOTH positions — where the block opened and where the wrong closer
  is. That is the entire reason a named closer is worth its characters over an anonymous one: without
  the check it is a comment, and a comment that can disagree with the structure is worse than nothing.
- An unclosed block at end of document is `BMX-E031`. It is never closed implicitly.
- **A block may open and close on one line**: `:span: class=box :!span:`. The trailing closer is
  recognised only at end of line and only when it names *this* block, so a `:!x:` inside a head is
  untouched. **Its body is empty** — everything between the marker and the closer is head. That is a
  decision, not an omission: a head is opaque to BMX, so in `:span: class=text {{ label }} :!span:`
  the format cannot tell where `class=text` ended and the label began. There is no delimiter and
  inventing one is a rule added, so a block that needs a *body* takes three lines, where the newline
  is the delimiter.

**On `:word:` and emoji shortcodes.** `:tada:` alone on a line is a block named `tada`, and a host that
declares no such block refuses it. That is a real collision with a convention several tools use, and the
ruling is that **the format does not adjust for it** — a shortcode that wants to survive gets wrapped,
`emoji(:tada:)`. Two reasons it is the right way round: a shortcode mid-sentence was never at risk (a
fence is recognised only at the start of a line), and the collision fails *loudly* — an unknown block is
refused, so nobody ships a page with a missing `tada`. A format that gave up its own structural syntax
to avoid a naming clash with an optional convention would be paying its central cost for someone else's
sugar.

**Why `!`.** It is already the negation operator of the host this format was designed for — a reader
who knows `!a` is *not a* reads `:!button:` as *not a button from here on* with nothing to learn. `/`
was proposed, borrowing XML, and rejected: it reads as an escape, and it would have given a character
with no current meaning in the host a second one. Choosing the mark that already means this beats
importing a convention.

### 4a.2 Nesting

**Blocks nest by NAME, and there is nothing to count:**

```
:for: section in page.sections
## {{ section.title }}

:card: title="Detail"
{{ section.body }}
:!card:
:!for:
```

`:!name:` closes the innermost open block, which must be named `name`; anything else is `BMX-E035`.
A closer with **no open block at all** is `BMX-E032`.

**0.6 nested by fence length** — a longer `::::` contained a shorter `:::`, the rule code fences use —
and 0.7 deletes it. Two reasons, and the second is the one that matters:

- **Nothing has to be counted.** A reader of `:!button:` knows what it closes. A reader of `:::` knows
  only that *something* ends, and finds out by counting openers upward.
- **A miscount used to produce a valid document with the wrong shape**, which is the silent-wrong-answer
  class this format exists to remove — sitting in the format's own structure. A named closer cannot be
  silently wrong: it is either right or `BMX-E035`.

*(An earlier draft of the length rule contradicted itself — one sentence said a longer closer was an
error, the next said it closed. Writing the conformance case is what exposed it, and the case is what
made deleting the whole rule safe.)*

### 4a.3 Attributes

A head may carry attributes, and BMX still does not parse them — but it does define **where a
class and an id go**, because those two are the ones every host wants and every dialect spells
differently:

```
:card: title="Pricing" .featured .wide #plans
```

- `.name` is a class, `#name` is an id. Both use the §4a.1 name rule.
- **At most one `#id` per block.** `BMX-E033` for a second.
- Everything else in the head is the host's, including `title="Pricing"` and any
  `on:click=save_order`. BMX captures the text and does not decide what an attribute means.

**A block emits nothing by itself.** A host decides what `card` renders, and whether `on:click`
becomes a wasm binding, a data attribute, or a refusal. That is what keeps a format with no
runtime from acquiring one.

### 4a.4 Inline blocks

The same construct in a sentence:

```
Press ::key[Ctrl+S]:: to save, or ::icon[trash]:: to discard.
```

`::`, a name, `[`, an opaque head, `]`, `::`. The head may not contain an unescaped `]`, and the
whole thing must close on its line — `BMX-E034` otherwise.

**An inline block is not a slot, and the difference is the guarantee.** A slot's value is escaped,
always (see [`ESCAPING.md`](ESCAPING.md)). An inline block is a call to something the host
declared, and the host decides what it produces. They look different because they are different,
and a reader must be able to tell at a glance which one can emit markup.

### 4a.5 What a host must do

Nothing in this section can be checked by BMX, so all of it is required of a host:

- **Refuse an unknown block name.** Never render it, never skip it silently.
- **Refuse an unknown attribute** on a block it declares.
- **Decide what a head means**, including whether it binds names inside the body.
- **Refuse an event attribute it cannot wire.** A host with no runtime must refuse `on:*` rather
  than emit an inline handler — emitting one puts unchecked script on the page, which is the hole
  the escaping rule exists to close.

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
| `paragraph` | `children`, `offset` |
| `list` | `ordered` (bool), `items` — each an `item` node, `offset` |
| `item` | `children`, `offset` |
| `code` | `info` (string, `""` if absent), `value` (string), `offset` |
| `quote` | `children`, `offset` |
| `text` | `value` |
| `emphasis` \| `strong` \| `link` | `children`, `offset`; `link` also `target` |
| `code_span` | `value` |
| `slot` | `expression`, `offset` |
| `block` | `name`, `head`, `one_line` (bool), `offset`, `head_offset`, `children` |
| `inline_block` | `name`, `head`, `offset`, `head_offset` |

**Every node except `text` and `code_span` carries an `offset`, and it is the byte index of the
first byte the author wrote for that construct** — the `#` of a heading, the `-` of a list item, the
first `*` of a strong run, the `[` of a link, the first `:` of a block's fence.

**One field name means one thing, and 0.3 shipped with it meaning two.** In 0.3 a `block`'s and an
`inline_block`'s `offset` was the position of the *head*, while the eight types 0.3 added used the
start of the construct — so the sentence above was false for exactly those two, and it was written in
0.3 by the person who moved them. It cost a consumer a measurement: a refusal about a block reported
a column pointing past the end of what was wrong, and worst on a block with no head at all, where
"the start of the head" is the newline after it.

So a block's `offset` is its fence and its `head_offset` is its head — both, because a host
highlighting or reporting on a head genuinely needs that position and it is not recoverable from the
fence.

**`one_line` distinguishes two documents that would otherwise be the same node**, and it is in 0.7
because a host measured what its absence costs. These two:

```
:span: class=text hello :!span:
```

```
:span: class=text hello
:!span:
```

both carry `head: "class=text hello"` and no children. But they do not mean the same thing to a host:
in the first, `hello` is where a *body* would go and a host may reasonably treat it as content; in the
second the author wrote it as head. Without the flag a host has to guess, and a guess that splits heads
changes the meaning of the two-line form too — star-burxt measured its own head parser turning `hello`
into a boolean attribute and dropping the text, producing `<span class="text" hello></span>` with no
refusal. **BMX cannot fix that, because head meaning is the host's; it can stop withholding the one
fact the host needs to fix it.**

**The host that asked for it then withdrew the request, and the field stays.** star-burxt's answer became
a named `child=` attribute in the head, which is better — the author says which part is the body instead
of a parser inferring it — so it no longer needs the flag. But `one_line` is the only thing in the AST
that records a choice the author made and the tree would otherwise lose, which means it is what a
formatter needs to print a document back the way it was written. **A tree that cannot reproduce its
source is a tree that a formatter has to guess from**, and there is no cheaper time to add a field than a
release that is already editing every block expectation.

A slot keeps the one real exception, and it is stated rather than implied: **a slot's `offset` is the
first byte of the *trimmed expression***, per §4, not of the `{{`. That is deliberate — the host is
handed the expression and must be able to point inside it.

Two nodes have none on purpose. `text` and `code_span` are the leaves a host never reports against:
a diagnostic points at the construct that is wrong, and "your text is wrong" is not a diagnostic.

**0.2 had offsets on three node types only**, which meant a host could say where a slot was and not
where anything containing it was — so a framework refusing *"a heading inside a button"* pointed at
the button. That is a position a reader cannot act on, and **a confidently wrong position is worse
than none**, which is why this is a major rather than something deferred.

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
| `BMX-E010` | tab in leading whitespace |
| `BMX-E011` | malformed heading |
| `BMX-E012` | list or quote nesting, which 0.8 does not have (blocks nest — see §4a.2). A `- ` or `<digits>. ` **deeper than the list already open**, or a `> > `; an indented line is otherwise ordinary (§1) |
| `BMX-E020` | unterminated code span |
| `BMX-E021` | invalid escape |
| `BMX-E022` | empty slot expression |
| `BMX-E030` | a block name that is not a name |
| `BMX-E031` | unterminated block |
| `BMX-E032` | a closer with no open block |
| `BMX-E035` | a closer names a different block than the one open here. The message carries both positions |
| `BMX-E036` | 0.6's `:::` fence, recognised only in order to refuse it by name and say what to run |
| `BMX-E033` | a second `#id` on one block |
| `BMX-E034` | unterminated inline block |

A conforming parser **stops at the first error**. Recovery is a later question and it is a real
one — an editor wants every error at once — but recovery that differs between implementations is
worse than no recovery.

## 7. What 0.8 deliberately does not have

Named with the trigger that would earn each one a version, because a list of omissions with no
reasons is a list somebody will "fix" at random.

| Absent | Trigger to add it |
|---|---|
| Nested lists and quotes | a real document that needs one. **The AST does NOT already nest** — an earlier version of this row said it did, and it was wrong: an `item`'s children are INLINE nodes, so a nested list has nowhere to go. It needs a field, which makes it a major |
| Tables | the same; they are the most-requested markdown extension and the least uniform |
| Images | a decision about whether a target is a URL or a host expression — probably the latter, which makes it a slot question. A host may declare an `image` block today |
| Raw HTML passthrough | it would put an unescaped hole in the format, and [`ESCAPING.md`](ESCAPING.md) says why that is the host's `raw` to grant, not the format's |
| Error recovery | §6 |
| Front matter | it is how a host will declare a view's signature, and it must be designed WITH a host rather than guessed at |

**Loops, conditionals, components and event bindings are NOT on this list any more**, and how they
left it is worth recording. They were refused in 0.1 on the reasoning that *a view is a function
and the host already has control flow* — which is true when the host compiles the view, and false
everywhere else. A receipt with N line items could not be written in BMX at all: the host had to
build the list, so the markup for a line lived in the host's code rather than in the document.
**A markup format that cannot express repetition is not a markup format.**

**A named closer was on this list for about two hours, and taking it off is worth recording.** It was
rejected on the argument that a closer which can be *wrong* is a new way for a document to lie about its
own structure — and that argument is simply answered: refuse the mismatch. `:!for:` against an open
`button` is `BMX-E035`, so it cannot lie, only be caught. The rejection was reasoned from a property the
construct does not have once it is checked, which is a failure mode worth naming: **an objection to an
unchecked version of a thing is not an objection to the thing.** It survived being written into a
normative document by an hour.

They arrived as §4a, and as **one** construct rather than four, so the grammar grew by three rules
instead of a dozen. That was the constraint: [`VERSIONING.md`](VERSIONING.md) says 1.0 needs an
implementation by somebody who did not write this spec, and every rule added is weight against
that bar.
