// The site's highlighter and the editor's grammar must classify the same characters the same way.
//
// **This is the check that makes a claim true rather than hopeful.** `docs/assets/code.js` colours
// code blocks on the site; `syntaxes/bmx.tmLanguage.json` colours them in an editor. They are two
// programs, written on different days, and nothing but this file stops them drifting — at which
// point a reader learns one set of colours from the documentation and meets a different set the
// moment they open a file, which is worse than the site having no colour at all.
//
// It runs over **the documentation's own snippets**, not invented ones, because the divergence that
// matters is the one a reader can actually see. Every ```bmx fence on the site is a case.
//
// The first run found a real one: the grammar runs inline patterns inside a heading, so a slot in a
// heading is a slot — and the site highlighter was colouring the whole heading as prose, so
// `# Receipt {{ order.total }}` lost its slot.
//
//   npm install vscode-textmate vscode-oniguruma
//   node editors/vscode/test/agrees.mjs

import { readFileSync, readdirSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..", "..");
const oniguruma = require("vscode-oniguruma");
const textmate = require("vscode-textmate");

await oniguruma.loadWASM(readFileSync(require.resolve("vscode-oniguruma/release/onig.wasm")));
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

// ---- the map between the two vocabularies ------------------------------------------------------
//
// Listed most specific first. This table IS the correspondence — if a scope is not here, the grammar
// produces a classification the site has no opinion about, and that is reported rather than ignored.

const SCOPE_TO_CLASS = [
  ["meta.slot.expression.bmx", "slot"],
  ["meta.inline-block.head.bmx", "slot"],
  ["entity.other.attribute-name.class.bmx", "class"],
  ["entity.other.attribute-name.id.bmx", "id"],
  ["punctuation.definition.class.bmx", "class"],
  ["punctuation.definition.id.bmx", "id"],
  ["meta.block.head.bmx", "head"],
  ["entity.name.tag.block.bmx", "name"],
  ["entity.name.function.inline-block.bmx", "name"],
  ["punctuation.definition.block.begin.bmx", "fence"],
  ["punctuation.definition.block.end.bmx", "fence"],
  ["punctuation.section.embedded", "slot-mark"],
  ["punctuation.definition.inline-block.bmx", "slot-mark"],
  ["punctuation.definition.raw.bmx", "raw"],
  // **Before the `markup.*` entries, and that ordering is the whole of a real question.** A
  // heading's `#` carries BOTH `markup.heading.bmx` and `punctuation.definition.heading.bmx`, so
  // which class wins is a decision rather than a lookup. Punctuation wins because it is the more
  // specific of the two and because that is what every markdown theme does: the `#` is furniture
  // and the words are the heading.
  ["punctuation.definition", "punct"],
  ["constant.character.escape.bmx", "escape"],
  ["markup.inline.raw.bmx", "raw"],
  ["markup.raw.block.bmx", "raw"],
  ["fenced_code.block.language.bmx", "info"],
  ["entity.name.section.bmx", "heading"],
  ["markup.heading.bmx", "heading"],
  ["markup.bold.bmx", "strong"],
  ["markup.italic.bmx", "em"],
  ["markup.quote.bmx", "quote"],
  ["markup.underline.link.bmx", "link"],
  ["string.other.link.title.bmx", "link-text"],
];

/** The site class the grammar's scope stack corresponds to, or null for "no opinion". */
function classOf(scopes) {
  for (const [scope, cls] of SCOPE_TO_CLASS) {
    if (scopes.some((s) => s.startsWith(scope))) return cls;
  }
  return null;
}

/** Per-character class, from the grammar. */
function fromGrammar(source) {
  const marks = [];
  let stack = textmate.INITIAL;
  for (const line of source.split("\n")) {
    const result = grammar.tokenizeLine(line, stack);
    const row = new Array(line.length).fill(null);
    for (const token of result.tokens) {
      const cls = classOf(token.scopes);
      for (let i = token.startIndex; i < token.endIndex && i < line.length; i++) row[i] = cls;
    }
    marks.push(row);
    stack = result.ruleStack;
  }
  return marks;
}

/** Per-character class, from the site highlighter, by parsing the spans it emits. */
function fromSite(source, painted) {
  const marks = [];
  let row = [];
  let i = 0;
  const stack = [];
  while (i < painted.length) {
    if (painted.startsWith('<span class="t-', i)) {
      const close = painted.indexOf('">', i);
      stack.push(painted.slice(i + 15, close));
      i = close + 2;
      continue;
    }
    if (painted.startsWith("</span>", i)) { stack.pop(); i += 7; continue; }
    if (painted.startsWith("&amp;", i)) { row.push(stack.at(-1) ?? null); i += 5; continue; }
    if (painted.startsWith("&lt;", i)) { row.push(stack.at(-1) ?? null); i += 4; continue; }
    if (painted.startsWith("&gt;", i)) { row.push(stack.at(-1) ?? null); i += 4; continue; }
    if (painted[i] === "\n") { marks.push(row); row = []; i += 1; continue; }
    row.push(stack.at(-1) ?? null);
    i += 1;
  }
  marks.push(row);
  return marks;
}

// ---- load the site highlighter in a stub DOM ---------------------------------------------------

function paintWithSite(source) {
  const block = { lang: "bmx", dataset: {}, textContent: source, innerHTML: "" };
  const stub = {
    readyState: "complete",
    querySelectorAll: (sel) => (sel.includes("bmx") && !sel.includes("burxt") ? [block] : []),
    addEventListener: () => {},
  };
  const code = readFileSync(join(root, "docs", "assets", "code.js"), "utf8");
  new Function("document", code)(stub);
  return block.innerHTML;
}

// ---- every ```bmx fence in the documentation ---------------------------------------------------

function docs(dir, found = []) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) docs(path, found);
    else if (name.endsWith(".md")) found.push(path);
  }
  return found;
}

const snippets = [];
for (const path of docs(join(root, "docs"))) {
  const text = readFileSync(path, "utf8");
  // ```bmx … ``` — and NOT a ````bmx fence, whose content is a document showing a fence
  for (const m of text.matchAll(/^```bmx\n([\s\S]*?)^```$/gm)) {
    snippets.push({ path: path.slice(root.length + 1), body: m[1] });
  }
}

// **The landing page's panel is not a fence, and it was invisible to this check.**
//
// `tools/showcase.py` generates `docs/_includes/showcase.html` with a `<pre><code class="language-bmx">`
// in it, and `code.js` paints that on the live site exactly as it paints a fence. Collecting only `.md`
// files meant the one snippet on the FRONT PAGE was the one snippet nobody compared — a check that
// cannot see the newest thing it is meant to cover. Handled separately rather than by teaching `docs()`
// about `.html`, because a fence's body is literal and this one is escaped, and hiding that difference
// inside one collector is how the unescaping would eventually be applied to the wrong half.
const unescape = (s) => s
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">")
  .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  .replace(/&amp;/g, "&");                        // last, or `&amp;lt;` decodes twice

const includes = join(root, "docs", "_includes");
for (const name of statSync(includes).isDirectory() ? readdirSync(includes) : []) {
  if (!name.endsWith(".html")) continue;
  const text = readFileSync(join(includes, name), "utf8");
  for (const m of text.matchAll(/<code class="language-bmx">([\s\S]*?)<\/code>/g)) {
    snippets.push({ path: `docs/_includes/${name}`, body: unescape(m[1]) });
  }
}

// **Only documents that PARSE are compared, and skipping the rest is not a dodge.** BMX refuses an
// invalid document, so highlighting one is undefined for both tools — the grammar cannot report an
// error and colours `*important` as emphasis to end of line, while the site colours it as nothing.
// The guide deliberately contains broken documents, because teaching what a refusal looks like is
// half of what it is for. Comparing the colours of text that has no valid reading would force the
// two tools to agree about something neither defines.
const { execFileSync } = await import("node:child_process");
const { writeFileSync } = await import("node:fs");
const { tmpdir } = await import("node:os");
function parses(body) {
  const scratch = join(tmpdir(), "bmx-agrees.bmx");
  writeFileSync(scratch, body);
  try {
    execFileSync("node", [join(root, "reference", "bmx.js"), scratch], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

let failures = 0;
let compared = 0;
let skipped = 0;
for (const { path, body } of snippets) {
  if (!parses(body)) { skipped++; continue; }
  const want = fromGrammar(body);
  const got = fromSite(body, paintWithSite(body));
  const lines = body.split("\n");
  for (let r = 0; r < lines.length; r++) {
    for (let c = 0; c < lines[r].length; c++) {
      // **Whitespace is not compared, because a colour on a space cannot be seen.** The grammar
      // puts the gap after a heading's `#` inside `markup.heading`; the site leaves it bare. Forcing
      // them to agree about the colour of an invisible character would be work with no reader on the
      // other end of it.
      if (/\s/.test(lines[r][c])) continue;
      const a = want[r]?.[c] ?? null;
      const b = got[r]?.[c] ?? null;
      compared++;
      if (a !== b) {
        failures++;
        if (failures <= 8) {
          console.log(`  DIFFER ${path} line ${r + 1} col ${c + 1} ${JSON.stringify(lines[r][c])}`);
          console.log(`         grammar says ${a ?? "nothing"}, the site says ${b ?? "nothing"}`);
          console.log(`         ${lines[r]}`);
        }
        r = lines.length; // one report per snippet is enough to act on
        break;
      }
    }
  }
}

console.log();
console.log(`${snippets.length - skipped} documentation snippets compared, ${compared} characters`);
console.log(`${skipped} skipped as deliberately-invalid documents, where neither tool defines a colour`);

// **A ceiling on the skips, because this check once lost nineteen documents without failing.**
//
// Respelling the fence in 0.7 made every `:::` snippet in the docs stop parsing, and `parses()` sent
// them all to `skipped` — so the run still said *the two tools agree on every character*, about a set
// that had shrunk by 40%. The number below is the count of documents in the guide that are
// deliberately broken, because teaching what a refusal looks like is half of what the guide is for.
// If it rises, either somebody added a broken example or the format moved under the documentation, and
// both want a person to look.
const DELIBERATELY_BROKEN = 9;   // 6 in the guide, plus `BMX-E005`, `BMX-E037` and `BMX-E038` on the
                                 // errors page. It has risen three times in two days and each rise was a
                                 // new refusal being documented, which is the ceiling working: every one
                                 // made me confirm the docs had not simply fallen behind the format.
if (skipped > DELIBERATELY_BROKEN) {
  console.error(`\n${skipped} documents did not parse, and only ${DELIBERATELY_BROKEN} are meant to.`);
  console.error('Either a new broken example needs counting here, or the docs have fallen behind the format.');
  process.exit(1);
}
if (failures) {
  console.log(`${failures} disagreements — the site and the editor would show different colours`);
  process.exit(1);
}
console.log("the site highlighter and the editor grammar agree on every character");
