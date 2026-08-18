---
layout: default
title: Writing a document
---

{% raw %}
# Writing a document

Every construct BMX 0.11 has, what it renders to, and the rule that decides it. **Every HTML
sample on this page was produced by running a real renderer, not typed by hand.**

If you know markdown you already know most of this. The differences are deliberate and there are
only a few: **one spelling per construct**, anything malformed is an error rather than literal
text, and one construct markdown has no equivalent for — the [block](#blocks), which is how a
document repeats, branches, and calls a component.

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
- **List nesting is not in 0.4.** An indented line is an error rather than a guess. (Blocks
  nest — see below — lists do not.)

### Quotes

```bmx
> A quotation
> over two lines
```

→ `<blockquote>A quotation\nover two lines</blockquote>`

No nested quotes in 0.4.

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

## Blocks

Everything above is markdown. **This is the one construct that is not**, and it is where a document
stops being a page and starts being a component.

```bmx
:for: line in order.lines
  - {{ line.sku }} × {{ to_string(line.qty) }}
:!for:
```

A block is `:name:`, an optional **head**, a body, and `:!name:`. And the important
part is what BMX does with the head: **nothing**. It captures the text and hands it to whatever is
rendering the document, exactly like a slot.

**So BMX does not know what `for` means.** The host declares it — which is why `for`, `if` and a
component you wrote are not three features. They are one feature used three times:

```bmx
:if: order.has_discount
  You saved {{ to_string(order.saved) }}.
:!if:

:card: title="Pricing" .featured #plans
  Any **markdown** in here, and slots too.
:!card:
```

### Nesting

**Blocks nest by name, so there is nothing to count** — each closer says what it closes:

```bmx
:for: section in page.sections
  ## {{ section.title }}

  :card: title="Detail"
    {{ section.body }}
  :!card:
:!for:
```

### Indentation

**Indent it however you like — the parser does not look.** Leading spaces are removed before a line is
read, so these two documents are the same document:

```bmx
:section: class=card
  # Today
  :for: task in model.tasks key to_string(task.id)
    :button: on:click=Msg.Toggle(string_to_int(key, 0))
      {{ task.label }}
    :!button:
  :!for:
:!section:
```

Without it, four closers stack at the bottom and nothing says what any of them closes — a reader has
to count openers upward to find out whether the third closer ends the button or the loop. Indented, each
closer sits at the column of the thing it closes and **nothing has to be counted**.

Two things this deliberately is not:

**It is not a second nesting rule.** A block nests by *containment* — its fences say where it ends —
and indentation says nothing at all. Two rules that can disagree is markdown's indented-list problem,
and one document cannot have two answers about its own shape.

**It is not what makes nesting checkable.** That is the closer's job: `:!button:` names what it closes
and a mismatch is [`BMX-E035`](errors.html). Indentation is for the eye and cannot be wrong, because it
means nothing — which is also why it cannot catch anything. The two do different work, and you want
both.

The exceptions are the two constructs that have no nesting at all — an indented `- ` or `> ` is
[`BMX-E012`](errors.html#bmx-e012--list-or-quote-nesting-which-07-does-not-have), and a tab in leading
whitespace is [`BMX-E010`](errors.html) whatever it is doing there, because its width is a matter of
opinion in every dialect. A code fence may be indented too, and its content keeps everything past the
fence's own indentation.

### Classes, ids and attributes

A head may carry them, and this is the one part of a head BMX has an opinion about:

```bmx
:card: title="Pricing" .featured .wide #plans
```

- `.name` is a class, `#name` is an id, both using the name rule above.
- **At most one `#id`** — a second is `BMX-E033`, because an id is an address and a block with two
  has no answer to *"where is it"*.
- **Everything else is the host's**, including `title="Pricing"` and `on:click=save(line.id)`. BMX
  captures the text and does not decide what an attribute means.

**A block emits nothing by itself.** The host decides what `card` renders and whether `on:click`
becomes anything at all — which is what keeps a format with no runtime from acquiring one.

### A head on one line with a body

`-> [ … ]` says where the head stops, so the rest of the line is the body:

```bmx
:button: -> [on:click=save(id), .featured, #plans] Save :!button:
```

- **The head is the bytes between `[` and the first `]`** that is not inside a `"…"` value or a
  `{{ … }}` slot — so `-> [title="a]b"]` and `-> [class={{ tags[0] }}]` hold the bracket they were
  written with. `BMX-E037` if that `]` never arrives.
- **Everything after the `]` is body**, and on a one-liner it is *inline content* — so `**bold**` is
  emphasis and a slot is a slot, both escaped by BMX. That is the difference from a host attribute
  carrying the same text, which is a string the format never looks inside.
- **The delimiter is optional.** Without it there is no body: `:span: class=text hello :!span:` puts
  `hello` in the head, because the format cannot tell where your attributes stopped.
- **A body after the `]` needs the line to close** — `BMX-E038` otherwise, because the body would
  have two sources and no reader could tell which won.

**Put nothing after the `]` and the body goes below, as usual:**

```bmx
:button: -> [on:click=save(id), .featured, #plans]
  Save
:!button:
```

Which is the same block as the one-line version above — the delimiter says where the *head* stops, and
whether the body shares the line is separately your choice. Use it when the head is long enough that the
line would wrap, or when the body is more than a few words.

`->` and not `=>`: both are Burxt tokens, and `=>` is the match arm, so `:case: Post(id) => [x]` would
read as one. A bare `[` cannot work either — `[text](url)` is a link, so a body beginning with one
would be ambiguous.

### Declaring what a document needs

A `props` block gives a document its own signature, so another document can call it:

```bmx
:props: title: String, featured: Bool
:!props:

# {{ title }}
```

`props` is a block name like any other; the head is captured opaquely like every other head. See
[Views that check themselves](guide/04-views-that-check-themselves.html) for what the compiler then
does with it.

### Inline blocks

The same idea inside a sentence:

```bmx
Press ::key["Ctrl+S"]:: to save.
```

`::`, a name, `[`, a head, `]`, `::`. **An inline block is not a slot**, and the difference is the
guarantee: a slot's value is always escaped, while an inline block is a call to something the host
declared. They look different because they are different, and you should be able to tell at a
glance which one can produce markup.

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

## What 0.11 does not have

Named with the trigger that would earn each one a version, because a list of omissions with no
reasons invites someone to fix them at random.

| Absent | What would earn it |
|---|---|
| Nested **lists** and quotes | a real document that needs one. Blocks nest; these do not |
| Tables | the same — the most-requested markdown extension and the least uniform |
| Images | a decision about whether a target is a URL or a host expression. A host can declare an `image` block today |
| Raw HTML passthrough | it would put an unescaped hole in the format; that waiver belongs to the host |
| `match` | it reduces to `if` for presence, and branching on data shape is host logic |
| Error recovery | one error at a time, so two implementations cannot disagree about how to carry on |

**Loops, conditionals, components and event bindings are not on this list**, and 0.1's reasoning
for refusing them is worth knowing because it was half right. *A view is a function and the host
already has control flow* — true when the host compiles the view, false everywhere else. A receipt
with N line items could not be written in BMX at all: the host had to build the list, so the markup
for a line lived in the host's code rather than in the document.

They arrived as **one construct**, which is why the grammar went from ten rules to thirteen rather
than to thirty.
{% endraw %}
