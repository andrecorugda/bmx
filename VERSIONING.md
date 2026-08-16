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
