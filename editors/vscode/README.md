# BMX for VS Code

Highlighting for `.bmx` documents — **markdown with one unambiguous reading and a typed hole in
it**.

```bmx
# Receipt {{ order.reference }}

Thank you, **{{ customer.name }}**. Your total is {{ order.total }}.

::: for line in order.lines
- {{ line.sku }} × {{ to_string(line.qty) }}
:::
```

## What it colours

Markdown structure — headings, lists, quotes, code, emphasis, links, escapes — plus the two things
BMX adds: the `:::` block and the `{{ … }}` slot.

**It deliberately does not colour what is inside a slot or a block's head.** BMX captures those
opaquely and hands them to whatever renders the document, so an editor that coloured them would be
claiming to know what `on:click=save(line.id)` means when the format does not.

That is not a gap; it is an extension point. A framework built on BMX adds a grammar that injects
into three named scopes and colours its own language there:

    meta.slot.expression.bmx        between {{ and }}
    meta.block.head.bmx             everything after a block's name
    meta.inline-block.head.bmx      between [ and ] of an inline block

A host whose slot language is [Burxt](https://burxt-lang.org) gets full expression highlighting by
including `source.burxt` — one line, no reimplementation. See
[`editors/README.md`](https://github.com/andrecorugda/bmx/blob/main/editors/README.md) for a worked
example.

## Installing

```sh
code --install-extension bmx-0.1.0.vsix
```

Or build it from a checkout — no toolchain, no npm:

```sh
python3 editors/vscode/pack.py
```

## Diagnostics

**This extension is highlighting only, and that is a decision rather than a stage.** Most editors let
one language server own a file, so a BMX server and a framework's server would compete for `.bmx`.
BMX gives a host the structural checks as ordinary functions — `bmx_check` answers a code, a message,
and a line and character column — and the host ships one server reporting both halves.

## Links

- [bmx.burxt-lang.org](https://bmx.burxt-lang.org) — the guide, the syntax, every error
- [The format](https://github.com/andrecorugda/bmx) — spec, conformance suite, two implementations

MIT OR Apache-2.0.
