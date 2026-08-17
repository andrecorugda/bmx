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

So the rule stands as a *floor*, not a proof: **an edited case proves a major; added cases only fail
to prove one.** Before calling a change minor, the question that has to be asked by hand is *what
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
