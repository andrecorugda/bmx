---
layout: default
title: How do I…?
description: "Short answers to the things people actually want to do — write this, get that."
---

{% raw %}
# How do I…?

Short answers. Each one is a thing you write and the page you get back. Nothing here needs the
pages before it — jump straight to what you want.

## …put a value on the page

Two braces. Whatever is between them comes from your data.

```bmx
Hello {{ customer.name }}, your total is {{ order.total }}.
```

```html
<p>Hello Alice, your total is £59.97.</p>
```

The value is always made safe for you. If `customer.name` is `Tom & <Co>`, the page shows
`Tom & <Co>` as text — never as markup, never as a broken tag. You do not have to remember to do
anything.

**Now change it:** misspell the field, `{{ customer.nme }}`. You get told, before a page exists.
Most template languages print nothing there and ship the page.

## …show a list of things

```bmx
::: for line in order.lines
- {{ line.sku }} × {{ to_string(line.qty) }}
:::
```

```html
<ul>
  <li>APPLE × 3</li>
  <li>PEAR × 1</li>
</ul>
```

Everything between the `:::` lines repeats once per item, and `line` is the name you chose for
each one.

## …show something only sometimes

```bmx
::: if order.has_discount
You saved {{ to_string(order.saved) }}.
:::
```

Nothing appears when there is nothing to say. Same shape as the list — that is on purpose, and it
is the only shape you need to learn.

## …reuse a piece of a page

Write the piece once, in its own file, and say what it needs at the top:

```bmx
::: props title: String, body: String
:::

## {{ title }}

{{ body }}
```

Then use it by name from anywhere:

```bmx
::: card title="Pricing" body="From £9 a month."
:::
```

**A `.bmx` file is a component.** There is no separate idea to learn — the same document you were
already writing becomes reusable the moment it says what it needs.

## …put a class or an id on something, for CSS

```bmx
::: card title="Pricing" .featured .wide #plans
Any **markdown** in here.
:::
```

```html
<div class="featured wide" id="plans">
  <p>Any <strong>markdown</strong> in here.</p>
</div>
```

`.name` is a class, `#name` is an id. Use as many classes as you like and one id — an id is an
address, and two of them means the page cannot answer *where is it*.

That is all Tailwind, Bootstrap or your own stylesheet needs. See
[Styling the output](styling.html) for the full list of tags you get.

## …make a navigation bar

A bar is a brand and a row of links, and both are ordinary markdown — so you write it in the document,
not in a template around it:

```bmx
# Roast&Co

[Coffee](/coffee) [Kit](/kit) [Search](/search) [Sign in](/signin) [Basket · 2](/basket)
```

```html
<h1>Roast&amp;Co</h1>
<p><a href="/coffee">Coffee</a> <a href="/kit">Kit</a> … <a href="/basket">Basket · 2</a></p>
```

The stylesheet does the rest: `.bmx > h1` is the brand and the first `p` is the links. The
[front page](/) is exactly this — one document, no HTML, and the buttons and search box are links with
a border-radius.

**It works with no framework, and it is positional, so it moves if you add a paragraph above it.** When
that matters, name the region with a block — `::: nav .bar` — and your host decides what it renders as.
[Styling the output](styling.html#a-whole-page-bar-included) has both versions side by side.

## …react to a click

```bmx
::: button on:click=save(line.id)
Save
:::
```

The `on:click=…` part is handed to whatever is rendering your page, untouched. BMX does not know
what a click is — which is why this works the same whether your page is rendered by Burxt,
JavaScript, or something nobody has written yet.

## …show money without it changing behind my back

Write the conversion in the document, where a reviewer can see it:

```bmx
Total: {{ to_string(order.total) }}
```

If `order.total` is exact to two decimal places, that is what appears. If the number you hand it
has more places than the page can show, you are asked to say what should happen rather than having
it rounded for you.

This is the part that is only true in [Burxt](https://burxt-lang.org). Other renderers will show
the number; Burxt refuses to guess.

## …write something that looks like BMX, without it being BMX

Put it in a code block. Nothing inside one is read as markup:

````bmx
```
This {{ stays }} exactly as written.
```
````

That is how these pages document BMX in BMX.

For a single character in ordinary text, put a backslash in front of it: `\*not emphasis\*`.

## …read a document from a file instead of typing it inline

Do this rather than putting a document in a string:

```burxt
match file_read_maybe("receipt.bmx") {
    None => { print("no document"); }
    Some(source) => { /* … */ }
}
```

Burxt uses `{ … }` inside strings for its own purposes, so a document pasted into one confuses the
two. Files avoid it, and `.bmx` files are what you want anyway.

## …find out why it refused

Read the message — it says where and what:

```
BMX-E002 at 16: unterminated strong
```

`at 16` is how many characters into your file the problem starts. Every code and its cause is on
[When it refuses](errors.html), each with the exact input that produces it and the fix beside it.

## …see the whole thing at once

[Writing a document](syntax.html) is the cheat sheet — every construct with the HTML it produces,
on one page.

If you have not written a document yet, start with
[Your first document](guide/01-your-first-document.html) instead. It takes five minutes and you get
a page at the end of it.
{% endraw %}
