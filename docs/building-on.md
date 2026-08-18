---
layout: default
title: Building on BMX
---

{% raw %}
# Building on BMX

For anyone — person or agent — writing a **layer above** BMX: a component system, a framework, a
static site generator, an editor integration. **star-burxt is the first of these**, and this page
is the contract it codes against.

Read this before extending anything. Most of what a framework wants to add to BMX belongs in the
host language instead, and the difference is not a matter of taste — it is what keeps the format
implementable by somebody who is not you.

## The one rule

> **BMX describes structure. Everything that happens at runtime belongs to the host.**

That is [`BOUNDARY.md`](https://github.com/andrecorugda/bmx/blob/main/BOUNDARY.md) in a sentence.
Applied concretely:

| You want | Where it goes |
|---|---|
| Conditionals, loops | the **host**. A view is a function; it already has `if` and `while` |
| Reactivity, state, stores | the **host**. BMX has no runtime and will not grow one |
| Components, composition | the **host**. Two views compose by one calling the other |
| Event handlers | the **host**. A document has no way to name a function, deliberately |
| A new block or inline type | **the format**, via a spec change and conformance cases — and only if a real document needed it |
| A new expression syntax | **nowhere.** The slot's contents are the host's language, entire |

**If your feature needs the format to change, you are almost certainly holding it wrong.** The
test: *could a language with no type system still implement this?* If not, it is not the format's.

## What you can rely on

These are guaranteed, verified by the conformance suite, and will not change inside 0.x without a
major version:

**Every slot value is escaped, always.** There is no raw syntax and there will not be one. A layer
above BMX cannot accidentally emit an unescaped value through a document, because the document has
no way to express one.

**A malformed document is an error, never partial output.** Parsing answers a result or a code —
it never answers a half-built tree. So a generated document that got truncated fails loudly rather
than rendering nearly right.

**Slot offsets point into the author's source.** `offset` is the byte index of the first byte of
the trimmed expression. This is what lets you report an error at a position in the `.bmx` file the
author opened rather than in whatever you generated. It is mandatory, and it is tested.

**Adjacent text nodes are merged.** `a` `b` is one text node, always. Two implementations that
disagree about that disagree about the document.

**A code block's content is never parsed.** No slots, no blocks, no inline markup. That is what makes it
possible to document BMX in BMX — and what lets you put a framework's own syntax in a fenced block
without the format touching it.

## What you must implement yourself

The format requires these of a host and does not provide them:

**Refuse dangerous link schemes.** `[click](javascript:steal())` is a working attack that no
character escaping addresses, because the danger is the scheme. The allowed set is yours; emitting
an arbitrary scheme unexamined is not conforming. Burxt's answer is `bmx_target_allowed`, which
permits `http`, `https`, `mailto` and relative targets.

**Decide what an expression means.** BMX hands you text and an offset. Whether `order.total`
resolves, type-checks, or is allowed to touch the filesystem is entirely yours.

**Decide what a missing value does.** BMX has no opinion. Burxt's answer is to refuse — a slot
with no binding is an error, never an empty string, because the empty string is how a page ships
with a missing total nobody sees. **A framework that renders blank here has chosen to, and should
say so.**

## Naming a body in the head, and the trap in it

A head is opaque bytes, so the format cannot tell you where attributes stop and content begins. That
means a host with attribute syntax has a hazard the format cannot close for it:

```bmx
:span: class=text hello
:!span:
```

If your head parser reads a bare word as a boolean attribute — the HTML convention, and a reasonable
choice — then `hello` becomes an attribute and **the text silently disappears**. star-burxt measured
exactly that, `<span class="text" hello></span>`, with no refusal: it had been happening since its
attributes landed.

**The fix is a named attribute for the body**, so the author says which part is content rather than a
parser inferring it:

```bmx
:span: class=text child=hello :!span:
:button: class=primary child={{ task.label }} on:click=Msg.Save
:!button:
```

Every token stays `name=value`, the head stays opaque to BMX, and there is nothing to guess. It also
composes with a one-line block, which is why the format did not need a delimiter for that case.

**Do not call it `value=`.** That is a real HTML attribute and hosts already emit it — `:input:
value={{ model.draft }}` is how a field is driven — so making `value=` mean *body* would change the
meaning of every form in your documentation, silently. `child=` is free. star-burxt nearly took the
name from a suggestion and caught it by checking what it already emitted.

Two more host-side rules worth copying, both measured rather than reasoned:

- **Refuse a named body AND a block body together** rather than merging them. Two sources for one
  thing means a reader cannot tell which won.
- **A handler expression runs to the end of the head**, because an expression has no end marker — so
  `:button: on:click=n + 1 class=danger` folds `class=danger` into the expression and the class
  vanishes. Say *attributes first* in an error rather than letting it compile into something strange.

## The Burxt surface

If you are building on Burxt specifically, this is what exists today. Signatures are exact;
`burxt/bmx.bx` here, and Burxt's `lib/html.bx`, are ordinary Burxt you can read.

### Parsing

```burxt
public function bmx_parse(source: String) -> Result<[Block], String>
public function bmx_json(blocks: [Block]) -> Json
```

`Block` is `Heading` · `Paragraph` · `Quote` · `List` · `Code`; inline `Bmx` is `Text` ·
`Emphasis` · `Strong` · `CodeSpan` · `Link` · `Slot`. Walk them with `match`.

### Rendering — level 1

```burxt
public pure function bmx_bind(name: String, value: String) -> Binding
public function bmx_html(blocks: [Block], bindings: [Binding]) -> Result<Html, String>
public function bmx_to_html(source: String, bindings: [Binding]) -> Result<String, String>
```

### Diagnostics

```burxt
public function bmx_check(source: String) -> Option<BmxDiagnostic>
public pure function bmx_where(source: String, offset: Int) -> BmxWhere
```

`bmx_check` answers the first problem in a document, or `None`. `bmx_where` turns a byte offset into a
`BmxWhere { line, column }` — **column counts characters, not bytes**, so a line containing `å` reports 17
rather than 18. Every refusal carries an offset; this is how a host turns one into a position an editor can
put a squiggle on.

### Generating — level 2

```burxt
public function bmx_emit_burxt(blocks: [Block], source_name: String, name: String,
                               parameters: String, clauses: [String]) -> Result<String, String>
```

Turns a document into a `pure function … -> Html` whose slots are ordinary expressions. **The
signature comes from the caller, not from the document** — BMX has no front matter, and a
generator inventing one would be adding to the format from the host side.

**And the pieces it is built from, for a host that wants a different envelope:**

```burxt
public function bmx_emit_stmts(blocks: [Block], target: String, tag: String,
                               indent: String) -> Result<String, String>
public function bmx_emit_one(block: Block) -> Result<String, String>
public function bmx_emit_inline(nodes: [Bmx]) -> Result<String, String>
public pure function bmx_strip_end(text: String) -> String
```

`bmx_emit_burxt` writes a whole function; these write the statements, one block, and one run of inline
content. A framework that generates its own component shape — a class, a lifecycle, a different return
type — wants `bmx_emit_stmts` and its own wrapper rather than the whole-function form.

**These six were reachable and depended on before they were written down**, which is the more dangerous
half of an undocumented surface. star-burxt calls all six; nothing in this repository does outside
`burxt/bmx.bx` itself. So the compatibility promise in [`VERSIONING.md`](VERSIONING.md) covered half of
the surface a consumer was actually using, and any of them could have changed in a patch. Documented is
what makes a name promised: `tests/surface.py` now fails if a `public` name is not on this page, and if a
name on this page is not reachable from another package.

### The output tree

```burxt
pure function html_text(value: String) -> Html        // escaped on render
pure function html_raw(trusted: String) -> Html       // the waiver, spelled out
pure function html_element(tag: String, attrs: [Attr], children: [Html]) -> Html
pure function html_attr(name: String, value: String) -> Attr
pure function html_render(node: Html) -> String
```

**This is where a framework attaches.** `bmx_html` gives you an `Html` tree, not a string — so you
can wrap it, walk it, or splice your own elements around it before rendering. Building the tree in
Burxt and rendering once is how you add anything BMX does not have.

Two things the tree refuses, both by contract on the constructor: a tag or attribute **name** that
is not a name, and a **void element carrying children**. Both are holes escaping does not cover.

**Everything above is `pure`.** That is load-bearing rather than decoration: a view built from
these can be `pure`, which is what makes `burxt effects --allow ""` a confirmation by construction
rather than a hope — and it is what lets a view compile to a WebAssembly island that provably
touches nothing.

## What does not exist yet

Stated plainly because a document that lets you infer capabilities you do not have is worse than
one that says nothing.

**What DOES exist**, as of 0.12, and did not when this page was first written: components with
declared props, repetition, conditionals, nesting, classes and ids on a block, event bindings captured as
head text, and inline blocks — all through **one construct**, see
[Writing a document](syntax.html#blocks) — plus, since this list was last honest at 0.2:

- **a byte `offset` on every node**, so a host can report a position in the document the author opened
- **named closers**, `:!name:`, checked against the opener (`BMX-E035`)
- **insignificant indentation**, so nesting can be seen without meaning anything
- **a delimited head**, `:name: -> [ … ] body`, which lets a block carry a body on one line — and that
  body is *inline content*, parsed and escaped by BMX, not a string a host has to interpret
- **`one_line` on a block node**, so a host can tell those two forms apart

**This list was nine releases stale, and that is the failure this page warns about in its own first
sentence.** A capability list frozen in the past does not merely age: it turns a reader away from a
feature that exists, and nobody re-tests what they have been told is absent.

What does not:

**No reactivity, no DOM updates, no lifecycle, no watchers, in the format.** Those are a host's,
and BMX will not grow them — a format with a runtime cannot be implemented by a language that has
none.

**No `match`.** It reduces to `if` for presence, and branching on data shape is host logic.

**No nested lists or quotes.** Blocks nest; those do not.

**No cross-file component resolution in the format.** A block names a component; how a host finds
it is the host's module system, not BMX's.

## Give your library its own version number

Not BMX's. They measure different promises, and 0.2 is the worked example of why.

0.2 added two node kinds — `Fenced` and `InlineBlock`. Against the conformance suite that is a
**minor**: cases were added, none edited, every 0.1 document still parses to what it did before.

0.3 is the other side of it. Adding an `offset` to eight node types edited thirty-one expectations,
so it is a **major** — even though every 0.2 document still means exactly what it did.

If your library **exports its AST**, the same change is a **major** for you. Anyone matching on a
node kind now has a case they do not handle — and in a language with exhaustive matching that is a
compile error in code nobody touched.

> Adding a node kind is a minor for the format and a major for any library that exposes the tree.

Neither number is wrong. One number cannot carry both, so pin them separately: your own version,
plus a statement of which BMX version you target. A library at 3.0 targeting BMX 0.2 is normal and
says something true.

**The design consequence is worth thinking about before your first release: exporting a tree is a
bigger promise than exporting a function.** If you return rendered output, or a documented subset
of node kinds, this never reaches your consumers. Export the tree when you want hosts to build on
it — that is what level 2 needs — but as a decision rather than a side effect of making your own
tests compile.

Full rules in
[`VERSIONING.md`](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md).

## If you extend the format anyway

Sometimes the answer really is a format change. Then:

1. **A case in [`tests/`](https://github.com/andrecorugda/bmx/tree/main/tests) is the proposal.**
   Where the spec and the tests disagree, the tests win, so the case *is* the specification of
   your feature.
2. **Adding a case is a minor; editing one is a major.** The suite is the semver —
   `git diff --diff-filter=M tests/` decides it mechanically rather than by judgement.
3. **Error codes are permanent.** Once assigned, a code means that thing forever; retire it rather
   than reuse it, because a host may be keyed on it.
4. **Both implementations must agree.** `python3 tests/agree.py 'node reference/bmx.js' '<yours>'`
   asks the question the suite cannot: *do two implementations reach the same answer where nothing
   was written down?* That is where a spec's ambiguities live.
{% endraw %}
