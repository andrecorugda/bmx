# Editor support for BMX — and how a host builds on it

BMX ships highlighting for `.bmx` documents and the parts of a language server that are the
format's. **What it deliberately does not ship is anything that depends on knowing what an
expression means**, because BMX does not know — [`BOUNDARY.md`](../BOUNDARY.md) is that rule, and
this directory is that rule applied to tooling.

So there are two audiences here. If you write documents, install the extension. If you build a
framework on BMX — [star-burxt](https://star.burxt-lang.org) is the first — the rest of this file is
the interface you extend, and it is designed so you never patch a file in this repository.

    editors/vscode/          the extension: grammar, language configuration, packaging
    editors/vscode/test/     tokenises real documents and asserts the scopes
    editors/helix/           Helix language configuration
    editors/nvim/            Neovim filetype + tree-sitter-free highlighting hook

## What BMX highlights, and what it refuses to

BMX colours **structure**: fences, block names, slot delimiters, headings, lists, quotes, emphasis,
links, escapes, and the two things a head genuinely belongs to the format — `.class` and `#id`.

It leaves three things uncoloured **on purpose**, and gives each one a stable scope name:

| Scope | What is in it |
|---|---|
| `meta.slot.expression.bmx` | the text between `{{` and `}}` |
| `meta.block.head.bmx` | everything after a block's name |
| `meta.inline-block.head.bmx` | the text between `[` and `]` of an inline block |

**Those three names are a compatibility surface, not an implementation detail.** Renaming one breaks
every host's grammar, so it is a major change under [`VERSIONING.md`](../VERSIONING.md) — the same
rule that governs renaming an AST field. They are asserted by name in
`editors/vscode/test/scopes.mjs`, so they cannot be renamed quietly.

## Extending the highlighting: injection

A host adds a grammar that **injects** into those scopes. Nothing in this repository changes.

`package.json`, in your extension:

```json
{
  "contributes": {
    "grammars": [
      {
        "scopeName": "source.star.injection",
        "path": "./syntaxes/star-injection.json",
        "injectTo": ["text.bmx"]
      }
    ]
  }
}
```

`syntaxes/star-injection.json` — colour your own expression language inside a slot, and your own
attributes inside a head:

```json
{
  "scopeName": "source.star.injection",
  "injectionSelector": "L:meta.slot.expression.bmx, L:meta.block.head.bmx",
  "patterns": [
    {
      "match": "\\b(on:[a-z]+)(=)",
      "captures": {
        "1": { "name": "entity.other.attribute-name.event.star" },
        "2": { "name": "punctuation.separator.star" }
      }
    },
    { "include": "source.burxt" }
  ]
}
```

That last line is the useful one: **`source.burxt` already exists**, so a host whose slot language is
Burxt gets full expression highlighting inside `{{ … }}` by including it rather than reimplementing
it. `L:` means the injection is tried *before* the base grammar's own rules at that scope.

Two documents' worth of the same idea: a slot's contents are the host's language, so the host's
grammar colours them. BMX only had to name the place.

## Extending the diagnostics

**The reusable half is in the library, not in a server**, and that is deliberate. Most editors let
one language server own a file, so if BMX shipped a server and star shipped a server they would
fight over `.bmx`. Instead BMX gives you the structural half as ordinary functions and **you ship one
server that reports both.**

```burxt
use "bmx/burxt/bmx.bx";

match bmx_check(source) {
    Some(d) => { /* d.code, d.message, d.offset, d.line, d.column */ }
    None    => { /* the document is structurally sound — now apply YOUR rules */ }
}
```

`BmxDiagnostic` carries `code`, `message`, `offset`, `line` and `column`.

**`column` counts characters, not bytes**, and that is the part worth not reimplementing: a byte
column is right on every ASCII line and puts the caret in the wrong place on the first line
containing an accent — and whoever writes it will test with ASCII. `bmx_where(source, offset)`
exposes the same conversion on its own if you need it for your own offsets.

`line` and `column` are **one-based**, matching what an editor displays and what `burxt` itself
prints. **The LSP protocol is zero-based**, so subtract one when you build a `Position`.

**One diagnostic, not a list**, and that is [`SPEC.md`](../SPEC.md) §6 rather than laziness: BMX has
no error recovery, so there is no second structural error to report. A host that wants a list wants
recovery, and §7 names the trigger for adding it.

## Running the tests

```sh
npm install vscode-textmate vscode-oniguruma
node editors/vscode/test/scopes.mjs
```

**A broken regex in a TextMate grammar does not fail** — the rule silently never matches, the file
still loads, and highlighting is quietly wrong. So the grammar is tokenised with the real engine and
the scopes are asserted, including the two cases that would be lies: a `{{ … }}` inside a code fence
or a code span is *not* a slot, because §5 says its content is never parsed.

Both of those assertions were checked by deliberately breaking the grammar and confirming they fail.

## Installing

VS Code, from a checkout:

```sh
ln -s "$PWD/editors/vscode" ~/.vscode/extensions/bmx
```

Helix and Neovim configurations are in their directories, each a few lines.

## What is not here yet

**No language server binary.** The library half above is what a host needs, and BMX shipping its own
server would be the thing this page argues against — two servers, one file. If it turns out that
every host writes the same fifty lines of framing, that is the trigger to ship a reference server,
and it will be reported as such rather than assumed.

**No formatter.** A formatter has to decide what a head means to reflow it, which is the host's.

**No completion or hover for block names.** BMX does not know which blocks exist — a host declares
them. That is a host's server with a host's list, and the scopes above are how it knows where it is.
