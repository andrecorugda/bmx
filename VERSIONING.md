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
