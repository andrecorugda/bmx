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
  source = source.replace("return painted.split('\\n').map((html) => {",
                          "return painted.split('\\n').slice(0, -1).map((html) => {");
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

// A document with the things that broke it for star: nesting, a blank line inside the nesting, a
// one-liner, and a line at depth zero after all of it.
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

console.log("depth");
const painted = paint("bmx", BMX);
const classes = painted.split("\n").map((b) => (b.match(/class="cl([^"]*)"/) || [, ""])[1].trim());
check("depth follows the indent", classes.slice(0, 4).join(",") === ",w1,w1,w2", classes.join("|"));
// **A blank line carries the level above it**, or the guide column breaks wherever a document breathes.
check("a blank line carries the depth above it", classes[4] === "w2", classes.join("|"));
check("and the level comes back down at the end", classes.at(-1) === "", classes.join("|"));

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
