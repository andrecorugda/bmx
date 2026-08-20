// not-burxt: platform — the artefact under test, or its runtime, is JavaScript and nothing else can be
// What `language-configuration.json` promises the editor, asserted.
//
//     node editors/vscode/test/config.mjs
//
// **This file existed for four releases with nothing testing it, and then broke silently.** Its folding
// markers and its onEnter rule were keyed on `:{3,}` — 0.6's fence — so when 0.7 respelled the fence,
// folding a block stopped working and the *stay inside the block* rule stopped firing. No test noticed,
// because none existed; the grammar has `scopes.mjs`, the server has `protocol.mjs`, the preview has
// `preview.js`, and the file that decides how the editor BEHAVES had nothing.
//
// It was found by reading, prompted by the star-burxt session reporting the same shape on its side: a
// migration reported success over the files it looked at and said nothing about the ones it did not.
// Both our tools rewrite fenced code; neither looks at a JSON config, and grep for `:::` finds it only
// if you think to grep outside the documents.
//
// **The one-liner case is the interesting assertion.** `:span: class=box :!span:` matches an opener, so
// without the lookahead it would start a fold that never ends — a construct 0.7 added, meeting a config
// written before it existed.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const config = JSON.parse(readFileSync(join(here, "..", "language-configuration.json"), "utf8"));

let failures = 0;
function check(name, condition, detail) {
  if (condition) {
    console.log(`  ok    ${name}`);
  } else {
    failures++;
    console.log(`  FAIL  ${name}`);
    if (detail) console.log(`        ${detail}`);
  }
}

const start = new RegExp(config.folding.markers.start);
const end = new RegExp(config.folding.markers.end);
const stay = new RegExp(config.onEnterRules[0].beforeText);

console.log("folding");
check("an opener starts a fold", start.test(':card: title="x"'));
check("a closer ends one", end.test(":!card:"));
check("an indented opener still folds", start.test("  :for: task in tasks"));
check("an indented closer still ends", end.test("    :!for:"));
// A block that opens and closes on one line must not start a fold, or the editor folds to end of file.
check("a one-liner does NOT start a fold", !start.test(":span: class=box :!span:"));
check("a one-liner with a slot in its head does not either", !start.test(":span: child={{ x }} :!span:"));
// The superseded fence must not fold, or a 0.6 document looks like it still works in the editor while
// the parser refuses it — the split `BMX-E036` exists to prevent.
check("the 0.6 fence does not fold", !start.test("::: card"));
check("and its bare closer does not close", !end.test(":::"));
// A closer is a whole line. `:!card:` inside prose is text, and folding on it would end a block early.
check("a closer mid-sentence is not a closer", !end.test("as in :!card: above"));

console.log("\nstaying inside a block on Enter");
check("fires on an opener", stay.test(":card: title=\"x\""));
check("fires on an indented opener", stay.test("  :card:"));
check("does not fire on a closer", !stay.test(":!card:"));
check("does not fire on ordinary prose", !stay.test("a paragraph about :cards:"));

console.log("\nwhat the editor auto-closes");
const pairs = Object.fromEntries(config.autoClosingPairs.map((p) => [p.open, p.close]));
// A slot is the construct people type most, and `{{ x }}` wants the space the format trims anyway.
check("a slot closes itself", pairs["{{"] === " }}");
check("a link's brackets close", pairs["["] === "]");
// **Not `:`.** A colon opens a block only in a specific shape, and auto-closing every one would put a
// stray `:` into every English sentence containing a colon — the format's own syntax fighting prose.
check("a bare colon is NOT auto-closed", !("::" in pairs) && !(":" in pairs));

console.log(failures ? `\n${failures} failed` : "\nthe editor behaves the way the format reads");
process.exit(failures ? 1 : 0);
