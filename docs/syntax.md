---
layout: default
title: Writing a document
---

{% raw %}
# Writing a document

Every construct BMX 0.1 has, what it renders to, and the rule that decides it. **Every HTML
sample on this page was produced by running a real renderer, not typed by hand.**

If you know markdown you already know most of this. The differences are deliberate and there are
only a few: **one spelling per construct**, no nesting yet, and anything malformed is an error
rather than literal text.

## Blocks

A **blank line** ends the block in progress. That is the only separator.

### Headings

```bmx
# Title
###### Six is the limit
```

One to six `#`, then **exactly one space**, then the heading. Renders `<h1>`…`<h6>`.

- `#Title` with no space is an error, not a paragraph. That reading is how a typo'd heading
  silently becomes body text.
- Seven or more `#` is an error. So is an empty heading.
- **There is no underlined heading** (`Title` underlined with `===`). Two spellings of one thing is what this
  format exists not to have.
- Trailing `#` are content: `# Title #` has the text `Title #`.

### Paragraphs

Consecutive non-blank lines that start no other block. Lines are joined with a newline.

**Trailing spaces are stripped**, and there is no two-space line break — an invisible character
that changes the output cannot be reviewed.

### Lists

```bmx
- first item
- second item

1. step one
2. step two
```

→ `<ul><li>first item</li><li>second item</li></ul>` and
`<ol><li>step one</li><li>step two</li></ol>`

- **`-` is the only bullet.** Not `*`, not `+`.
- **Numbers are content, not instructions.** A list written `1. 1. 1.` renders as `1. 1. 1.` —
  nothing renumbers, because a format whose output does not match its source is a format you
  cannot review.
- **No nesting in 0.1.** An indented line is an error rather than a guess.

### Quotes

```bmx
> A quotation
> over two lines
```

→ `<blockquote>A quotation\nover two lines</blockquote>`

No nested quotes in 0.1.

### Code blocks

````bmx
```burxt
let x: Int = 1;
```
````

→ `<pre><code class="language-burxt">let x: Int = 1;\n</code></pre>`

- Exactly three backticks. **There is no indented code block** — indentation is where every
  markdown dialect disagrees.
- The word after the fence becomes `class="language-…"`, which is what every syntax highlighter
  expects.
- **Content is never parsed.** A `{{` inside a code block is two characters, not a slot.
- **An unterminated fence is an error.** Markdown closes it for you at end of file, which is the
  commonest way a page becomes one giant code block with nobody told why.

## Inline

Four constructs, and **each must close on the same line.**

| Written | Renders |
|---|---|
| `` `code` `` | `<code>code</code>` |
| `**strong**` | `<strong>strong</strong>` |
| `*emphasis*` | `<em>emphasis</em>` |
| `[text](target)` | `<a href="target">text</a>` |
| `{{ expression }}` | the value — see below |

One spelling each: no `_emphasis_`, no `__strong__`.

**An unclosed marker is an error, never literal text.** This is the rule that separates BMX from
markdown, and it is why a generated document that got truncated gets told.

### Escapes

`\` makes the next character literal, and it is the only way to write a `` ` ``, `*`, `[`, `{` or
`\` that is not markup. **A backslash before anything else is an error** — a backslash that
sometimes escapes and sometimes does not is how dialects diverge.

### Link targets

The target runs to the closing `)` and may not contain one. **A renderer must refuse a scheme it
does not allow** — `[click](javascript:steal())` is a working attack that no character escaping
addresses, because the danger is the scheme and not the bytes. Burxt's renderer allows `http`,
`https`, `mailto` and relative targets, and refuses the rest at build time.

## Slots

```bmx
Hello {{ user.name }}, your total is {{ order.total }}.
```

`{{`, the expression, `}}`. Everything about the expression belongs to the host language: BMX
trims the spaces, checks it is not empty, requires the `}}` on the same line, and **otherwise does
not look at it at all.**

Three things follow that are worth knowing before you meet them:

**The value is always escaped.** There is no `{{{ raw }}}` and there will not be one — three
characters is too little to stand between a correct page and a compromised one. A host that wants
to emit trusted markup does it in the host language, where the waiver is a named call on a line a
reviewer can grep.

**No control flow.** No `{{#if}}`, no loops. The host already has `if` and `while`, and a view is
a function; control flow inside a template is what turns a view into a program no type system is
watching.

**No slots in code blocks.** That is what makes it possible to document BMX in BMX.

## A complete example

```bmx
# A heading

A paragraph with *emphasis*, **strong**, `code`, a [link](https://burxt-lang.org)
and a slot: {{ name }}.

- first item
- second item

> A quotation
```

With `name` bound to `Ada`, that renders to exactly:

```html
<article class="bmx"><h1>A heading</h1><p>A paragraph with <em>emphasis</em>,
<strong>strong</strong>, <code>code</code>, a <a href="https://burxt-lang.org">link</a>
and a slot: Ada.</p><ul><li>first item</li><li>second item</li></ul>
<blockquote>A quotation</blockquote></article>
```

(Line breaks added here for reading; the renderer emits one line.)

## What 0.1 does not have

Named with the trigger that would earn each one a version, because a list of omissions with no
reasons invites someone to fix them at random.

| Absent | What would earn it |
|---|---|
| Nested lists and quotes | a real document that needs one — the tree already nests, only the parser refuses |
| Tables | the same |
| Images | a decision about whether a target is a URL or a host expression, which makes it a slot question |
| Raw HTML passthrough | it would put an unescaped hole in the format; that waiver belongs to the host |
| Loops and conditionals | a view is a function, and the host has control flow |
| Front matter | it is how a host will declare a view's signature, and it must be designed *with* a host rather than guessed at |
{% endraw %}
