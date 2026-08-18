// Tokenise real documents with the real engine and assert the scopes.
//
// **A grammar is a program and an untested one is a guess.** A bad regex in a TextMate grammar does
// not fail — the rule silently never matches, so the file still loads, highlighting is quietly
// wrong, and nothing says so. That is the same shape as every other check on this project: the
// failure is invisible unless something asks.
//
// What matters most here is the third case. `meta.slot.expression.bmx` is the scope a host injects
// into, so it is a compatibility surface: if it stops appearing, every host's grammar stops
// working and their editors go quiet rather than erroring. It is asserted by name.
//
//   npm install vscode-textmate vscode-oniguruma
//   node editors/vscode/test/scopes.mjs
//
// Exits non-zero on the first failure.

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const oniguruma = require("vscode-oniguruma");
const textmate = require("vscode-textmate");

const wasmPath = require.resolve("vscode-oniguruma/release/onig.wasm");
await oniguruma.loadWASM(readFileSync(wasmPath));

const registry = new textmate.Registry({
  onigLib: Promise.resolve({
    createOnigScanner: (s) => new oniguruma.OnigScanner(s),
    createOnigString: (s) => new oniguruma.OnigString(s),
  }),
  loadGrammar: async () =>
    textmate.parseRawGrammar(
      readFileSync(join(here, "..", "syntaxes", "bmx.tmLanguage.json"), "utf8"),
      "bmx.tmLanguage.json",
    ),
});

const grammar = await registry.loadGrammar("text.bmx");

/** Every scope applied to the first character of `needle` on the given line. */
function scopesAt(document, lineIndex, needle) {
  const lines = document.split("\n");
  let stack = textmate.INITIAL;
  for (let i = 0; i <= lineIndex; i++) {
    const result = grammar.tokenizeLine(lines[i], stack);
    if (i === lineIndex) {
      const column = lines[i].indexOf(needle);
      if (column < 0) throw new Error(`"${needle}" is not on line ${i + 1}`);
      const token = result.tokens.find((t) => t.startIndex <= column && column < t.endIndex);
      return token ? token.scopes : [];
    }
    stack = result.ruleStack;
  }
  return [];
}

let failures = 0;
function check(name, document, line, needle, expected, absent) {
  let scopes;
  try {
    scopes = scopesAt(document, line, needle);
  } catch (e) {
    console.log(`  FAIL  ${name}\n        ${e.message}`);
    failures++;
    return;
  }
  const has = expected.every((s) => scopes.includes(s));
  const clean = !absent || !absent.some((s) => scopes.includes(s));
  if (has && clean) {
    console.log(`  ok    ${name}`);
  } else {
    console.log(`  FAIL  ${name}`);
    if (!has) console.log(`        wanted ${expected.join(" + ")}`);
    if (!clean) console.log(`        must NOT have ${absent.join(" or ")}`);
    console.log(`        got    ${scopes.join(" ")}`);
    failures++;
  }
}

// ---- structure ----
check("a heading is a heading", "# Receipt\n", 0, "Receipt", ["markup.heading.bmx"]);
check("a list marker", "- one\n", 0, "-", ["punctuation.definition.list.begin.bmx"]);
check("a quote", "> said\n", 0, ">", ["punctuation.definition.quote.bmx"]);

// ---- the injection points, which are a promise to hosts ----
check(
  "a slot's expression carries the host's scope",
  "Total: {{ order.total }}\n",
  0,
  "order.total",
  ["meta.slot.expression.bmx"],
);
check(
  "a block's name is a tag, its head is the host's",
  ":card: title=\"Pricing\" .featured #plans\n:!card:\n",
  0,
  "title=",
  ["meta.block.head.bmx"],
);
check("a block's name", ":card: x\n:!card:\n", 0, "card", ["entity.name.tag.block.bmx"]);
check(
  "a class in a head is BMX's business",
  ":card: .featured\n:!card:\n",
  0,
  "featured",
  ["entity.other.attribute-name.class.bmx"],
);
check(
  "an id in a head is BMX's business",
  ":card: #plans\n:!card:\n",
  0,
  "plans",
  ["entity.other.attribute-name.id.bmx"],
);
check(
  "an inline block's head is the host's, and is NOT a slot",
  "Press ::key[Ctrl+S]:: to save.\n",
  0,
  "Ctrl+S",
  ["meta.inline-block.head.bmx"],
  ["meta.slot.expression.bmx"],
);

// ---- the lie the grammar exists to avoid ----
check(
  "a slot inside a code fence is NOT a slot",
  "```\nTotal: {{ order.total }}\n```\n",
  1,
  "order.total",
  ["markup.raw.block.bmx"],
  ["meta.slot.expression.bmx"],
);
check(
  "a slot inside a code SPAN is not a slot either",
  "Write `{{ x }}` for a slot.\n",
  0,
  "{{ x }}",
  ["markup.inline.raw.bmx"],
  ["meta.slot.expression.bmx"],
);

// ---- a delimited head (0.9) ----
//
// **The head must keep `meta.block.head.bmx` in BOTH forms.** That scope is what every host's grammar
// injects into (see the compatibility note in the grammar itself), so a delimited head landing in some
// new scope would silently stop every framework colouring its own expressions — with nothing failing.
check(
  "a delimited head is still the host's head",
  ':button: -> [on:click=save(id)] Save :!button:\n', 0, "on:click=save(id)",
  ["meta.block.head.bmx"],
);
check(
  "the arrow is punctuation, not part of the head — and named so the site's table already covers it",
  ':button: -> [class=x] Save :!button:\n', 0, "->",
  ["punctuation.definition.head.arrow.bmx"],
);
check(
  "and the body after the bracket is content rather than head",
  ':button: -> [class=x] Save :!button:\n', 0, "Save",
  ["text.bmx"],
);

// ---- nesting by name ----
check(
  "a block inside a block",
  ":for: s in page.sections\n:card: t\n:!card:\n:!for:\n",
  1,
  "card",
  ["entity.name.tag.block.bmx"],
);
check(
  "and the outer block is still open on the inner line",
  ":for: s in page.sections\n:card: t\n:!card:\n:!for:\n",
  1,
  "card",
  ["meta.block.bmx"],
);

// ---- inline ----
check("strong", "a **bold** b\n", 0, "bold", ["markup.bold.bmx"]);
check("emphasis", "a *thin* b\n", 0, "thin", ["markup.italic.bmx"]);
check("a link target", "[click](/here)\n", 0, "/here", ["markup.underline.link.bmx"]);
check("an escape", "\\*not emphasis\\*\n", 0, "\\*", ["constant.character.escape.bmx"]);
check(
  "a slot inside strong still reaches the host",
  "**{{ total }}**\n",
  0,
  "total",
  ["meta.slot.expression.bmx"],
);

console.log();
if (failures) {
  console.log(`${failures} failed`);
  process.exit(1);
}
console.log("every scope is where the grammar says it is");
