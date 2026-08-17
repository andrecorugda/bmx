#!/usr/bin/env node
// A language server for BMX. Diagnostics only, over stdio, no dependencies.
//
//   bmx-lsp.mjs            # speaks LSP on stdin/stdout
//
// **Why this exists after I argued it should not.** `editors/README.md` said BMX would ship no server
// because "most editors let one language server own a file, so a BMX server and a framework's server
// would fight over `.bmx`". The conclusion did not follow from the fact, and the fact was wrong in the
// part that mattered: **diagnostics are additive.** In VS Code each extension owns a named
// `DiagnosticCollection` and they merge in the Problems panel; helix and nvim both run several servers
// for one language. What genuinely conflicts is formatting, which this does not provide.
//
// So the argument only ever justified not shipping *completion* or *hover* — and meanwhile the common
// case, somebody writing `.bmx` documents with no framework at all, had no diagnostics in their editor
// and had to run a command to find out a document was broken.
//
// **What it deliberately does not do**, and each is a host's rather than a gap:
//
//   completion for block names   BMX does not know which blocks exist. A host declares them.
//   hover                        the same: there is nothing to say about `card` that BMX knows.
//   formatting                   reflowing a head means deciding what it means.
//   go-to-definition             a component lives wherever the host's module system says.
//
// A framework builds those on top, in its own server, and both sets of diagnostics show at once.

import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
// The implementation lives at the repository root; the extension stages a copy beside itself.
const candidates = [
  join(here, '..', '..', 'reference', 'bmx.js'),
  join(here, '..', 'vscode', 'reference', 'bmx.mjs'),
  join(here, 'reference', 'bmx.mjs'),
]
let bmx = null
for (const path of candidates) {
  try {
    bmx = await import(pathToFileURL(path).href)
    break
  } catch {
    /* try the next layout */
  }
}
if (!bmx) {
  process.stderr.write(`bmx-lsp: cannot find bmx.js — looked in:\n  ${candidates.join('\n  ')}\n`)
  process.exit(2)
}

const ERROR = 1
const WARNING = 2

/** Everything to say about one document: the refusal if it has one, then the warnings. */
function diagnose(text) {
  const out = []
  try {
    bmx.parse(text)
  } catch (e) {
    if (!(e instanceof bmx.BmxError)) throw e
    const { line, column } = bmx.at(text, e.offset)
    // **The span is the rest of the line, not one character.** A caret on a single byte is hard to
    // see and often points at the character AFTER the mistake — an unterminated `**` is reported
    // where it opened, and the problem is everything from there on.
    const lines = text.split('\n')
    const length = Math.max(1, (lines[line - 1] || '').length - (column - 1))
    out.push({
      range: span(line, column, length),
      severity: ERROR,
      code: e.code,
      source: 'bmx',
      message: e.message.replace(/^\S+ at \d+: /, ''),
    })
    // A document that does not parse has no tree, so there is nothing to lint. Reporting style
    // notes beside a refusal buries the refusal.
    return out
  }
  for (const w of bmx.lint(text)) {
    out.push({
      range: span(w.line, w.column, 1),
      severity: WARNING,
      code: w.code,
      source: 'bmx',
      message: w.message,
    })
  }
  return out
}

/** LSP positions are ZERO-based; `at` answers one-based, because that is what a human reads. */
function span(line, column, length) {
  return {
    start: { line: line - 1, character: column - 1 },
    end: { line: line - 1, character: column - 1 + length },
  }
}

// ---- the protocol ------------------------------------------------------------------------------

const open = new Map() // uri -> text

function send(message) {
  const body = JSON.stringify({ jsonrpc: '2.0', ...message })
  // Content-Length is in BYTES. Using `body.length` is correct until the first non-ASCII character
  // in a diagnostic message, and then the client reads a truncated frame and goes quiet.
  process.stdout.write(`Content-Length: ${Buffer.byteLength(body, 'utf8')}\r\n\r\n${body}`)
}

function publish(uri) {
  send({ method: 'textDocument/publishDiagnostics', params: { uri, diagnostics: diagnose(open.get(uri) ?? '') } })
}

function handle(message) {
  const { id, method, params } = message
  switch (method) {
    case 'initialize':
      send({
        id,
        result: {
          capabilities: {
            // 1 = full text on every change. A document is small and the parser has no incremental
            // mode, so anything cleverer would be a claim without a measurement behind it.
            textDocumentSync: 1,
          },
          serverInfo: { name: 'bmx-lsp', version: '0.1.0' },
        },
      })
      break
    case 'initialized':
      break
    case 'textDocument/didOpen':
      open.set(params.textDocument.uri, params.textDocument.text)
      publish(params.textDocument.uri)
      break
    case 'textDocument/didChange':
      open.set(params.textDocument.uri, params.contentChanges.at(-1).text)
      publish(params.textDocument.uri)
      break
    case 'textDocument/didClose':
      open.delete(params.textDocument.uri)
      // Clearing on close is not optional: a stale diagnostic for a file nobody has open is a
      // problem the reader cannot find or dismiss.
      send({ method: 'textDocument/publishDiagnostics', params: { uri: params.textDocument.uri, diagnostics: [] } })
      break
    case 'shutdown':
      send({ id, result: null })
      break
    case 'exit':
      process.exit(0)
    default:
      // A request must be answered even when unsupported, or the client waits forever. A
      // notification (no id) is dropped, which is what the protocol says to do.
      if (id !== undefined) send({ id, error: { code: -32601, message: `no method ${method}` } })
  }
}

let buffer = Buffer.alloc(0)
process.stdin.on('data', (chunk) => {
  buffer = Buffer.concat([buffer, chunk])
  for (;;) {
    const split = buffer.indexOf('\r\n\r\n')
    if (split < 0) return
    const header = buffer.slice(0, split).toString('ascii')
    const match = /Content-Length: *(\d+)/i.exec(header)
    if (!match) {
      // Unrecoverable: without a length there is no way to find the next frame.
      process.stderr.write(`bmx-lsp: a frame arrived with no Content-Length\n`)
      process.exit(2)
    }
    const length = Number(match[1])
    const start = split + 4
    // **A message can arrive split across chunks**, which is the failure that looks fine in testing
    // and appears under load. Wait rather than parse a fragment.
    if (buffer.length < start + length) return
    const body = buffer.slice(start, start + length).toString('utf8')
    buffer = buffer.slice(start + length)
    try {
      handle(JSON.parse(body))
    } catch (e) {
      process.stderr.write(`bmx-lsp: ${e && e.message ? e.message : String(e)}\n`)
    }
  }
})

process.stdin.on('end', () => process.exit(0))
