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

> **An edited case in [`tests/cases/`](tests/cases) proves a major. Nothing proves a minor.**

The first half is mechanical and still is: `git diff --stat tests/cases` with a modified file means a
document's expected output moved, so a document's meaning moved, so it is a major — no judgement
involved. Reach for that first, because it settles most releases without an argument.

**The second half is the part this document originally got wrong**, and it said the opposite: *a change
is a major if and only if a case had to be edited*. That "only if" is false in three ways, each found by
a release that broke it, each written up below:

| when the mechanical answer is wrong | which release found it |
|---|---|
| **added cases cannot acquit** — a change can break a document no fixture contains | 0.7, the one-line block |
| **`tests/errors/` is not `tests/cases/`** — a *deleted* refusal is a widening, so a minor | 0.8, the narrowed `BMX-E012` |
| **a defect found inside its own release** has no window for anyone to depend on it | 0.9.1, the truncated head |

So the question the rule cannot answer for you, and which has to be asked by hand every time:

> **What document is valid today whose meaning this changes?**

If the answer is not "none", the fixture for it is missing and belongs in the same commit. If the answer
is "none, and I know that rather than assume it", say how you know — 0.9.1 says *the only consumer asked
about the behaviour instead of building on it*, which is evidence rather than optimism.

**Why the rule is stated with its exceptions rather than above them.** It was not, until 2026-08-18: the
absolute version stood at the top with four corrections appended below it, so a reader who read the top
got a rule that was false four times over. The Burxt session named the shape while correcting their own
notes — **a correction appended below a wrong sentence leaves the wrong sentence for whoever reads the
top, and reading the top is what people do.**

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

## 0.11 came from a peer's search key, not from a suite

star-burxt offered a better way to hunt this class than "look at delimiters": **look for a scanner whose
failure mode produces something that still parses.** Applied to the places in BMX that key had not been
pointed at, it found two things a suite could not:

- **`HTTPS://example.com` was refused.** A URI scheme is case-insensitive (RFC 3986 §3.1), so that is a
  correct URL and BMX rejected it — a *false refusal of correct input*, which is the one class a
  conformance suite structurally cannot contain, because nobody writes a case asserting that something
  they believe illegal actually works. A widening, therefore a minor.
- **`[Home]({{ url }})` rendered `href="{{ url }}"`.** A broken link, on a page, silently. Refused now
  (`BMX-E005`), which makes a valid document an error — a major.

So the release is both at once, and it is one tag rather than two because the consumer sweeps once.

**And the third finding was in this repository's own claims rather than its code.** `ESCAPING.md` said
*"the conformance suite tests this"* about the scheme refusal, and pointed at
`tests/pass/bmx_library.bx` in the Burxt repository — a path that went away with the `lib/` migration.
Nothing tested it: `renders.py` compares the two renderers and treats **both refusing as agreement**, so
if both had stopped refusing `javascript:` it would still have passed. `tests/output.py` asserts the
outcome per renderer now, sixteen targets, and its control is a renderer that renders nothing, which must
fail all sixteen.

The lesson is not new but the location is: **the security-critical half of the contract was held by a
sentence, and the sentence named a file that did not exist.** A normative document pointing at a missing
test is worse than one pointing at none, because a reader who goes looking concludes they have the wrong
checkout.

## 0.11.1 is a patch, and the finding came from grepping prose for verbs

star-burxt named the family after 0.11: **a claim in prose is a specification nobody runs.** The grep is
not for a token, it is for the *verbs* — *checked*, *refused*, *cannot*, *the tests* — and then asking of
each claim whether anything would notice if it stopped being true. Pointed at this repository's own
normative documents it found two, and one of them was a defect in the code rather than in the prose.

**`SPEC.md` §4a.4 said an inline block's head "may not contain an unescaped `]`", and both halves were
false.** A `]` not followed by `::` has always been accepted — `::key[a]b]::` has the head `a]b` — and `]`
is not in the escapable set at all, so "unescaped" described a mechanism that does not exist. The real
rule is that the head ends at the first `]::`, which is a better rule and is now what the document says.

**And chasing that sentence found a false refusal.** `::key[Ctrl+S]:: saves` — an inline block at the
start of a line — was refused as a block with an empty name, because 0.7's malformed-opener pattern used
`*` where it needed `+` and therefore matched `::`. **The reference implementation only:** `bmx.bx`
excludes `::` explicitly, so the two implementations disagreed and `tests/agree.py` never saw it, because
the one fixture beginning with `::` has it inside a code fence.

That is why this is a **patch and not a widening**: SPEC §4a.4 puts no line-position restriction on an
inline block, so the format never changed — one implementation was non-conforming and now is not.

**The second prose claim was true and untested.** `docs/styling.md` says *"the info string is checked as a
name before it becomes a class, so a document cannot inject an attribute through it"*. It is true —
`x" onload="steal()` produces no class at all. Nothing asserted it, and every fixture used `burxt` or
`js`. It is the one place a DOCUMENT's own bytes reach an attribute, which makes it the same hazard class
as a link target, so it lives beside them in `tests/output.py` — renamed from `targets.py`, because a
file whose name describes half of what it does is the stale-pointer defect this release is about.

## 0.11.2: the stale claim that was a status, not a rule

star-burxt found a chapter saying *"you cannot put a button inside a `for` yet"* about a feature that
works, and named the asymmetry: **a stale DONE gets found the first time somebody tries the thing; a
stale NOT-DONE is found by nobody**, because a reader who is told a feature is absent believes it and
leaves.

The same sweep here found three status claims stale at once, and the third is the one that matters:

- `README.md` said the format was **0.4**
- `docs/promise.md` said **0.2**
- `docs/building-on.md` listed *"what DOES exist, as of 0.2"* — a capability list frozen before offsets,
  named closers, insignificant indentation and delimited heads existed. **A framework author reading that
  page would not have known a one-line block can carry a body**, which is exactly the readers-turned-away
  failure, in the document whose own first sentence warns about it.

Fixing three sentences is not the work. `tests/version.py` is: the version lives in **one** place, the
title of `SPEC.md`, and every status claim in the documentation is checked against it. Its control adds a
claim naming a version that is not current and requires the check to fail.

**Why it greps phrasings rather than keeping a list of files:** a registry of known sites cannot see a
claim added somewhere new. Historical references — *"0.6 nested by fence length"*, *"until 0.5.1"* — are
worded differently on purpose and must keep working, so the one thing a person still has to maintain is
the list of *shapes* a status claim can take. That is written at the top of the file.

**And the fourth face of a lying measurement, which is star's and belongs with the other three:** not a
pattern that matched nothing, not an equality that matched, not an assertion that could not fail, but **a
runner that could not report one.** They had been reading `python3 test.py | tail -1`, which reports
whether `tail` succeeded; three failures sat visible and unread. `tools/check.sh` was already sound — it
captures each command's own status — but it now sets `pipefail` as well, because the next inline pipe
somebody adds to it should not be the one that lies.

## 0.12: the format gains a comment, because it had one and it was visible

star-burxt, answering Andre's question about what would make it stable, measured this end to end:

    <!-- TODO: ask a designer about this -->
    Hello

    rendered:  <p>&lt;!-- TODO: ask a designer about this --&gt;\nHello</p>

**A developer's private note, delivered to the reader.** Accepted rather than refused, which is the
silent-wrong-answer class this format exists to remove — sitting in the one construct every author of
every markup format reaches for. They hit it on their own tooling before going looking, and patched
around it by stripping a header; **an author cannot patch around it.**

A major: `<!-- x -->` was a paragraph and is now nothing, and `Total: 5 <!-- x -->` was text and is now
`BMX-E007`.

**Why `<!-- -->` and not a new sigil.** Markdown has no comment either, so this is what an author already
types in every dialect — and it is the one HTML spelling with **no output**, so claiming it is not the raw
HTML passthrough §7 refuses. A `:comment:` block could not have done the job at all: a level-1 renderer
refuses a block it does not declare (`BMX-R003`), so a host-declared comment would make a `.bmx` and a
host's document accept different inputs, which is the split the boundary exists to prevent.

**Why a comment is a whole line.** Closing half of this would have been worse than closing none:
`Total: {{ x }} <!-- fix this -->` would still ship the note. `BMX-E007` refuses a mid-line marker and
names the alternative — a code span, `` `<!-- x -->` ``, which shows the characters literally.

**And the first version of that refusal broke the alternative it names.** Checking the whole string on
entry to the inline parser refused `` `<!-- x -->` `` too: a fix for a silent wrong answer introducing a
false refusal of correct input, in minutes, because the check ran before the scan could reach the
construct that protects its content. Moved to the point where a `<` becomes ordinary text — which is
where star-burxt's own comma fix had to go, and where every scanner fix this week has ended up.

**Also declined and recorded rather than left open:** a dynamic block name, `:{{ tag }}:`. star-burxt
asked and then argued against its own request — a name arriving at runtime means the content model is
unknown until it runs, so a host cannot tell an author that a `<p>` may not hold a `<div>`. `BMX-E030`
stays, and §7 says why so nobody re-raises it.

## 0.12.1: six documented calls, five of them unreachable

A patch, and the reason it was tagged without an entry here is worth the entry: the fix was small and the
finding was not. `docs/` told a host to call `bmx_to_html`, `bmx_bind`, `bmx_json`, `bmx_html` and
`bmx_emit_burxt`. **None of them was `public`, so a dependent package could not reach any of them** —
somebody following the documentation writes the call and stops.

**Nothing caught it because the boundary is the PACKAGE, not the file.** A non-`public` function called
from another file in the same tree compiles happily, so `public` had been applied to whatever
`burxt/examples/` needed — and those live inside the package. **No test that stays inside this repository
can see the boundary at all.** CI's one consumer test called `bmx_parse`, the single name that worked.

`tests/surface.py` reaches every documented name from a real dependent package, and it checks **both
directions**. The reverse one is worse: six functions were `public`, depended on by star-burxt, and
mentioned in no documentation — so `VERSIONING.md`'s compatibility promise covered half the surface a
consumer was actually using. **Reachable-and-unwritten is worse than written-and-unreachable**: the first
breaks a consumer silently at some later date, the second stops them at the keyboard today.

Its control has to be a genuinely private function *discovered from the source*. Aimed at an invented
name, the compiler answers `unknown function` — a refusal, convincing, and nothing to do with visibility.

## 0.12.2: thirty commits changed the extension and its version never moved

No format change, so the suite is untouched and this is a patch by the rule at the top. What moved is the
thing a user installs.

`git log -- editors/vscode/bmx-0.1.0.vsix` counts **thirty** commits. Unzipping the first against the last
gives two different grammars — an 8,931-byte one that knows only `::: card`, and a 13,235-byte one that
knows `:name:` / `:!name:` — **both declaring version 0.1.0.** VS Code decides whether to offer an update
by comparing versions, so anyone who installed the extension before the 0.7 respelling has a highlighter
that paints today's documents wrong and an editor telling them they are current. There is no symptom
except colour.

**The cause was ergonomic, which is why care would never have fixed it.** The version was in the
*filename*, so it appeared in seven places — two READMEs, three doc pages, the packer's docstring, CI —
and bumping it broke every install command in the repository. **A version that is expensive to change is a
version that does not change.** So the filename lost its version (`bmx.vsix`, stable) and the version now
lives only where a tool reads it. The extension's `major.minor` must equal `SPEC.md`'s; the patch is free.

**Two things had to be built before that could be checked.**

`pack.py` is deterministic now. Three entries carried the current time — the two written from strings, and
`reference/bmx.mjs`, which the packer writes moments earlier — so the bytes moved on every run and a stale
committed `.vsix` was undetectable. Nothing detected it: CI packs and *then* inspects the result. **A check
that regenerates the artefact it is verifying cannot see a stale one.**

And the reproducibility is asserted as a property of the archive, not by packing twice. **The first
version of that check packed twice in a row and passed on the non-reproducible packer**, because a zip
stores timestamps at two-second granularity and back-to-back runs share a bucket. A three-second sleep
exposed it. A test that can only fail when it happens to straddle a boundary is a test that reports
success — another face of the lying measurement, alongside a pattern that matched nothing, an equality
that matched, an assertion that could not fail, a runner that could not report one, and the success the
defect itself produces. **Deliberately not numbered:** the count is kept in one place across two
repositories, and this sentence first said "the fifth" when the tally was already six — a headline a
reader trusts, corrected somewhere they have not reached, which is the disease one level up from the
thing it is about.

**The language server had the identical defect**, found by grepping for the version string I had just
removed: it answered `initialize` with `0.1.0` while producing 0.12 diagnostics, and its own test asserted
the `serverInfo` **name** — the half that never changes. A client logs that field, so every bug report
about a diagnostic would have named the wrong version.
