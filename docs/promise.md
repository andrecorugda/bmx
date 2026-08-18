---
layout: default
title: The promise
description: "Your document means the same thing everywhere — and here is how that is known rather than hoped."
---

{% raw %}
# Why documents agree

**A document you write today means the same thing in every tool that reads BMX, and will still mean
it next year.** That is the promise. This page is how it is kept, because a promise nobody can check
is a wish.

You do not need any of this to write a document. It is here for the moment you wonder whether to
trust the format with something that matters.

## The problem it is answering

Markdown has three main dialects and they disagree. The same file gives you different pages
depending on which tool opened it, and there is no way to tell from the file which one you meant.
Most of the time it does not matter. Then one day the thing that renders your page changes, and a
document you wrote years ago quietly comes out different.

That happened because markdown was described in prose, and prose leaves room. Two people read the
same paragraph and build two different things, both convinced they are correct.

## So the rules are files, not paragraphs

BMX is written down twice: once as an explanation, and once as **a folder of documents paired with
exactly what each one should produce.** Around sixty of them, covering every construct and every way
a document can be wrong.

Anyone writing a tool that reads BMX runs their tool against that folder. Either it produces what
the files say, or it does not. There is no room to interpret, and no discussion to have.

**Where the explanation and the files disagree, the files win.** That rule exists so that the answer
to *"what does BMX do here?"* is always something you can run rather than something you can argue
about.

## And two tools are checked against each other

Passing the tests proves a tool matches what was written down. It cannot prove that what was written
down covers everything — a test suite is made of the things somebody thought of.

So there are two independent implementations of BMX, and they are also run against each other over
the same documents. Where they disagree, something was never decided, and that is exactly where a
format quietly rots.

**It has already earned its place.** One of them was reporting a position inside a paragraph three
characters early, in a case nothing in the suite covered. Writing the second implementation is what
surfaced it. It is a test now, so it can never come back.

## What this does not yet claim

**Both implementations were written by the same author.** That means they catch mistakes and
accidental changes; it does not prove the written rules are unambiguous, because one person can
misread their own sentence twice the same way.

The version number says so honestly. BMX is **0.11**, and it becomes 1.0 when someone who did not
write the rules builds a tool from them and it passes — not when the feature list looks finished.

## How versions work, in one line

A change that only **adds** documents to that folder is a small version bump: everything you have
written still means what it meant. A change that had to **edit** an existing one is a big bump,
because some document somewhere now comes out differently.

That makes the version number a fact about the folder rather than a judgement call, and it is why
you can upgrade a minor version without reading a migration guide.

---

If you want the rules themselves — the grammar, the error codes, the test files — they are in the
project's repository, linked from the top of every page. This page is the part worth knowing before
you decide to trust it.
{% endraw %}
