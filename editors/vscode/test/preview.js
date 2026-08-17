#!/usr/bin/env node
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
const assert = require('assert');

// ---- the smallest `vscode` extension.js actually uses ----
const commands = new Map();
const listeners = { change: [], switch: [] };
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

const vscode = {
  ViewColumn: { Beside: 2 },
  commands: { registerCommand: (id, fn) => { commands.set(id, fn); return { dispose() {} }; } },
  window: {
    get activeTextEditor() { return activeEditor; },
    showInformationMessage: (m) => { messaged = m; },
    createWebviewPanel: () => (created = panelStub()),
    onDidChangeActiveTextEditor: (cb) => { listeners.switch.push(cb); return { dispose() {} }; },
  },
  workspace: {
    getConfiguration: () => ({ get: (key) => config[key] }),
    onDidChangeTextDocument: (cb) => { listeners.change.push(cb); return { dispose() {} }; },
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
  activeEditor = { document: doc('::: card title="x"\nhi\n:::\n') };
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

  console.log();
  if (failures) { console.log(`${failures} failed`); process.exit(1); }
  console.log('the preview does what the button promises');
}

main();
