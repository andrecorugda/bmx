#!/usr/bin/env node
// not-burxt: platform — the artefact under test, or its runtime, is JavaScript and nothing else can be
// Drive extension.js against a stub `vscode`, because VS Code cannot be scripted here.
//
// **The failure modes of a preview all look fine on inspection**: a command registered under the
// wrong id, a panel that renders once and never again, an error path that shows a blank page instead
// of the reason. None of those is visible in a diff, and all of them are visible here.
//
// The last one matters most. A document that does not render has no page, and a preview that shows an
// empty panel has quietly done the thing BMX exists to refuse — printed nothing where something was
// missing. So there is a case for it.
//
//   node editors/vscode/test/preview.js
//
// Exits non-zero on the first failed expectation.

const Module = require('module');
const path = require('path');
const fs = require('fs');

// **Stage the renderer before loading the extension, every run.** `pack.py` copies
// `reference/bmx.js` to `reference/bmx.mjs` here at package time, and that copy is gitignored — so a
// checkout has none and a previous run leaves a STALE one. This test failed against exactly that: a
// copy from before `lint` existed, reporting `module.lint is not a function`. Two copies of a parser
// is how they drift, and re-staging is the cheap half of the fix.
const staged = path.join(__dirname, '..', 'reference');
fs.mkdirSync(staged, { recursive: true });
fs.copyFileSync(path.join(__dirname, '..', '..', '..', 'reference', 'bmx.js'),
                path.join(staged, 'bmx.mjs'));

// ---- the smallest `vscode` extension.js actually uses ----
const commands = new Map();
const listeners = { change: [], switch: [], open: [], close: [] };
let created = null;
let messaged = null;
let activeEditor = null;
let config = {};

const panelStub = () => ({
  title: '',
  webview: { html: '' },
  reveal() { this.revealed = (this.revealed || 0) + 1; },
  onDidDispose(cb) { this.dispose = cb; },
  dispose: null,
});

// A named collection is what lets this coexist with a framework's server, so the stub records the
// name it was created with and every set/delete — the behaviour, not just the calls.
const published = new Map();
let collectionName = null;

const vscode = {
  ViewColumn: { Beside: 2 },
  Range: class { constructor(start, end) { this.start = start; this.end = end } },
  Position: class { constructor(line, character) { this.line = line; this.character = character } },
  Diagnostic: class { constructor(range, message, severity) {
    this.range = range; this.message = message; this.severity = severity } },
  DiagnosticSeverity: { Error: 0, Warning: 1 },
  languages: {
    createDiagnosticCollection: (name) => {
      collectionName = name;
      return {
        set: (uri, list) => published.set(uri.toString(), list),
        delete: (uri) => published.delete(uri.toString()),
        dispose() {},
      };
    },
  },
  commands: { registerCommand: (id, fn) => { commands.set(id, fn); return { dispose() {} }; } },
  window: {
    get activeTextEditor() { return activeEditor; },
    showInformationMessage: (m) => { messaged = m; },
    createWebviewPanel: () => (created = panelStub()),
    onDidChangeActiveTextEditor: (cb) => { listeners.switch.push(cb); return { dispose() {} }; },
  },
  workspace: {
    textDocuments: [],
    getConfiguration: () => ({ get: (key) => config[key] }),
    onDidChangeTextDocument: (cb) => { listeners.change.push(cb); return { dispose() {} }; },
    onDidOpenTextDocument: (cb) => { listeners.open.push(cb); return { dispose() {} }; },
    onDidCloseTextDocument: (cb) => { listeners.close.push(cb); return { dispose() {} }; },
  },
};

const load = Module._load;
Module._load = function (request, ...rest) {
  if (request === 'vscode') return vscode;
  return load.call(this, request, ...rest);
};

const extension = require(path.join(__dirname, '..', 'extension.js'));

// ---- helpers ----
const doc = (text, name = 'page.bmx', languageId = 'bmx') => ({
  languageId,
  uri: { fsPath: `/tmp/${name}`, toString: () => `file:///tmp/${name}` },
  getText: () => text,
});

let failures = 0;
function check(name, condition, detail) {
  if (condition) console.log(`  ok    ${name}`);
  else { console.log(`  FAIL  ${name}${detail ? `\n        ${detail}` : ''}`); failures++; }
}

async function main() {
  extension.activate({ subscriptions: [] });

  check('the command is registered under the id package.json declares',
    commands.has('bmx.preview'), [...commands.keys()].join(', '));
  check('it listens for edits', listeners.change.length === 1);
  check('it follows the active editor', listeners.switch.length === 1);

  // ---- with no .bmx open, it says so rather than opening an empty panel ----
  activeEditor = { document: doc('x', 'notes.txt', 'plaintext') };
  await commands.get('bmx.preview')();
  check('a non-BMX file is told, not previewed', created === null && messaged !== null, messaged);

  // ---- a real document ----
  activeEditor = { document: doc('# Receipt\n\n- one\n- two\n\nSome **bold** text.\n') };
  await commands.get('bmx.preview')();
  check('a panel opens', created !== null);
  const html = created ? created.webview.html : '';
  check('it renders the document', html.includes('<h1>Receipt</h1>') && html.includes('<li>one</li>'),
    html.slice(0, 160));
  check('the panel is titled with the file', (created?.title || '').includes('page.bmx'), created?.title);
  check('scripts are not enabled in the webview', !html.includes('<script'));

  // ---- a slot with no binding: the refusal IS the preview ----
  activeEditor = { document: doc('Total: {{ order.total }}\n') };
  await commands.get('bmx.preview')();
  const unbound = created.webview.html;
  check('an unbound slot shows the refusal rather than a blank',
    unbound.includes('BMX-R002') && unbound.includes('bmx-note'), unbound.slice(0, 200));
  check('and it does NOT render a page for it', !unbound.includes('<p>Total:'), unbound.slice(0, 200));

  // ---- the same slot, bound by the setting ----
  config['preview.bindings'] = { 'order.total': '£59.97' };
  await commands.get('bmx.preview')();
  check('a bound slot renders, escaped', created.webview.html.includes('£59.97'));
  config = {};

  // ---- a block: refused by name, because a preview is not a host ----
  activeEditor = { document: doc(':card: title="x"\nhi\n:!card:\n') };
  await commands.get('bmx.preview')();
  check('a block is refused by name, per SPEC 4a.5',
    created.webview.html.includes('BMX-R003') && created.webview.html.includes('card'),
    created.webview.html.slice(0, 200));

  // ---- live: an edit repaints without the command being run again ----
  const live = doc('# First\n');
  activeEditor = { document: live };
  await commands.get('bmx.preview')();
  const edited = doc('# Second\n');
  await listeners.change[0]({ document: edited });
  check('an edit repaints the panel', created.webview.html.includes('<h1>Second</h1>'),
    created.webview.html.slice(0, 160));

  // ---- a second call reuses the panel rather than stacking them ----
  const before = created;
  await commands.get('bmx.preview')();
  check('a second invocation reveals the same panel', created === before && before.revealed >= 1);

  // ---- diagnostics, which is the half a framework must be able to coexist with ----
  check('the diagnostic collection is NAMED, so a host\'s server can publish too',
    collectionName === 'bmx', String(collectionName));

  const broken = doc('Your balance is **£240.00\n', 'broken.bmx');
  await listeners.open[0](broken);
  const one = published.get(broken.uri.toString()) || [];
  check('a broken document gets one error', one.length === 1 && one[0].severity === 0,
    JSON.stringify(one.map((d) => [d.code, d.severity])));
  check('the squiggle covers the rest of the line, not one character',
    one[0] && one[0].range.end.character > one[0].range.start.character + 1,
    JSON.stringify(one[0]?.range));

  const linty = doc('# One\n\n### Three\n', 'lint.bmx');
  await listeners.open[0](linty);
  const warns = published.get(linty.uri.toString()) || [];
  check('a document that parses gets warnings at Warning severity',
    warns.length === 1 && warns[0].code === 'BMX-W001' && warns[0].severity === 1,
    JSON.stringify(warns.map((d) => [d.code, d.severity])));

  listeners.close[0](linty);
  check('closing clears them, so a problem cannot outlive its file',
    !published.has(linty.uri.toString()));

  const fine = doc('# Fine\n', 'fine.bmx');
  await listeners.open[0](fine);
  check('a clean document publishes an empty list', (published.get(fine.uri.toString()) || []).length === 0);

  console.log();
  if (failures) { console.log(`${failures} failed`); process.exit(1); }
  console.log('the preview does what the button promises');
}

main();
