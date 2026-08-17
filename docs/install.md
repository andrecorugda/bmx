---
layout: default
title: Getting BMX
description: BMX ships with Burxt. In any other language it is one file, or a spec and a suite.
---

{% raw %}
# Getting BMX

BMX is a **format**, so what you install depends on what you want to do with it. Three answers,
shortest first.

## In Burxt — a package you pin

BMX used to ship inside the language, as `lib/bmx.bx`. **It does not any more**, and the change is
worth understanding rather than working around: a module in somebody else's standard library has
that language's version and no say in its own. BMX is 0.2 and Burxt is 1.1; one number could not
honestly carry both.

So it is a dependency, named in your `burxt.package`:

```
name        my-app
version     0.1.0
dependency  bmx  https://github.com/andrecorugda/bmx  <tag>
```

```sh
burxt fetch
```

Then in a program:

```burxt
use "bmx/burxt/bmx.bx";
```

That gets you the parser, the level-1 renderer, and the generator. See
[Turning it into a page](rendering.html) for which you want.

**Why the path has `burxt` in it**: this repository holds more than one implementation, and
`reference/bmx.js` sits beside it. The first segment is your dependency's name, the rest is where
the file lives — so `bmx/burxt/bmx.bx` reads as *the Burxt implementation, from the bmx package*.

**And what the split buys, since it costs a manifest line**: `burxt.lock` pins a commit, so the BMX
your build used is a fact somebody can check, and it stops moving when Burxt releases. The old
arrangement had a real virtue — the format and its host could not drift apart — but it bought that
by making drift *unrepresentable* rather than *visible*, which is only the same thing while nobody
needs to upgrade one without the other.

> **Today this needs a Burxt built from source.** `use "std/…"` — how a package reaches the standard
> library — is not in a release yet, so no published Burxt can compile this file. That is temporary
> and it is why no tag is minted above.

### The two command-line tools

Both are ordinary Burxt programs, in this repository beside the implementation:

```sh
burxt build burxt/examples/parse.bx    -o bmx-parse      # a document -> its AST, as JSON
burxt build burxt/examples/generate.bx -o bmx-generate   # a document -> a typed Burxt view
```

`bmx-generate` is the interesting one — it is [level 2](guide/04-views-that-check-themselves.html),
where a document becomes a function the compiler checks:

```sh
./bmx-generate receipt.bmx receipt_view "order: Order" > receipt_view.bx
```

If the document declares its own props, the signature argument can be empty:

```bmx
::: props order: Order
:::
```

```sh
./bmx-generate receipt.bmx receipt_view ""
```

## In JavaScript — one file, no dependencies

There is **no npm package**, deliberately for now: publishing a package is a promise to maintain a
release channel, and BMX is 0.2 with two implementations by one author. Copy the file instead —
it has zero dependencies and is written to be read.

```sh
curl -O https://raw.githubusercontent.com/andrecorugda/bmx/main/reference/bmx.js
```

```js
import { parse, BmxError } from './bmx.js'

try {
  const doc = parse(source)      // the AST
} catch (e) {
  if (e instanceof BmxError) console.error(e.code, e.offset, e.message)
}
```

Or run it directly over a file:

```sh
node bmx.js document.bmx     # prints the AST as JSON, or an error and exit 1
```

**It is a level-1 implementation**: it parses. It does not check what is inside `{{ … }}`, because
JavaScript has nothing to check it with — which is the whole of
[`BOUNDARY.md`](https://github.com/andrecorugda/bmx/blob/main/BOUNDARY.md) in one sentence.

## In any other language — the spec and the suite

There is nothing to install. Implement
[`SPEC.md`](https://github.com/andrecorugda/bmx/blob/main/SPEC.md) and check yourself against the
conformance suite, which is **data rather than code** so it needs no runtime of ours:

```sh
git clone https://github.com/andrecorugda/bmx
cd bmx
python3 tests/harness.py '<your parser command>'
```

Your command is run once per document with the path appended, and must print the AST as JSON and
exit 0, or print an error beginning with its `BMX-Ennn` code and exit non-zero. That is the entire
interface.

```
56 cases, 56 passed, 0 failed
```

**Read [Building on BMX](building-on.html) first** if you are implementing rather than using — it
says what a host must do that the format cannot check for you, and refusing a dangerous link
scheme is on that list.

### Checking against the other implementation

The suite asks whether you match what was written down. This asks the harder question — whether
two implementations reach the same answer where nothing was:

```sh
python3 tests/agree.py 'node reference/bmx.js' '<your parser command>'
```

That is where a specification's ambiguities live, and it is how the one in §4a.2 was found.

## Versions

BMX carries [its own version](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md),
independent of any host's. A host may be at 3.0 and target BMX 0.2.

**The conformance suite is the semver.** A change that had to *edit* an existing case is a major; a
change that only *added* cases is a minor. `git diff --diff-filter=M tests/` decides it
mechanically rather than by anyone's judgement.

Currently **0.2**. It is not a standard yet, and
[`VERSIONING.md`](https://github.com/andrecorugda/bmx/blob/main/VERSIONING.md) says what 1.0
requires: an implementation written by somebody who did not write the spec.
{% endraw %}
