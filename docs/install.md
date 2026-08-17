---
layout: default
title: Getting BMX
description: BMX ships with Burxt. In any other language it is one file, or a spec and a suite.
---

{% raw %}
# Getting BMX

BMX is a **format**, so what you install depends on what you want to do with it. Three answers,
shortest first.

## In your editor — first, because it needs nothing else

Colour, a live preview and inline diagnostics come from an extension that bundles its own renderer,
so it needs **no compiler and no toolchain**:

```sh
code --install-extension bmx-0.1.0.vsix
```

Helix and Neovim get diagnostics from a language server that needs only Node. All three are on
[In your editor](editor.html).

Everything below is for *rendering* documents from a program, which is a different job.

## In Burxt — a package you pin

BMX used to ship inside the language, as `lib/bmx.bx`. **It does not any more**, and the change is
worth understanding rather than working around: a module in somebody else's standard library has
that language's version and no say in its own. BMX is 0.6 and Burxt is 1.3; one number could not
honestly carry both.

So it is a dependency, named in your `burxt.package`:

```
name        my-app
version     0.1.0
dependency  bmx  https://github.com/andrecorugda/bmx  burxt-0.6.0
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

### If you reached BMX through another package, you still have to declare it

This is the one thing about installing BMX that will look like your mistake and is not. If you
depend on something that depends on BMX — [star-burxt](https://star.burxt-lang.org/), say — **you
must declare BMX yourself, under the same name that package uses**:

```
dependency  star  https://github.com/andrecorugda/star-burxt  v0.1.0
dependency  bmx   https://github.com/andrecorugda/bmx         burxt-0.6.0  # star needs this
```

Leave the second line out and you get:

```
error: cannot read <star-burxt>/bmx/burxt/bmx.bx: No such file or directory
  ...used by <star-burxt>/star.bx
  ...used by app.bx
```

**Read that error carefully, because it names nobody.** It looks like a broken install of
star-burxt, so the natural next move is to go looking for a mistake in your own program — and there
is none. What happened is that `use "bmx/…"` inside star-burxt was resolved against *your*
dependency list, found nothing there, and fell back to a relative path inside star-burxt's own
directory.

Burxt resolves package imports against the **root** manifest only: a dependency's own manifest is
never read. That is what keeps this repository from having to be a Burxt package at all — nothing
here declares one — and it is the same rule seen from the other side. Whether it should change is
Burxt's to decide; until it does, one extra line is the whole workaround, and the versions have to
be kept in step by hand.

> **Needs Burxt 1.3.0 or later.** 1.2.0 was the first release that knew `use "std/…"`, which is how a
> package reaches the standard library at all — but 1.3.0 is the floor now, because parts of the
> implementation are declared `pure` and that rests on a `pure string_to_int`, which 1.3.0 is the first
> to mark. On 1.2.0 the compiler says so rather than guessing:
>
> ```
> error: `pure function bmx_parse_error` may not call `string_to_int`, which is not declared `pure`
> ```

### The two command-line tools

Both are ordinary Burxt programs, in this repository beside the implementation:

```sh
burxt build burxt/examples/parse.bx    -o bmx-parse      # a document -> its AST, as JSON
burxt build burxt/examples/generate.bx -o bmx-generate   # a document -> a typed Burxt view
```

### Read your document from a file, not a string literal

The first thing most people try is passing a document straight to `bmx_parse`, and it does not
compile:

```burxt
bmx_parse("Total: {{ order.total }}")
```

```
error: in the interpolation `{{ order.total }}`: expected an expression, found `{`
```

**Burxt has its own `{ … }` interpolation inside string literals, and it reaches BMX's slot first.**
Nothing is wrong with either language — they simply want the same two characters, and the error
names Burxt's feature rather than the collision, so it reads as a puzzle rather than an answer.

Read the document from a file and it goes away:

```burxt
match file_read_maybe("doc.bmx") {
    None => { print("no document"); }
    Some(source) => { /* bmx_parse(source) */ }
}
```

That is what `.bmx` files are for anyway. It is worth knowing before you write your first test
rather than during it.

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
release channel, and BMX is 0.6 with two implementations by one author. Copy the file instead —
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

**It reads documents; it does not check what is inside `{{ … }}`.** Nothing is missing — BMX leaves
the contents of a slot to whatever language is rendering, and JavaScript has nothing to check them
against. In [Burxt](https://burxt-lang.org) it does get checked, which is
[chapter 4](guide/04-views-that-check-themselves.html).

## In any other language

Nothing to install, and nothing stopping you — BMX is a format, so a reader for it is a few hundred
lines in any language. [Building on BMX](building-on.html) has what you need and what to check
yourself against.

## Which version am I getting?

BMX has its own version, separate from whatever language you are using it from. Yours can be at 3.0
and target BMX 0.6 quite happily.

Upgrading between small versions never changes what your existing documents mean — that is what the
numbering is for, and [Why documents agree](promise.html) explains how it is kept true rather than
merely intended.

{% endraw %}
