---
layout: default
title: Putting values in
section: guide
description: A slot is a blank in a form letter. The question is what happens when nobody fills it in.
---

{% raw %}
# 2. Putting values in

## What this is for

A page about nothing is a document. A page about *your order* needs values from somewhere.

In BMX the blank is called a **slot**, and it looks like this:

```bmx
Dear {{ customer.name }},

Your total is {{ order.total }}.
```

Bind `customer.name` to `Ada Lovelace` and `order.total` to `$59.97`, and out comes:

```html
<article class="bmx"><p>Dear Ada Lovelace,</p><p>Your total is $59.97.</p></article>
```
<figure class="shot">
  <img src="/assets/examples/slots-receipt.png" alt="A receipt document with slots, and the rendered page">
  <figcaption>Slots filled in. Change the values and the page changes; change the document and the layout does.</figcaption>
</figure>


## Think of a form letter

You have seen the paper version: *"Dear ________, your account ________ is now ________."*
Somebody fills in the blanks and posts it.

Everybody has also received the version where it went wrong:

> **Dear ,**
>
> Your order  is ready for collection.

Nobody typed that. A blank did not get filled and the machine **printed it anyway**, because an
empty string is a perfectly good string and nothing was watching.

That is the interesting question about slots, and it is not "how do I put a value in". It is
**what happens when the value is not there.**

## BMX refuses

```bmx
Dear {{ customer.nmae }},
```

A typo — `nmae`. Here is what happens:

```
BMX-R002: no binding for slot `customer.nmae` at 8
```

**An error. Not an empty string.** The page does not render, so the page cannot ship saying
*"Dear ,"*.

Compare that with what almost every other template language does with the same typo:

| | Result |
|---|---|
| Handlebars | renders nothing, page ships |
| Jinja2 (default) | renders nothing, page ships |
| Mustache | renders nothing, page ships |
| ERB | raises — but only if the object is nil in the wrong way |
| **BMX** | **refuses; nothing renders** |

The `at 8` is a byte offset — character 8 of your file, which is where `customer.nmae` starts. Your
editor can jump there.

## The value is always escaped

Say the customer's name is, for whatever reason:

```
<script>alert('hi')</script>
```

You do not have to think about that. The value comes out as **characters, not markup**:

```html
<p>Dear &lt;script&gt;alert(&#39;hi&#39;)&lt;/script&gt;,</p>
```

There is no way to turn this off from inside a document. There is no `{{{ raw }}}` and there never
will be — three characters is too little to stand between a correct page and a compromised one. If
a host genuinely needs to emit trusted markup, it does that in its own code, on a line somebody can
find.

## What goes inside the braces

**BMX does not know.** It reads the text between `{{` and `}}`, trims the spaces, checks it is not
empty, and hands it to whatever is rendering the document.

So in a simple renderer, `{{ order.total }}` is just a **name to look up**. In [Burxt](https://burxt-lang.org)
it is a real expression the compiler checks — which is [page 4](04-views-that-check-themselves.html),
and the reason to keep reading.

Two rules that are BMX's, though:

**A slot must close on its own line.**

```bmx
Dear {{ customer
.name }},
```
```
BMX-E001 at 5: unterminated slot: no }} on this line
```

If slots could span lines, an unterminated one would look exactly like an ordinary paragraph — and
you would find out from a reader.

**A slot in a code block is not a slot.**

````bmx
```
{{ this is just text }}
```
````

That is what makes it possible to write documentation about BMX, in BMX.

## Slots are values — repetition and branching are blocks

A slot is always **a value**. There is no `{{#if}}` and no `{{#each}}`, and that is not because
BMX cannot repeat — it is because anything that opens and closes is a different shape:

```bmx
::: for line in order.lines
- {{ line.sku }}
:::
```

That is a **block**, and it is one construct that also gives you `::: if`, and components you
declare yourself. [Writing a document](../syntax.html#blocks) has the whole of it, and
[page 4](04-views-that-check-themselves.html) is where it gets interesting — inside that loop,
`line` is a real value with a real type, and `{{ line.sk }}` is a build error naming the field.

What blocks deliberately are **not** is a place to put logic. `for` and `if` describe *structure* —
what repeats, what appears. Deciding *what is true* stays in the host language, which has types,
tests and a debugger, and is much better at it.

---

**Next:** [When BMX says no](03-when-bmx-says-no.html) — why refusing is the feature, not the
friction.
{% endraw %}
