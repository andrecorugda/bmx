#!/usr/bin/env node
// not-burxt: platform — the artefact under test, or its runtime, is JavaScript and nothing else can be
// Drive the language server with real LSP frames.
//
// **Every failure mode of a server is a silence.** A wrong Content-Length, a frame split across two
// chunks, a request answered with nothing — the editor does not error, it just stops showing
// diagnostics, and the author concludes the extension is broken or that their document is fine. So
// the framing is exercised deliberately, not only the happy path.
//
//   node editors/lsp/test/protocol.mjs
//
// Exits non-zero on the first failed expectation.

import { spawn } from 'node:child_process'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const server = spawn('node', [join(here, '..', 'bmx-lsp.mjs')], { stdio: ['pipe', 'pipe', 'pipe'] })

let stderr = ''
server.stderr.on('data', (d) => { stderr += d.toString() })

const frames = []
const waiters = []
let buffer = Buffer.alloc(0)
server.stdout.on('data', (chunk) => {
  buffer = Buffer.concat([buffer, chunk])
  for (;;) {
    const split = buffer.indexOf('\r\n\r\n')
    if (split < 0) return
    const length = Number(/Content-Length: *(\d+)/i.exec(buffer.slice(0, split).toString())[1])
    if (buffer.length < split + 4 + length) return
    const body = JSON.parse(buffer.slice(split + 4, split + 4 + length).toString('utf8'))
    buffer = buffer.slice(split + 4 + length)
    frames.push(body)
    for (const [predicate, resolve] of waiters.splice(0)) {
      if (predicate(body)) resolve(body)
      else waiters.push([predicate, resolve])
    }
  }
})

function frame(body) {
  const text = JSON.stringify({ jsonrpc: '2.0', ...body })
  return `Content-Length: ${Buffer.byteLength(text, 'utf8')}\r\n\r\n${text}`
}
const send = (body) => server.stdin.write(frame(body))

function until(predicate, what) {
  const found = frames.find(predicate)
  if (found) return Promise.resolve(found)
  return new Promise((resolve, reject) => {
    waiters.push([predicate, resolve])
    setTimeout(() => reject(new Error(`timed out waiting for ${what}`)), 5000)
  })
}
const diagnosticsFor = (uri) =>
  until((f) => f.method === 'textDocument/publishDiagnostics' && f.params.uri === uri,
        `diagnostics for ${uri}`)

let failures = 0
function check(name, condition, detail) {
  if (condition) console.log(`  ok    ${name}`)
  else { console.log(`  FAIL  ${name}${detail ? `\n        ${detail}` : ''}`); failures++ }
}

const openDoc = (uri, text) =>
  send({ method: 'textDocument/didOpen', params: { textDocument: { uri, languageId: 'bmx', version: 1, text } } })

async function main() {
  send({ id: 1, method: 'initialize', params: { capabilities: {} } })
  const ready = await until((f) => f.id === 1, 'the initialize reply')
  check('it answers initialize', !!ready.result)
  check('it declares full document sync', ready.result.capabilities.textDocumentSync === 1,
    JSON.stringify(ready.result.capabilities))
  check('it names itself', ready.result.serverInfo?.name === 'bmx-lsp')

  // ---- a refusal ----
  openDoc('file:///broken.bmx', 'Your balance is **£240.00\n')
  const broken = (await diagnosticsFor('file:///broken.bmx')).params.diagnostics
  check('a broken document reports one error', broken.length === 1, JSON.stringify(broken))
  check('with the format\'s code', broken[0]?.code === 'BMX-E002', broken[0]?.code)
  check('at severity Error', broken[0]?.severity === 1)
  check('and the message does not repeat the code and offset',
    !/^BMX-E002 at /.test(broken[0]?.message ?? ''), broken[0]?.message)

  // ---- ZERO-based positions, which is the thing everybody gets wrong ----
  openDoc('file:///second-line.bmx', 'fine\n**broken\n')
  const second = (await diagnosticsFor('file:///second-line.bmx')).params.diagnostics
  check('a problem on line 2 is reported as line 1, because LSP is zero-based',
    second[0]?.range.start.line === 1, JSON.stringify(second[0]?.range))

  // ---- a CHARACTER column, on a line with a multi-byte character ----
  openDoc('file:///accent.bmx', 'Your bålance is **£240.00\n')
  const accent = (await diagnosticsFor('file:///accent.bmx')).params.diagnostics
  check('the column counts characters, not bytes (16 not 17 on a line with `å`)',
    accent[0]?.range.start.character === 16, JSON.stringify(accent[0]?.range))

  // ---- lints, on a document that parses ----
  openDoc('file:///lint.bmx', '# One\n\n### Three\n\n:bare:\n:!bare:\n')
  const lints = (await diagnosticsFor('file:///lint.bmx')).params.diagnostics
  check('a document that parses gets warnings', lints.length === 2, JSON.stringify(lints.map(d => d.code)))
  check('at severity Warning', lints.every((d) => d.severity === 2))
  check('the heading skip is found', lints.some((d) => d.code === 'BMX-W001'))
  check('the empty block is found', lints.some((d) => d.code === 'BMX-W002'))

  // ---- a refusal SUPPRESSES lints, so the reason is not buried ----
  openDoc('file:///both.bmx', '# One\n\n### Three\n\nUnterminated **bold\n')
  const both = (await diagnosticsFor('file:///both.bmx')).params.diagnostics
  check('a document that does not parse reports the refusal only',
    both.length === 1 && both[0].severity === 1, JSON.stringify(both.map(d => d.code)))

  // ---- an edit republishes ----
  send({ method: 'textDocument/didChange',
         params: { textDocument: { uri: 'file:///broken.bmx', version: 2 },
                   contentChanges: [{ text: '# fixed\n' }] } })
  const fixed = await until((f) => f.method === 'textDocument/publishDiagnostics'
    && f.params.uri === 'file:///broken.bmx' && f.params.diagnostics.length === 0, 'the cleared frame')
  check('fixing the document clears its diagnostics', fixed.params.diagnostics.length === 0)

  // ---- closing clears, or a stale problem outlives the file ----
  send({ method: 'textDocument/didClose', params: { textDocument: { uri: 'file:///lint.bmx' } } })
  const closed = await until((f) => f.method === 'textDocument/publishDiagnostics'
    && f.params.uri === 'file:///lint.bmx' && f.params.diagnostics.length === 0, 'the close clear')
  check('closing a document clears its diagnostics', closed.params.diagnostics.length === 0)

  // ---- THE framing case: one message, delivered in two pieces ----
  const whole = frame({ method: 'textDocument/didOpen',
    params: { textDocument: { uri: 'file:///split.bmx', languageId: 'bmx', version: 1,
                              text: 'Broken **here\n' } } })
  server.stdin.write(whole.slice(0, 30))
  await new Promise((r) => setTimeout(r, 60))
  server.stdin.write(whole.slice(30))
  const split = await diagnosticsFor('file:///split.bmx')
  check('a frame split across two writes is still read',
    split.params.diagnostics[0]?.code === 'BMX-E002', JSON.stringify(split.params.diagnostics))

  // ---- an unknown REQUEST is answered, so the client does not hang ----
  send({ id: 99, method: 'textDocument/formatting', params: {} })
  const refused = await until((f) => f.id === 99, 'the reply to an unsupported request')
  check('an unsupported request is answered rather than ignored', !!refused.error, JSON.stringify(refused))

  // ---- LAST, and the ordering is the point ----
  //
  // **A server that answers nothing to everything passes this assertion on its own.** So it comes
  // after every case that proves this one can speak — the refusal, the warnings, the positions. Taken
  // from star-burxt's driver, which had it last while mine had it second: the vacuity problem in a
  // place I had not thought to look.
  openDoc('file:///clean.bmx', '# Title\n\nA paragraph.\n')
  const clean = await diagnosticsFor('file:///clean.bmx')
  check('a clean document publishes an empty list rather than nothing',
    Array.isArray(clean.params.diagnostics) && clean.params.diagnostics.length === 0,
    JSON.stringify(clean.params.diagnostics))

  send({ id: 100, method: 'shutdown', params: {} })
  await until((f) => f.id === 100, 'the shutdown reply')
  check('it answers shutdown', true)
  send({ method: 'exit' })

  console.log()
  if (stderr.trim()) console.log(`server stderr:\n${stderr}`)
  if (failures) { console.log(`${failures} failed`); process.exit(1) }
  console.log('the server says what it should, when it should, in the right coordinates')
}

main().catch((e) => { console.log(`  FAIL  ${e.message}`); if (stderr) console.log(stderr); process.exit(1) })
