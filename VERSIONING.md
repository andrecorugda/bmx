# Versioning — the conformance suite is the semver

BMX carries its own version, independent of any host's. A host may be at 3.0 and target BMX 0.1;
a host may support two BMX versions at once. Nothing about BMX's number implies anything about
a host's.

## What each part means

**Patch** — the suite is unchanged, or gains a case that every conforming implementation already
passes. Wording, examples, a clarified sentence.

**Minor** — the suite gains cases that an older implementation would fail, and **every existing
case still passes unchanged**. New syntax that was previously an error is a minor: a document
valid under 0.1 is valid under 0.2 and means the same thing.

**Major** — an existing case changes its expected output, or a document that was valid becomes
an error. This is the only kind of change that can break a document that already exists, and it
is the one that costs everybody.

## The rule that makes this checkable

> **A change is a major if and only if a case in [`tests/`](tests/) had to be edited rather than
> added.**

Not "if it feels breaking". The suite is the artifact, so the diff of the suite is the version
decision, and it is mechanical: `git diff --stat tests/` with modified files is a major, with
only added files is a minor.

This is deliberately the same idea as `burxt review` — a promise diffed rather than asserted —
applied to a format instead of a signature. A format whose compatibility claim is a human's
judgement is a format that will break someone quietly.

### Where that rule has a hole, found 2026-08-17

**The suite is the semver only as far as the suite covers the language.** A change that breaks a
document no fixture contains passes the mechanical test and is still a major.

The case that found it: a one-line block, `::: name head :::`. No fixture has a head ending in
` :::`, so `git diff --stat tests/` would have shown added files only — a minor. But this document is
valid today:

    ::: p some :::
    hello
    :::

head `some :::`, body `hello`. Under a trailing-fence rule it becomes a one-liner, `hello` becomes a
paragraph, and the `:::` becomes `BMX-E032`. **A valid document becomes an error, which is the
definition of a major**, and the rule above would have said otherwise.

### And the other direction, found the same week

**A deleted case in `tests/errors/` is not a major either**, and the letter of the rule said it was.

0.8 narrowed `BMX-E012`, so two refusals became acceptances and their fixtures had to go — mechanically
an edit, and by the sentence above a major. But an `errors/` case asserts what is *refused*, and
un-refusing something cannot break a document that exists: nothing valid changes meaning, only invalid
things become valid. That is the definition of a **minor**.

So the rule splits by directory, which is still mechanical:

> **`tests/cases/` edited → major.** Those are valid documents with expected output; changing one means a
> document's meaning moved.
>
> **`tests/errors/` deleted → minor.** A refusal withdrawn is a widening. (An errors case *added* is a
> major, though: something that parsed now does not.)

Both fixtures were repurposed rather than dropped — `> one` / `  > two` became a passing case asserting
it is one quote — which is better than deleting, because the behaviour that changed is now pinned in the
direction it changed to.

So the rule stands as a *floor*, not a proof: **an edited `cases/` entry proves a major; added entries
only fail to prove one.** Before calling a change minor, the question that has to be asked by hand is *what
document is valid today whose meaning this changes* — and if the answer is not "none", the fixture
for it is missing and belongs in the same commit. The proof obligation was pointing the wrong way:
the suite can convict, it cannot acquit.

## 0.3 is the worked example of a major

0.2 added node kinds and edited no case: a minor. **0.3 added an `offset` field to eight node types
and turned a list item from a bare array into a node** — thirty-one of fifty-six expectations had to
be edited, so the rule above makes it a major mechanically, with no judgement involved.

Worth saying plainly, because "it only adds a field" is how a major gets called a minor: **a
document valid under 0.2 is still valid under 0.3 and still means the same thing.** What broke is
every implementation and every consumer reading the tree. The rule versions the *suite*, not the
prose, and the suite is what an implementation is judged against.

**How it was checked, because regenerating expectations is how a real change hides inside a
mechanical one.** Every new expectation was compared against its old one with the added fields
stripped back out — `offset` on the eight new types, and the `item` wrapper unwrapped — and all
fifty-six matched. So thirty-one files changed and **zero documents changed meaning**, which is a
fact rather than an intention. The first version of that check stripped `offset` unconditionally and
reported fourteen false alarms on the slot and block cases, which already had one.

## 0.4 is the worked example of a major that FIXES a major

0.3 gave eight node types an `offset` and described it as *"the first byte the author wrote for that
construct"*. That sentence was false for `block` and `inline_block`, whose `offset` was their head's
— so one field name meant two things, in the release that introduced the description.

0.4 makes it true: a block's `offset` is its fence, and its head keeps a position under
`head_offset`. Ten expectations edited, so a major by the rule, and **it is a major to undo a
mistake in the previous major** — which is the honest version rather than documenting the
inconsistency as a quirk and leaving the next consumer to find it.

**How it was checked**, since the previous release's lesson was that regenerating hides things: every
expectation was compared field by field against 0.3's, requiring `head_offset` to equal the old
`offset` on exactly those two types and *nothing else to differ*. Ten files changed and nothing moved
that was not meant to.

Worth naming because it is the general shape: **a field that means one thing on most nodes and
another on two is worse than a field that is absent**, because the consumer who reads the description
is the one who gets it wrong.

## An implementation's version is not this version

The rule above versions **the format**. A library that parses BMX has a second surface the format
knows nothing about — its AST — and the two move at different speeds in a way that will bite
anyone who assumes one number covers both.

0.2 is the worked example. It added `Fenced` to the block type and `InlineBlock` to the inline
type. Against the suite that is unambiguously a **minor**: cases were added, none edited, and every
0.1 document still parses to what it did before.

For a library that *exports* those types it is a **major**, because a consumer matching on the
block type now has an unhandled variant. In a language whose `match` must be exhaustive, that is a
compile error in code nobody touched.

> **Adding an AST variant is a minor for the format and a major for any package that exposes the
> AST.** Neither number is wrong; they are measuring different promises.

So an implementation carries its own version rather than mirroring this one, and says which BMX
version it targets. The alternative — one number for both — forces a choice between calling a
purely additive format change breaking, or shipping a silent break to every consumer. Both are
worse than two numbers.

The narrower lesson, for anyone building on this: **exporting an AST is a bigger promise than
exporting a parse function.** A parser that returns only rendered output, or only a documented
subset of node kinds, keeps this problem away from its consumers entirely. Exporting the tree is
worth doing — it is what makes a host able to reach level 2 — but it should be a decision, not a
side effect of making the tests compile.

## What a git tag in this repository means

The rule above says the package's number is not the format's. That leaves a practical question the
first consumer asks: **what do I pin?**

Tags here name **an implementation release**, not a format version, and they say which
implementation:

    burxt-0.1.0        the Burxt implementation, `burxt/bmx.bx`, first release

So a Burxt consumer writes:

    dependency  bmx  https://github.com/andrecorugda/bmx  burxt-0.1.0

**A bare `v0.2.0` would have been the obvious name and it is the wrong one.** This repository holds a
format at 0.2 and an implementation of it, and a tag reading `v0.2.0` invites both to be read off
one number — which is the exact conflation the section above exists to prevent. A reader browsing
tags should not have to know which of the two they are looking at.

It also leaves room without renaming anything: if `reference/bmx.js` is ever published as a package,
it takes `js-…` and nothing has to move.

**What the implementation's own number tracks** is its API: the functions and types it exports, and
the AST a consumer can `match` on. It moves when that surface moves, which — per the section above —
can happen on a format change that was only a minor, and can fail to happen across a format change
that touched nothing it exports.

## Error codes

A code, once assigned, means that thing forever. Codes are never reused and never renumbered.
Removing a rule retires its code rather than freeing it, because a host may have been keyed on
it, and a code that changes meaning between versions is worse than a gap in the numbering.

Adding a code is a **minor** when it applies to input that was already an error under a broader
code, and a **major** when it makes previously valid input an error.

## Pre-1.0

**0.x is not stable, and this file does not pretend otherwise.** Until 1.0 a minor version may
carry breaking changes, and each one will say so in the changelog with the case it edited.

1.0 is earned when two things are true, not when the feature list looks complete:

1. **A second implementation exists**, written by someone who did not write this spec, and it
   passes the suite. A format with one implementation is a syntax, and this spec has one.
2. **A real document set has been through it** — enough pages that the absences in `SPEC.md` §7
   have been tested against something other than imagination.

Until then, the number stays below one, however finished it looks.

## 0.6 is the worked example of a minor that WIDENS

0.6 made leading spaces insignificant (§1). Nothing about it needed judgement:

    git diff --stat tests/     # six files ADDED, none modified  ->  minor

Three cases added that 0.5.1 fails (an indented block, an indented content line, an indented code
fence keeping its shape) and three refusals added that it already passes for the wrong reason. **The
two existing `BMX-E012` cases — a nested list and a nested quote — still pass unchanged**, because the
rule narrowed to exactly what §2.3 and §2.5 always said and no further.

Worth stating because it is the direction people fear: **a document valid under 0.5.1 is valid under
0.6 and means the same thing.** Everything 0.6 adds was previously an *error*, so nothing that existed
can break. The only implementations affected are ones that must now accept what they used to refuse,
which is what a minor is for.

And the thing that made it findable: the format's tooling had already assumed indentation was legal.
`bmx.tmLanguage.json` and `docs/assets/code.js` both match `^\s*` and always did — so the editor
coloured a document the parser would refuse, and nothing compared the two. **A highlighter is a second
opinion about the grammar, and it disagreed with the parser for two releases in silence.**

## 0.7 is the worked example of a major done deliberately

0.7 respelled the fence: `::: name head` / `:::` became `:name: head` / `:!name:`, Andre's spelling.
`git diff --stat tests/` shows **13 expectations edited**, one case deleted and four added, so the rule
convicts it as a major without anyone having to judge — and this time the mechanical answer and the real
answer agree, because a 0.6 document genuinely is refused by 0.7.

**Refused rather than misread, and that distinction is the release.** `BMX-E036` recognises the old
fence for the sole purpose of saying so and naming the migration tool. A respelling that let old
documents render their fences as paragraph text would have broken the format's one promise while
technically changing nothing.

Three things rode along, and each was only cheap *because* a major was already happening:

- **`one_line` on a block node.** A new AST field edits every block expectation, which is a major on its
  own; adding it in 0.6 would have cost a second one. star-burxt asked for it during this release, having
  measured that without it a host cannot tell `:span: x hello :!span:` from its two-line form and
  silently drops the text.
- **The fence-length rule deleted**, with `BMX-W004` and `034-longer-fence-closes-shorter` — a lint and a
  case for a rule the grammar no longer has cannot fire, and documenting a warning nobody can trigger is
  worse than documenting none.
- **`BMX-E030` kept alive.** In 0.6 `:::9lives` was an opener with a bad name; in 0.7 `:9lives:` simply
  fails to be an opener, so it would have become a paragraph starting with a colon. A typo'd block
  rendering as text is the exact silence this format exists to remove, and only the fixture caught it:
  `030-block-name-not-a-name` could not be migrated without the rule.

**A migration is a tool, not a note.** `tools/migrate-0.7.py` rewrites documents and the `bmx` fences
inside markdown, tracking a stack — because a bare `:::` carries no name, so what it becomes depends on
what is open, so a `sed` cannot do it. Handing a consumer a regex would have handed them a silent
mis-migration on their first nested component.

## 0.8 is what happens when a tool consumes a rule

0.8 narrowed `BMX-E012` — an indented list or quote is no longer read as an attempted nest — and it exists
because of a five-line script.

0.7 made leading space insignificant so that nesting could be *seen*. `tools/fmt.py` was written to do
that indenting mechanically, and the first thing it did was round-trip the conformance suite: indent every
fixture, reparse, compare. **Two fixtures stopped parsing.** Indenting `:for:` / `- item` produced *a list
may not nest* about a document containing exactly one list — so the readable form of the single most
motivating example was illegal in the release whose purpose was making it legal.

Nothing in the suite could have caught that. Every fixture was written by someone who believed the rule,
so no case asserted that a list inside an indented block works, because nobody writes a case for something
they think is forbidden. **The tool that consumes a rule is what finds the rule too broad**, and that is a
different instrument from a test: a test asks *does this do what I expect*, a tool asks *can I use this at
all*.

The shape of the mistake is worth keeping too. `- ` and `> ` were refused **as lines**, when nesting is a
property of a line's *relationship to another line* — a marker deeper than the list already open. A rule
stated about the wrong subject will be implemented too widely every time, and it was, twice: every version
through 0.5.1 refused any indented line at all, and 0.6–0.7 refused any indented marker.

## 0.9 is a minor that adds a delimiter, and the question that decided it

0.9 lets a head be delimited — `:name: -> [ … ] body` — so a block can carry a body on one line.
`git diff --stat tests/`: **twelve files added, none modified.** A minor, because the delimiter is
optional and the undelimited form is untouched, so every document written before it means exactly what
it did.

The alternative was making brackets the *only* head form: uniform, one spelling per concept, and a
major that would have re-swept star-burxt's 72 examples two days running. **Two spellings is honest here
because each has a distinct job** — the undelimited head takes the whole line and has no delimiter to
collide with, which is also the escape hatch for a head containing `]`.

**What the delimiter buys is the format's own guarantee, not syntax.** A host can already pass a body as
an attribute (`child="…"`), and star shipped that — but an attribute value is a string BMX never looks
inside, so `child="**bold**"` is six characters and nothing escapes it. After a `]`, the body is inline
content: real emphasis, real slot nodes, escaped by the format. That is the difference between a
workaround at the boundary and a feature inside it.

And `->` rather than `=>` or a bare `[`, which is worth recording because two of the three are wrong for
measurable reasons: `=>` is the host's match arm, so `:case: Post(id) => [x]` would read as one; a bare
`[` collides with `[text](url)`, so a body beginning with a link would be ambiguous. `->` is the host's
return arrow — 556 occurrences in its standard library against 135 for `=>` — so it is the glyph a reader
already parses fluently, and its direction reads correctly: name, then what is attached.

## 0.9.1 is a patch that changes what a document means, and saying why is the point

0.9.1 makes a delimited head end at the first `]` **outside a quoted value or a slot**. 0.9.0 took the
first `]` at all, so `-> [title="a]b"] hi` parsed as head `title="a` with body `b"] hi` — silently.

**By the letter of the rule at the top of this file, that is a major**: a document that parsed one way
parses another. The mechanical test says minor (fixtures added, none modified), and the honest question —
*what document valid today changes meaning* — has a real answer.

It is called a patch anyway, and the reasoning is the part worth keeping rather than the number:

- **The old behaviour was a defect, not a contract.** It produced a head the author did not write and a
  body containing the wreckage of one. Nothing could have depended on it deliberately.
- **The window was one hour.** 0.9.0 was tagged, the one consumer asked whether a `]` inside a quoted
  value was still the first `]`, and said they had built nothing on the answer. So the set of documents
  whose meaning changes is empty, and known to be empty rather than assumed.

**The general rule this adds:** the mechanical test answers *did the suite change*, and the honest
question answers *could a document change*. Neither answers *did anyone have time to rely on it*, and
for a defect found inside its own release, that third question is the one that decides. Write the
reasoning down rather than the number, because the number will look wrong to whoever reads the diff.

## 0.10 is a major that fixes one defect in three places

Three delimiters, each ending at its own first occurrence, each silently:

    {{ pick("}}", n) }}       expression became `pick("`
    [Foo](/wiki/Foo_(bar))    target became `/wiki/Foo_(bar`
    -> [title="a]b"]          head became `title="a`     (fixed in 0.9.1)

**A major, by the honest question rather than the mechanical one.** `git diff --stat tests/` shows only
additions, so the rule at the top of this file says minor. But `[a](/x(y` was accepted before and is
`BMX-E004` now — *a document that was valid becomes an error*, which is the definition. Unlike 0.9.1
there is no one-hour window to appeal to: slots and links have been in the format since 0.1, so a
document with an unbalanced paren in a target has had every release to exist.

**Why refusing beats the alternative**, since the alternative would have kept it a minor: falling back to
the first `)` when the parens do not balance preserves every document that parses today, and preserves
the silent truncation with it. That is the trade — one version number against a class of wrong answers
that says nothing. The format's whole claim is that it fails loudly, so the version number is the cheaper
thing to spend.

**And the rule is stated ONCE now, in §3, as one rule with three instances**, because that is what it is.
Fixing the head in 0.9.1 and stopping there would have been the shape this project keeps re-learning:
nine escape defects that were one recursion, five separator checks that were one predicate, three
consuming loops that needed one refusal. star-burxt found three more instances of this same defect in its
own scanners on the same day, which is the strongest evidence that the sentence — *a delimiter rule has
to know what protects a delimiter* — is worth more than any of the six fixes.
