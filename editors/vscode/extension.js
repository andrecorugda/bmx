// The BMX preview: a `.bmx` document, rendered, beside the document.
//
// **It renders with the reference implementation rather than shelling out to a compiler**, and that
// is the whole design. Burxt's extension spawns `burxt` because it needs a type checker; a preview
// needs a renderer, BMX has one in JavaScript, and requiring a toolchain to look at a document would
// make the preview unavailable to exactly the people a preview is for.
//
// So this works with nothing installed. The trade is stated rather than hidden: the reference
// implementation is **level 1**, so it substitutes slot values and it does not check them. A slot
// with no binding is an error here, the same as it is on a real page — it is not silently blank,
// because a blank is how a page ships with a missing total nobody sees.
//
// What it deliberately cannot do is render a `:::` block. A block is a component, the host decides
// what `card` means, and this preview is not a host — so it refuses by name and says why, which is
// SPEC §4a.5 rather than a limitation of the button.

const vscode = require('vscode');
const path = require('path');

/** Problems for `.bmx` files. A NAMED collection, which is why this cannot conflict with a host's. */
let problems = null;

/** The panel, if one is open. One preview, retargeted — not one per document. */
let panel = null;
let showing = null; // the uri the panel is currently rendering

/** Slot values the preview substitutes, so a document with slots shows something. */
function bindings() {
  const configured = vscode.workspace.getConfiguration('bmx').get('preview.bindings');
  return configured && typeof configured === 'object' ? configured : {};
}

function page(html, title, note) {
  // A style sheet close enough to bmx.burxt-lang.org to be recognisable, and using VS Code's own
  // theme variables so the preview follows the editor rather than fighting it.
  return `<!doctype html>
<html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
<style>
  body { font: 15px/1.65 var(--vscode-font-family, system-ui); color: var(--vscode-foreground);
         background: var(--vscode-editor-background); padding: 1.5rem 2rem; max-width: 46rem; }
  h1, h2, h3, h4, h5, h6 { line-height: 1.25; margin: 1.6em 0 .5em; }
  h1 { font-size: 1.7rem; } h2 { font-size: 1.35rem; }
  pre { background: var(--vscode-textCodeBlock-background, rgba(127,127,127,.1));
        padding: .8rem 1rem; border-radius: 6px; overflow-x: auto; }
  code { font-family: var(--vscode-editor-font-family, monospace); font-size: .92em; }
  pre code { font-size: .88rem; }
  blockquote { margin: 1em 0; padding-left: 1rem;
               border-left: 3px solid var(--vscode-textBlockQuote-border, #888); opacity: .9; }
  a { color: var(--vscode-textLink-foreground); }
  .bmx-note { margin: 0 0 1.2rem; padding: .7rem .9rem; border-radius: 6px; font-size: .86rem;
              background: var(--vscode-inputValidation-errorBackground, rgba(200,16,46,.12));
              border: 1px solid var(--vscode-inputValidation-errorBorder, #c8102e);
              font-family: var(--vscode-editor-font-family, monospace); white-space: pre-wrap; }
  .bmx-title { font-size: .78rem; opacity: .6; margin: 0 0 1.2rem; letter-spacing: .04em;
               text-transform: uppercase; }
</style></head>
<body>
<p class="bmx-title">${title}</p>
${note ? `<p class="bmx-note">${note}</p>` : ''}
${html}
</body></html>`;
}

function escapeHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** The reference implementation, imported once and cached by the loader. */
async function bmx() {
  return import(require('url').pathToFileURL(path.join(__dirname, 'reference', 'bmx.mjs')).href);
}

// ---- diagnostics ------------------------------------------------------------------------------
//
// **Computed here rather than through a language server, and that is not a shortcut.** The server in
// `editors/lsp/` exists for editors that need one — helix, nvim — and speaking LSP to ourselves
// inside VS Code would mean a second process, a client dependency, and framing to get wrong, for
// diagnostics we can publish directly. Both paths call the same `parse` and `lint`, so they cannot
// disagree about a document.
//
// A NAMED `DiagnosticCollection` is what makes this safe beside a framework's own server: VS Code
// merges collections rather than letting one own a file. That fact is why this extension has
// diagnostics at all — an earlier version of `editors/README.md` argued the opposite and was wrong.

async function check(document) {
  if (!problems || !document || document.languageId !== 'bmx') return;
  const module = await bmx();
  const text = document.getText();
  const found = [];

  const range = (line, column, length) => new vscode.Range(
    // `at` answers one-based, because that is what a human reads. VS Code is zero-based.
    new vscode.Position(line - 1, column - 1),
    new vscode.Position(line - 1, column - 1 + length),
  );

  try {
    module.parse(text);
  } catch (e) {
    if (!(e instanceof module.BmxError)) throw e;
    const { line, column } = module.at(text, e.offset);
    const lines = text.split('\n');
    // The rest of the line, not one character: an unterminated `**` is reported where it opened and
    // the problem is everything after it, so a one-byte squiggle points at the wrong thing.
    const length = Math.max(1, (lines[line - 1] || '').length - (column - 1));
    const d = new vscode.Diagnostic(range(line, column, length),
      e.message.replace(/^\S+ at \d+: /, ''), vscode.DiagnosticSeverity.Error);
    d.code = e.code;
    d.source = 'bmx';
    found.push(d);
    // A document with no tree has nothing to lint, and style notes beside a refusal bury it.
    problems.set(document.uri, found);
    return;
  }

  for (const w of module.lint(text)) {
    const d = new vscode.Diagnostic(range(w.line, w.column, 1), w.message,
      vscode.DiagnosticSeverity.Warning);
    d.code = w.code;
    d.source = 'bmx';
    found.push(d);
  }
  problems.set(document.uri, found);
}

async function render(document) {
  // The reference implementation is an ES module; `require` cannot load one, so it is imported.
  // Cached by the loader after the first call, so this is not a per-keystroke cost. `.mjs` because
  // this extension is CommonJS, and a `.js` ES module inside it makes Node reparse and warn.
  const module = await bmx();
  const title = path.basename(document.uri.fsPath);
  try {
    return page(module.render(document.getText(), bindings()), title, null);
  } catch (e) {
    // **The refusal IS the preview.** A document that does not render has no page, and showing a
    // half-built one would be the thing BMX exists to refuse. So the panel shows the reason.
    return page('', title, escapeHtml(e && e.message ? e.message : String(e)));
  }
}

async function paint(document) {
  if (!panel || !document || document.languageId !== 'bmx') return;
  showing = document.uri.toString();
  panel.title = `Preview ${path.basename(document.uri.fsPath)}`;
  panel.webview.html = await render(document);
}

function activate(context) {
  problems = vscode.languages.createDiagnosticCollection('bmx');
  context.subscriptions.push(problems);

  // Everything already open, then everything opened later.
  vscode.workspace.textDocuments.forEach(check);
  const onOpen = vscode.workspace.onDidOpenTextDocument(check);
  // Cleared on close, or a problem outlives the file and cannot be found or dismissed.
  const onClose = vscode.workspace.onDidCloseTextDocument((d) => problems.delete(d.uri));

  const open = vscode.commands.registerCommand('bmx.preview', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'bmx') {
      vscode.window.showInformationMessage('Open a .bmx document to preview it.');
      return;
    }
    if (panel) {
      panel.reveal(vscode.ViewColumn.Beside, true);
    } else {
      panel = vscode.window.createWebviewPanel(
        'bmx.preview', 'BMX preview', { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true },
        { enableScripts: false, retainContextWhenHidden: true },
      );
      panel.onDidDispose(() => { panel = null; showing = null; }, null, context.subscriptions);
    }
    await paint(editor.document);
  });

  // Live, because a preview you have to refresh is a build step with a nicer name.
  const onChange = vscode.workspace.onDidChangeTextDocument((e) => {
    const painted = panel && e.document.uri.toString() === showing ? paint(e.document) : null;
    return Promise.all([painted, check(e.document)]);
  });

  // Follow the active editor, so opening a second document does not leave the panel lying.
  const onSwitch = vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (panel && editor && editor.document.languageId === 'bmx') return paint(editor.document);
  });

  context.subscriptions.push(open, onOpen, onClose, onChange, onSwitch);
}

function deactivate() {}

module.exports = { activate, deactivate };
