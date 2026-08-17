# BMX for VS Code

Highlighting and a live preview for `.bmx` documents — **markdown with one unambiguous reading and a
typed hole in it**.

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

## Preview

**Open Preview to the Side** — the button in the editor title bar, `Ctrl+K V` (`Cmd+K V` on a Mac),
or the command palette. It renders the document beside itself and repaints as you type.

It renders with the reference implementation bundled in this extension, so **it needs nothing
installed** — no compiler, no toolchain. The trade is stated rather than hidden: that implementation
is level 1, so it substitutes slot values and does not check them.

Give it values to substitute in your settings:

```json
"bmx.preview.bindings": {
  "customer.name": "Ada Lovelace",
  "order.total": "£59.97"
}
```

**A slot with no binding is an error in the preview, not a blank.** The empty string is how a page
ships with a missing total nobody sees, so the panel shows the refusal instead of a page — which is
the same thing a real render does.

And a `:::` block is refused by name. A block is a component, the host decides what `card` renders,
and a preview is not a host. That is the format's rule rather than a limit of the button, so the
message says which block and why.

## Diagnostics

**This extension ships no language server, and that is a decision rather than a stage.** Most editors
let one server own a file, so a BMX server and a framework's server would compete for `.bmx`. BMX
gives a host the structural checks as ordinary functions — `bmx_check` answers a code, a message, and
a line and character column — and the host ships one server reporting both halves.

The preview above is not a server: it renders on demand in the extension, so it costs a host nothing
and cannot conflict with one.

## Links

- [bmx.burxt-lang.org](https://bmx.burxt-lang.org) — the guide, the syntax, every error
- [The format](https://github.com/andrecorugda/bmx) — spec, conformance suite, two implementations

MIT OR Apache-2.0.
