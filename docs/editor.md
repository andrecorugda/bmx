---
layout: default
title: In your editor
description: "Colour, a live preview, and mistakes underlined as you type — for VS Code, Helix and Neovim."
---

{% raw %}
# In your editor

Three things, and you can have the first two in under a minute:

- **Colour** — headings, slots, blocks, everything
- **A live preview** beside the document, updating as you type
- **Mistakes underlined where they are**, with the reason

<figure class="shot">
  <img src="/assets/examples/editor.png" alt="A document on the left, the page the preview shows on the right">
  <figcaption>The document, and what the preview shows beside it. The right-hand panel is real
  output from the same renderer the preview uses — not a mock-up.</figcaption>
</figure>

## VS Code

{% endraw %}
<!-- **What the icon looks like where it is used.** Andre asked for this and star-burxt built the same
     figure on their page the same hour, so the two agree by coordination rather than by accident: three
     extensions in one tree, at 16px, from each repo's own copies of the three assets.

     **16px is the whole point.** VS Code gives an explorer row a 22px line and a 16px icon box, and the
     complaint that started this work was that an icon *"looks like it is really sticking to the edge making
     it no space on the file tree line"*. A figure at 48px cannot show that problem or its fix.

     **The icons are real, the rows are drawn**, and the caption says so — this site's `figure.shot` means a
     real screenshot of real output, and a hand-built tree is not one. What IS checkable is which file VS
     Code loads, so the caption names it. -->
<figure class="tree-shot">
  <div class="tree">
    <div class="row"><img src="{{ site.baseurl }}/assets/bx-file-icon-48.png" alt="" width="16" height="16"><span>main.bx</span></div>
    <div class="row is-open"><img src="{{ site.baseurl }}/assets/bmx-file-icon-128.png" alt="" width="16" height="16"><span>shop.bmx</span></div>
    <div class="row"><img src="{{ site.baseurl }}/assets/sbmx-file-icon-128.png" alt="" width="16" height="16"><span>Card.sbmx</span></div>
    <div class="row"><img src="{{ site.baseurl }}/assets/bmx-file-icon-128.png" alt="" width="16" height="16"><span>receipt.bmx</span></div>
  </div>
  <figcaption>
    A `.bmx` file in the explorer, beside its two siblings. The extension registers the icon itself —
    <code>contributes.languages[0].icon</code> points VS Code at <code>file-icon.png</code> for both
    themes — so this is the file your editor loads, at the 16px box a row gives it. The rows around the
    icons are drawn here; only the icons are the shipped assets.
  </figcaption>
</figure>
{% raw %}


Download `bmx.vsix` from the
[repository](https://github.com/andrecorugda/bmx/tree/main/editors/vscode) and install it:

```sh
code --install-extension bmx.vsix
```

Open any `.bmx` file. That is the whole setup — no compiler, no toolchain, nothing to configure.

### The preview

Press **`Ctrl+K V`** (`Cmd+K V` on a Mac), or click the preview icon in the editor's title bar.

The page appears beside your document and repaints as you type. It uses the same renderer a real page
uses, so what you see is what you get.

**Give it values for your slots** in your settings, and they appear in the preview:

```json
"bmx.preview.bindings": {
  "customer.name": "Ada Lovelace",
  "order.total": "£59.97"
}
```

Two things the preview will refuse, and both are the point rather than a limitation:

**A slot with no value shows the error, not a blank.** An empty space is how a page ships with a
missing total nobody notices, so the preview says which slot and where instead of quietly leaving a
gap.

**A `:name:` block is refused by name.** A block is a component, and what `card` looks like is decided
by whatever renders your page — the preview is not that, so it says so rather than guessing. To see
a page with components in it, render it with your framework.

### Mistakes as you type

A problem is underlined where it is, with the reason and a code:

```
BMX-E002   unterminated strong
BMX-W001   a heading jumps from level 1 to 3 within this document
```

Red for a **refusal** — the document will not render until you fix it. Yellow for a **warning** — it
renders fine and is probably still a mistake. [When it refuses](errors.html) lists every one with the
input that causes it.

## Helix

Colour comes from Helix's own grammar support; diagnostics come from the language server, which needs
[Node](https://nodejs.org) and nothing else. Add to `~/.config/helix/languages.toml`:

```toml
[language-server.bmx-lsp]
command = "node"
args = ["/path/to/bmx/editors/lsp/bmx-lsp.mjs"]

[[language]]
name = "bmx"
scope = "text.bmx"
file-types = ["bmx"]
language-servers = ["bmx-lsp"]
```

## Neovim

```sh
git clone https://github.com/andrecorugda/bmx ~/bmx
```

Then source
[`editors/nvim/bmx.lua`](https://github.com/andrecorugda/bmx/blob/main/editors/nvim/bmx.lua), or copy
it into your config. It sets the filetype and starts the language server, and needs no plugin manager.

## Any other editor

The language server speaks ordinary LSP over stdio:

```sh
node editors/lsp/bmx-lsp.mjs
```

It reports refusals and warnings, and **deliberately nothing else** — no completion, no hover, no
formatting. Each of those needs to know what a block *means*, and BMX does not: your framework
declares which blocks exist and what they do. So those belong to your framework's own server, which
publishes them alongside these rather than instead of them.

## Building a framework on BMX?

The pieces above are designed to be extended without patching anything.

Your grammar **injects** into three named scopes to colour your own language inside a slot or a
block's head, and your server publishes its own diagnostics beside BMX's. Both are described in
[Building on BMX](building-on.html), with a worked example.

{% endraw %}
