---
layout: default
title: When it refuses
---

{% raw %}
# When it refuses

**Every error carries a code, a byte offset and a message.** The code is the part that is the
same in every implementation; the wording after it is that implementation's own, and may be
better in some languages than others.

A conforming parser **stops at the first error**. Recovery — reporting every error at once — is a
a later question and a real want, but recovery that differs between implementations is worse than
none.

Every message below was produced by running a parser, not typed from the spec.

## Structural errors

### `BMX-E001` — unterminated slot

```
Hi {{ name
```
```
BMX-E001 at 3: unterminated slot: no }} on this line
```

A slot must close on its own line. If it could span lines, an unterminated one would look exactly
like an ordinary paragraph — which is the failure this rule exists to prevent.

### `BMX-E002` — unterminated emphasis or strong

```
a *bold sentence
```
```
BMX-E002 at 2: unterminated emphasis
```

**This is the difference from markdown in one line.** Markdown renders that as the characters
`a *bold sentence`. BMX tells you.

### `BMX-E003` — unterminated code fence

The commonest way a page becomes one giant code block. Markdown closes the fence for you at end
of file and says nothing.

### `BMX-E004` — unterminated link

```
see [docs](x
```
```
BMX-E004 at 4: unterminated link target
```

Also fires when a `[text]` is not followed by `(`.

### `BMX-E010` — a tab in significant whitespace

A tab is four columns, or eight, or one, depending on who is looking. A format that promises one
reading cannot contain a character whose width is a matter of opinion.

### `BMX-E011` — malformed heading

```
#Heading
```
```
BMX-E011 at 0: a heading needs exactly one space after its #
```

Also: seven or more `#`, and an empty heading. **It is not read as a paragraph beginning with
`#`** — that reading is how a typo'd heading silently becomes body text.

### `BMX-E012` — list or quote nesting, which 0.6 does not have

```
- one
  - nested
```
```
BMX-E012 at 6: a list may not nest; this line is indented. Put the `- ` at the start of the line, or make it a block — see §4a.2
```

Refused rather than guessed at. **Blocks nest** — see [`:::` blocks](syntax.html#blocks) — lists
and quotes do not, and a real document that needs it is what would earn it a version.

**It fires for an indented `- `, `<digits>. ` or `> ` and nothing else.** Indentation elsewhere is
invisible to the parser (see [Indentation](syntax.html#indentation)), so this is one of two places
where leading space still decides anything, and it decides it by refusing.

*Every version through 0.5.1 refused **every** indented line with this error, so a document like*

```
::: div
  hello
:::
```

*was told a list may not nest, about a document containing no list.* That is the worst shape a
diagnostic can have — confident, specific, and naming something the reader never wrote — and it is why
0.6 exists. If you are on 0.5.1 and see this on a line with no `- ` in it, upgrade; the document was
always fine.

### `BMX-E020` — unterminated code span

An unclosed `` ` ``.

### `BMX-E021` — invalid escape

```
a \q b
```
```
BMX-E021 at 2: only ` * [ { and \ may be escaped
```

A backslash that sometimes escapes and sometimes is a backslash is how every markdown dialect
ends up with a different answer.

### `BMX-E022` — empty slot expression

`{{ }}` — nothing to evaluate.

### `BMX-E030` — a block name that is not a name

```
:::9lives
:::
```

A block name is a letter, then letters, digits, `-` and `_`. A line of **only** colons closes a
block, so a block with no name cannot be written at all — it would be indistinguishable from a
closing fence.

### `BMX-E031` — unterminated block

A `:::` that never closes. Never closed implicitly at end of file, for the same reason an
unterminated code fence is not.

### `BMX-E032` — a closing fence with nothing open

A `:::` line where no block is open. Note that a **longer** fence legitimately closes a shorter
one — `::::` closes a `:::` block, exactly as with code fences.

### `BMX-E033` — a second `#id` on one block

```
:::card #one #two
:::
```

An id is an address. Two of them leaves *"where is it"* with no answer. Classes are unlimited.

### `BMX-E034` — unterminated inline block

```
Press ::key[Ctrl+S to save.
```

An inline block is `::name[head]::` and must close on its own line.

---

## Render-time errors

These are the host's rather than the format's, so the codes are Burxt's. Another implementation
may name them differently; **it must still refuse.**

### `BMX-R001` — a link target with a disallowed scheme

```
BMX-R001: refused a link target whose scheme is not http, https or mailto: javascript:steal
```

Not a character-escaping problem — the danger is the scheme, and escaping every byte of
`javascript:` changes nothing. An implementation written in an afternoon will not think of this,
which is why the spec requires it rather than suggesting it.

### `BMX-R003` — a block the renderer does not declare

```
BMX-R003: this renderer declares no blocks, and `card` at 3 is one.
          Compile the document instead.
```

The spec **requires** a host to refuse a block name it did not declare — never render it, never
skip it silently. A level-1 renderer declares none, because a component's whole value is the
compiler checking the call. Compile the document instead: see
[Views that check themselves](guide/04-views-that-check-themselves.html).

### `BMX-R002` — a slot with no binding

```
BMX-R002: no binding for slot `order.totl` at 10
```

**An error, never an empty string.** Every template language in wide use renders the empty string
here, and that is how a page ships with a missing total that nobody sees.

At level 2 you never meet this one: the same typo is a compile error naming the field and listing
what the type actually has.

### `BMX-G001` — a dangerous link target, at build time

The generator refuses it before a page exists. A document's targets are static text, so this
never needs to reach a render.

---

## Reading an offset

The offset is a **byte index into the document**, and for a slot it points at the first byte of
the **expression** — not at the `{{`. For `Hello {{ user.name }}.` it is 9, the `u`.

That is so a host can underline the text it is complaining about. It is the only reason the field
exists, and getting it wrong is caught by the conformance suite: `023-slot-offset-survives-a-stripped-line`
exists because an early implementation reported an offset three bytes early inside a multi-line
paragraph, off by the trailing spaces stripped from an earlier line.
## Warnings — it renders, and it is probably still wrong

An error means BMX **refuses** the document. A warning means it rendered fine and a reader would
still call it a mistake. Warnings never fail a build, because a linter that does is a linter people
switch off.

**All four are about structure**, which is the only kind of opinion BMX may hold: what is inside a
head or a slot belongs to whatever renders the document, so there is no rule here about naming, about
attributes, or about how a component ought to be written.

### `BMX-W001` — a heading skips a level

```bmx
# One

### Three
```

The outline a reader navigates by now has a gap in it, and a page looks identical either way — which
is why this is worth a warning rather than a glance. Use `##`, or make the parent shallower.

**It is about the jump, never about starting at `h1`.** A document that opens at `##` is correct —
a component's headings are relative to the page that embeds it — so the first heading sets the
baseline whatever it is.

### `BMX-W002` — a block with no head and no body

```bmx
::: bare
:::
```

It renders as nothing. Almost always an unfinished edit.

**Two cases are exempt because they are correct.** A block with a *head* is carrying its meaning
there — `::: props order: Order` and `::: input on:input=save(id)` are both complete. And a **void
element** must have an empty body: `::: br` and `::: hr` are right, and a renderer that gave them
children would be refused. The exempt names are HTML's void elements by default, and a host whose
vocabulary differs replaces the list.

### `BMX-W003` — a link with an empty target

```bmx
A [dead]() link.
```

An empty target points at the current page, which nobody means. Give it a target, or write the text
without brackets.

### `BMX-W004` — a fence longer than its nesting needs

```bmx
:::: card
no nested block in here
::::
```

A longer fence only means something when it **contains** a shorter one. Written without a reason it
reads as significant and is not — and that is the kind of noise a reviewer stops seeing.

## Where you see these

Install the [editor extension](editor.html) and every code on this page appears as you type — red for
a refusal, yellow for a warning. Under the hood it is `bmx-lsp`, which reports these and deliberately
nothing else: completion and hover need to know what a block *means*, and that belongs to whatever is
rendering your document.

{% endraw %}
