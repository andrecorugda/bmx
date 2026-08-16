---
layout: default
title: Styling the output
---

{% raw %}
# Styling the output

BMX emits **plain semantic HTML with one hook**. There are no utility classes, no wrapper divs,
no generated identifiers — so any CSS you already have works, and Tailwind, SCSS or a stylesheet
you wrote by hand all attach the same way.

## What you get

Every document renders inside one element:

```html
<article class="bmx"> … </article>
```

That is the only class BMX adds. Everything inside is the tag the construct means:

| You write | You get |
|---|---|
| `# Heading` | `<h1>` … `<h6>` |
| a paragraph | `<p>` |
| `- item` | `<ul><li>` |
| `1. item` | `<ol><li>` |
| `> quoted` | `<blockquote>` |
| ` ```burxt ` | `<pre><code class="language-burxt">` |
| `*emphasis*` | `<em>` |
| `**strong**` | `<strong>` |
| `` `code` `` | `<code>` |
| `[text](target)` | `<a href="target">` |
| `{{ slot }}` | the escaped value, as text |

**A slot produces no element.** Its value lands as text wherever the slot was, so a slot inside a
heading is part of the heading and inherits its styling. There is no `<span class="slot">` to
target, deliberately — a hook there would make styling depend on where a value came from rather
than on what it is.

## Plain CSS

Descendant selectors on the one class:

```css
.bmx h1        { font-size: 2rem; line-height: 1.2; }
.bmx p         { margin-block: 1em; }
.bmx blockquote{ border-inline-start: 3px solid #ddd; padding-inline-start: 1em; }
.bmx pre       { overflow-x: auto; }
.bmx a         { text-decoration-thickness: .08em; }
```

Because the markup is semantic, a **classless stylesheet** works with no configuration at all —
point one at `.bmx` and a document is styled.

## Tailwind

Tailwind styles elements by class, and BMX emits none — which is exactly what
`@tailwindcss/typography` is for:

```html
<article class="bmx prose prose-slate dark:prose-invert max-w-none"> … </article>
```

Two ways to get that second class onto the element:

- **Wrap it.** Put the rendered document inside a `<div class="prose">`. Nothing to configure.
- **Style `.bmx` directly**, so the document needs no extra class:

  ```css
  @import "tailwindcss";
  .bmx { @apply prose prose-slate dark:prose-invert max-w-none; }
  ```

**One integration note**: Tailwind's JIT finds class names by scanning your source files. It has
no reason to look at `.bmx` files, and if you ever put a utility class in a slot value it will not
find it. Either add the glob:

```js
content: ["./src/**/*.{html,js}", "./views/**/*.bmx"],
```

…or, better, keep utility classes out of documents entirely. A document that carries styling is a
document you cannot restyle.

## SCSS

Nesting maps onto the structure directly:

```scss
.bmx {
  h1, h2, h3 { font-weight: 650; }
  p + p      { margin-block-start: 1em; }
  pre        { background: $code-bg; }
  code       { font-family: $mono; }

  // code inside a paragraph, not inside a block
  p code     { padding: .15em .35em; border-radius: 3px; }
}
```

## Syntax highlighting

A fenced block's info string becomes `class="language-<info>"`, which is the convention Prism,
highlight.js and Shiki all read. Nothing else is needed:

````bmx
```burxt
let price: Decimal<2> = 19.99;
```
````

→ `<pre><code class="language-burxt">let price: Decimal&lt;2&gt; = 19.99;\n</code></pre>`

Note the escaping: the `<` in `Decimal<2>` is `&lt;` in the output, as it must be. **Highlighters
read the text content, so this is correct rather than a problem** — but if you write your own
highlighting pass, read `textContent` and not `innerHTML`.

The info string is checked as a name before it becomes a class, so a document cannot inject an
attribute through it.

## What you cannot style, and why

**There is no way to put a class on a paragraph from inside a document.** No attribute syntax, no
`{: .class}` blocks. That is a real limitation and it is deliberate: the moment a document can
carry presentation, documents stop being restylable and every one of them has to be revisited
when the design changes.

If a particular block genuinely needs different treatment, it is a different **view** — and in a
host at level 2 a view is a function, so composing two of them is ordinary code rather than a
templating feature.
{% endraw %}
