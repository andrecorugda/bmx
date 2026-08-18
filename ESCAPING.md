# Escaping — normative

**This is the one place BMX is opinionated about output, and it is deliberate.** Every other
question about rendering belongs to the host. This one does not, because if each implementation
decides for itself where escaping happens, some of them ship cross-site scripting, and a format
whose implementations differ on *that* has done net harm.

## The rule

> **A slot's value is escaped for the output format, at render time, always. There is no
> configuration that turns it off, and no per-slot syntax that opts out.**

Three parts, each load-bearing:

**"For the output format."** Escaping is not one function. HTML escapes `& < > " '`; an XML
attribute differs; a terminal escapes nothing and must instead refuse control bytes. BMX
mandates *that* the host escapes and *when*; the host supplies the function, per
[`BOUNDARY.md`](BOUNDARY.md).

**"At render time."** Not when the value is bound, and not when the AST is built. A value
escaped early is a value that has to be tracked as already-escaped, and nothing in a string's
type says that it is. Escaping where the value leaves means there is exactly one place to be
right. (This is the same argument `lib/html.bx` makes in Burxt, and it was arrived at
independently, which is mild evidence it is correct.)

**"No syntax that opts out."** BMX has no `{{{ raw }}}`. This is the deliberate difference from
Handlebars and Mustache, and the reason is that a triple brace is *three characters* between a
correct page and a compromised one, in a document an agent may have written and a human is
scanning. If a host wants to allow trusted markup, it does so **in the host language**, where
the waiver is a named function call on a line a reviewer can grep — Burxt spells it `html_raw`.
The format does not hand out that power, because the format cannot see who is asking.

## What is escaped

Only **slot values**. Everything else in a BMX document is structure the author wrote, and a
renderer emits it as the structure it is:

| | escaped? |
|---|---|
| A slot's value | **always** |
| Text the author typed | no — it is text, and the renderer emits text |
| A code block's content | as text, in whatever the output format's code element is |
| A link's target | **yes, and per-context** — see below |
| An info string | it is metadata; a host that puts it in output escapes it there |

## Link targets are their own hazard

A target is not text. `[click](javascript:steal())` is a working attack in HTML that no amount of
character escaping addresses, because the danger is the *scheme*, not the bytes.

**A host MUST refuse a target whose scheme it does not allow**, and
[`tests/output.py`](tests/output.py) tests it — sixteen targets, per renderer, each asserted to render
or to refuse.

**A scheme comparison MUST fold case.** RFC 3986 §3.1 says scheme names are case-insensitive, so
refusing `HTTPS://example.com` refuses a correct URL. Folding cannot weaken the check, because the
allowed set is an **allow**-list: it admits only case-variants of the schemes already named, and
`JAVASCRIPT:` folds to `javascript`, which is still absent. The allowed set is the host's — an HTML renderer will want `http`, `https`, `mailto` and
relative targets; a terminal renderer may want none. What is not permitted is emitting an
arbitrary scheme unexamined.

This is stated here rather than in the host's own documentation because a level-1 implementation
written in an afternoon will not think of it, and that is exactly the implementation most likely
to be pointed at user input.

## What the conformance suite proves

Structural cases live in [`tests/cases`](tests/cases) and error cases in
[`tests/errors`](tests/errors). Escaping is **not** testable there — those tests assert an AST,
and escaping happens after it.

So an implementation claiming conformance must additionally show:

1. a rendered output where a slot value containing `<script>` appears as characters;
2. a rendered output where a slot value containing the output format's quote character cannot
   leave an attribute;
3. a refusal of a link target with a scheme outside the allowed set.

Three tests. They are the ones that matter, and an implementation that passes the AST suite and
skips these has proved the easy half.

Here they are [`tests/output.py`](tests/output.py) for the second and third — it also pins the one place
a DOCUMENT's own bytes reach an attribute, a code fence's info string — and
[`burxt/test.py`](burxt/test.py) for the first. **Both of those sentences were wrong until 0.11**, and the way they were wrong is
worth keeping:

- *"the conformance suite tests this"* was an assertion. `tests/renders.py` was the nearest thing, and it
  compares the two renderers and treats **both refusing as agreement** — so if both had stopped refusing
  `javascript:`, it would still have passed. Agreement is a check on drift, never on correctness, and
  this is the one place where being wrong is an attack rather than a typo.
- the pointer was to `tests/pass/bmx_library.bx` **in the Burxt repository**, a path that went away with
  the `lib/` migration. A normative document naming a file that does not exist is worse than naming
  none: a reader who goes looking concludes they have the wrong checkout.
