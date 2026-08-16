---
layout: default
title: Views that check themselves
section: guide
description: A recipe card and an order ticket look alike. Only one of them is checked before the kitchen starts.
---

{% raw %}
# 4. Views that check themselves

## What this is for

Everything so far works in any language. This page is about the thing only a host with types can
do, and it is the reason BMX was worth defining at all.

Start with the observation. In almost every program ever written:

- the **database** checks your data,
- the **API layer** checks your data,
- the **business logic** checks your data,
- and then the **template** takes whatever it is given and prints it.

**The template is the last place where nothing is checked.** It names fields that may not exist,
holds types it cannot state, and escapes by convention. It is the one file in the stack that finds
out it was wrong by being looked at.

## A recipe card and an order ticket

A **recipe card** says *"add the zest of one lemon"*. If there is no lemon, you find out at the
stove, mid-service, with the pan hot.

An **order ticket** in a working kitchen goes through the pass first. Somebody checks it against
what is actually in the room. If it says "lemon" and there are no lemons, that is caught **before**
anyone turns on a burner.

Level 1 — everything on the previous three pages — is a recipe card. This page is the pass.

## The same document, checked

Here is a document. Nothing new in it:

```bmx
# Receipt {{ order.reference }}

Thanks, **{{ order.customer }}** — {{ to_string(order.total) }}.
```

Instead of rendering it at request time, you **compile** it into a function:

```sh
./bmx-generate receipt.bmx receipt_view "order: Order" "len(order.reference) > 0"
```

Out comes ordinary [Burxt](https://burxt-lang.org) code:

```burxt
pure function receipt_view(order: Order) -> Html
    requires len(order.reference) > 0
{
    return html_element("article", [html_attr("class", "bmx")], [
        html_element("h1", [], [html_text("Receipt "), html_text(order.reference)]),
        html_element("p", [], [html_text("Thanks, "),
            html_element("strong", [], [html_text(order.customer)]),
            html_text(" — "), html_text(to_string(order.total)), html_text(".")]),
    ]);
}
```

You never edit that file. The point is what happens next: **the compiler reads it.**

## What the compiler catches

### A field that does not exist

Go back to page 2's typo — `order.custmer`:

```
error: `Order` has no field named `custmer`. Its fields are: reference: String,
customer: String, total: Decimal<2, RoundHalfEven>, …
```

At level 1 that was a refusal at render time. Now it is a **build error**, and it tells you what
the fields actually are. The page never existed to be wrong.

### A value of the wrong kind

```bmx
Total: {{ order.total }}
```

`order.total` is money, not text:

```
error: in the call to `html_text`, argument 1 must be String,
       but it has type Decimal<2, RoundHalfEven>
```

So you write the conversion **in the document**, where a reviewer reads it:

```bmx
Total: {{ to_string(order.total) }}
```

That is not ceremony. It means anybody reading the document can see where a number became text —
which is exactly where money goes wrong.

### Money that would quietly round

This is the one worth the whole page.

```bmx
Due: {{ money2(order.amount * order.rate) }}
```

Two amounts at two decimal places. Multiply them and the exact answer has **four**:

```
error: this multiplication of Decimal<2> by Decimal<2> has an exact product with 4
decimal places, and reaching Decimal<2> means rounding it. Say how —
Decimal<2, RoundHalfEven> — or take the exact answer with Decimal<4>.
```

Nothing is broken. There is no crash, no float error. The product genuinely has four places and
the display genuinely has two, and **something has to decide** — so a template that prints it
anyway has silently rounded on your behalf. Do that a hundred thousand times and an auditor asks
about the difference.

Every other web stack loses this at the template boundary, because in every other stack the value
became a string long before it got there. Here `Decimal<2, RoundHalfEven>` keeps its scale **and
its tie-breaking rule** all the way to the tag.

### A dangerous link

```bmx
[click](javascript:steal())
```
```
BMX-G001: refused a link target whose scheme is not http, https or mailto
```

Refused at build time, before a page exists. Escaping cannot help with this one — the danger is
the scheme, not the characters.

## And you can diff the promise

A generated view is a function with a signature, so a tool can compare two versions of a document
and tell you whether the newer one promises **less**:

```
WEAKENED  receipt_view   lost `requires len(order.reference) > 0`
```

Component libraries normally version by changelog and hope. This is mechanical: adding a required
field is a breaking change whether or not anyone wrote it down.

## When to use which

| | Use level 1 | Use level 2 |
|---|---|---|
| The document is | user-supplied, or arrives at runtime | part of your project |
| Checked | at render | at build |
| Available in | any language | a host with types |

Most application views are level 2. A CMS rendering documents somebody uploaded is level 1 — and
level 1 still refuses missing values and dangerous links, which is more than most template
languages do.

---

That is the guide. From here: [Writing a document](../syntax.html) is the complete syntax,
[Styling the output](../styling.html) is the CSS, and [Building on BMX](../building-on.html) is
for people writing a framework on top.
{% endraw %}
