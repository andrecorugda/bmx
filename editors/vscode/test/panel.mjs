// What the code panels on the site must be true of: a number for every line, and a document you can copy.
//
//     node editors/vscode/test/panel.mjs
//     node editors/vscode/test/panel.mjs --prove-it     # the negative control
//
// **Every assertion here is one star-burxt had to measure.** They built the gutter first and sent the
// technique with the parts that only showed up under measurement:
//
//   - a wrapper called at each of the painter's exits wrapped ONE of three, so the numbers stopped
//     partway down the panel. **A gutter with unnumbered lines in it is worse than no gutter**, because
//     the numbers above the gap stop meaning anything.
//   - a blank line's box reports `height: 0`, printing its number on top of the next one's.
//   - and an EMPTY inline-block baselines from its bottom edge, so fixing the height made that row 27px
//     against everyone else's 21. Neither is visible in a screenshot; both are visible in the GAPS.
//
// **This file used to check a depth class per line, for indent guides that lived one day.** Andre removed
// them after looking at them — correct code in the wrong setting — and the three depth checks went with
// the feature rather than staying to certify machinery no page renders. A test kept past its subject is
// how a repository grows a floor under something nobody wants.
//
// The height and baseline are CSS and asserted in the browser rather than here. What this file holds is
// the structure: one box per line, and **the document survives being painted** — because `inline-block`
// with the newline outside the box is what keeps a panel from being a trap for anyone who copies from it.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = join(here, "..", "..", "..");
const prove = process.argv.includes("--prove-it");

let source = readFileSync(join(ROOT, "docs", "assets", "code.js"), "utf8");
if (prove) {
  // The control: a painter that drops the last line. Star's defect in its purest form — the panel still
  // looks like a panel, and every number in it is still correct, and one line is simply gone.
  //
  // **This patch had to be repointed when the depth pass was deleted, and it announced that itself.** The
  // old target was the opening line of a multi-line `map`; the body is one line now, `.replace` matched
  // nothing, and the run said `THE CONTROL DID NOT FAIL`. Which is the whole reason a control is a
  // separate mode rather than a comment: **a negative control that silently stops matching is a test
  // suite quietly losing a check**, and this one is anchored on the shortest fragment that still names
  // the operation rather than on the shape of the surrounding code.
  const target = "painted.split('\\n').map(";
  if (!source.includes(target)) {
    console.log(`the control cannot find \`${target}\` in code.js, so it is patching nothing`);
    process.exit(1);
  }
  source = source.replace(target, "painted.split('\\n').slice(0, -1).map(");
}

let failures = 0;
function check(name, condition, detail) {
  if (condition) {
    console.log(`  ok    ${name}`);
  } else {
    failures++;
    console.log(`  FAIL  ${name}`);
    if (detail !== undefined) console.log(`        ${detail}`);
  }
}

/** Run the site painter over one document, the way a browser does. */
function paint(language, text) {
  const block = { className: `language-${language}`, dataset: {}, textContent: text, innerHTML: "" };
  const stub = {
    querySelectorAll: (s) => (s.includes(language) ? [block] : []),
    readyState: "complete",
    addEventListener: () => {},
  };
  new Function("document", source)(stub);
  return block.innerHTML;
}

const strip = (html) => html
  .replace(/<[^>]*>/g, "")
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"')
  .replace(/&#39;/g, "'").replace(/&amp;/g, "&");

// The hardest input for the boxing: nesting, a blank line inside it, a one-liner, and a line back at the
// left margin. It was chosen for the guides and kept for the blank line, which is still the row where a
// per-line wrapper goes wrong — an empty string between two newlines is easy to drop and easy to merge.
const BMX = `:section: class=card
  # Today
  :for: task in model.tasks
    :button: -> [on:click=Msg.Toggle(id)] Save :!button:

    {{ task.label }}
  :!for:
:!section:`;

const BURXT = `pure function receipt_view(order: Order) -> Html {
    let mutable kids: [Html] = [];
    for line in order.lines {
        let p: Int = push(kids, html_text(line.sku));
    }
    return html_element("article", [], kids);
}`;

for (const [language, doc] of [["bmx", BMX], ["burxt", BURXT]]) {
  console.log(language);
  const painted = paint(language, doc);
  const boxes = painted.split("\n");
  const lines = doc.split("\n");

  // **The one that would have caught star's defect**, and the reason it is first.
  check(`every line gets a box (${lines.length})`, boxes.length === lines.length,
        `${lines.length} lines painted into ${boxes.length} boxes`);
  check("every box is a box", boxes.every((b) => b.startsWith('<span class="cl')), boxes.find((b) => !b.startsWith('<span class="cl')));

  // **The clipboard is the document.** If this fails, the panel is a trap: it looks right and what a
  // reader pastes is not what they read.
  check("stripping the markup returns the document exactly", strip(painted) === doc,
        JSON.stringify(strip(painted).slice(0, 60)));

  // The newline must sit BETWEEN two boxes, not inside one — that is what `inline-block` buys.
  check("the newline is outside the box", !painted.includes("\n</span>"));
}

console.log();
if (prove) {
  if (failures) {
    console.log("the control failed as it must — a painter that drops a line is caught");
    process.exit(0);
  }
  console.log("THE CONTROL DID NOT FAIL, so this file cannot see a missing line");
  process.exit(1);
}
console.log(failures ? `${failures} failed` : "every line is numbered and the document survives painting");
process.exit(failures ? 1 : 0);
