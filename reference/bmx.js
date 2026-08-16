// bmx.js — the BMX 0.1 reference parser. Zero dependencies.
//
//   import { parse, BmxError } from './bmx.js'
//   node reference/bmx.js document.bmx        # prints the AST as JSON
//
// **Why a reference implementation exists at all**, given that the specification and its
// conformance suite are the artifacts that travel:
//
//   * A spec exercised by one implementation is a description of that implementation. CommonMark
//     shipped `cmark` alongside its spec for this reason, and the three-dialect mess BMX exists
//     to fix came from a spec that had no reference.
//   * Two implementations that must AGREE is a stronger test than either one passing a suite
//     somebody wrote by hand. It is the same discipline Burxt applies to itself — two compilers,
//     byte-identical output — pointed at a format instead of a language.
//   * And it proves the claim the format makes about itself: that conformance costs an afternoon
//     in any language rather than a port.
//
// This is a **level 1** implementation: it parses. It does not check slot expressions against
// anything, because JavaScript has nothing to check them with — see BOUNDARY.md, which is
// precisely the line this file sits on the other side of.
//
// It is written to be READ. No cleverness, no lookup tables, no regex where a loop is clearer:
// somebody porting BMX to a third language should be able to follow this top to bottom.

export class BmxError extends Error {
  constructor(code, offset, message) {
    super(`${code} at ${offset}: ${message}`)
    this.code = code
    this.offset = offset
  }
}

const SPACE = 0x20
const TAB = 0x09

// ---- lines ------------------------------------------------------------------
//
// `\n` ends a line and a `\r` immediately before it is consumed with it. A LONE `\r` is an
// ordinary byte: a stray carriage return mid-line is far more likely to be data than intent,
// and the format decides that once rather than leaving each parser to guess.

function lines(source) {
  const out = []
  let start = 0
  for (let i = 0; i < source.length; i++) {
    if (source[i] === '\n') {
      let stop = i
      if (stop > start && source[stop - 1] === '\r') stop--
      out.push({ text: source.slice(start, stop), offset: start })
      start = i + 1
    }
  }
  if (start < source.length) out.push({ text: source.slice(start), offset: start })
  return out
}

// Trailing spaces go. There is no two-space line break in BMX — an invisible character that
// changes the output is unreviewable by construction.
const stripEnd = (text) => text.replace(/ +$/, '')

const isBlank = (text) => /^ *$/.test(text)

// The byte after a `12. ` marker, or -1.
function orderedMarker(text) {
  let i = 0
  while (i < text.length && text[i] >= '0' && text[i] <= '9') i++
  if (i === 0) return -1
  if (text[i] !== '.' || text[i + 1] !== ' ') return -1
  return i + 2
}

// ---- inline -----------------------------------------------------------------
//
// `base` is where `text` begins in the whole document, so a slot's offset points into the file
// the author opened. Inline content is parsed ONE LINE AT A TIME — never over a joined buffer —
// because joining first puts every offset off by the trailing spaces stripped from earlier
// lines. The spec already requires every inline construct to close on its own line, so there is
// nothing to parse across.

function parseInline(text, base) {
  const out = []
  let buffer = ''
  const flush = () => {
    if (buffer.length > 0) {
      out.push({ type: 'text', value: buffer })
      buffer = ''
    }
  }

  let i = 0
  while (i < text.length) {
    const c = text[i]

    if (c === '\\') {
      // One escape rule. A backslash before anything else is an error rather than
      // sometimes-a-backslash — that ambiguity is where markdown dialects diverge.
      if (i + 1 >= text.length) {
        throw new BmxError('BMX-E021', base + i, 'a backslash at the end of a line escapes nothing')
      }
      const next = text[i + 1]
      if (!'`*[{\\'.includes(next)) {
        throw new BmxError('BMX-E021', base + i, 'only ` * [ { and \\ may be escaped')
      }
      buffer += next
      i += 2
      continue
    }

    if (c === '{' && text[i + 1] === '{') {
      const close = text.indexOf('}}', i + 2)
      if (close < 0) {
        throw new BmxError('BMX-E001', base + i, 'unterminated slot: no }} on this line')
      }
      const raw = text.slice(i + 2, close)
      const expression = raw.replace(/^[ \t]+|[ \t]+$/g, '')
      if (expression.length === 0) {
        throw new BmxError('BMX-E022', base + i, "a slot's expression is empty")
      }
      // The offset is the first byte of the EXPRESSION, not of the `{{`, so a host underlines
      // the text it is complaining about.
      let pad = 0
      while (pad < raw.length && (raw.charCodeAt(pad) === SPACE || raw.charCodeAt(pad) === TAB)) pad++
      flush()
      out.push({ type: 'slot', expression, offset: base + i + 2 + pad })
      i = close + 2
      continue
    }

    if (c === '`') {
      const close = text.indexOf('`', i + 1)
      if (close < 0) throw new BmxError('BMX-E020', base + i, 'unterminated code span')
      flush()
      // A code span's bytes are literal to the closing backtick — no nested inline content.
      out.push({ type: 'code_span', value: text.slice(i + 1, close) })
      i = close + 1
      continue
    }

    if (c === '*') {
      const strong = text[i + 1] === '*'
      const marker = strong ? '**' : '*'
      const from = i + marker.length
      const close = text.indexOf(marker, from)
      if (close < 0) {
        throw new BmxError('BMX-E002', base + i, `unterminated ${strong ? 'strong' : 'emphasis'}`)
      }
      flush()
      out.push({
        type: strong ? 'strong' : 'emphasis',
        children: parseInline(text.slice(from, close), base + from),
      })
      i = close + marker.length
      continue
    }

    if (c === '[') {
      const shut = text.indexOf(']', i + 1)
      if (shut < 0) throw new BmxError('BMX-E004', base + i, 'unterminated link text')
      if (text[shut + 1] !== '(') {
        throw new BmxError('BMX-E004', base + i, "a link's text must be followed by (target)")
      }
      const end = text.indexOf(')', shut + 2)
      if (end < 0) throw new BmxError('BMX-E004', base + i, 'unterminated link target')
      flush()
      out.push({
        type: 'link',
        target: text.slice(shut + 2, end),
        children: parseInline(text.slice(i + 1, shut), base + i + 1),
      })
      i = end + 1
      continue
    }

    buffer += c
    i++
  }

  flush()
  return out
}

// Adjacent text nodes are ALWAYS merged. Two implementations that disagree about whether `a` `b`
// is one node or two disagree about the document, so the format decides it rather than leaving
// it to chance.
function mergeText(nodes) {
  const out = []
  let pending = null
  for (const node of nodes) {
    if (node.type === 'text') {
      pending = pending === null ? node.value : pending + node.value
    } else {
      if (pending !== null) {
        out.push({ type: 'text', value: pending })
        pending = null
      }
      out.push(node)
    }
  }
  if (pending !== null) out.push({ type: 'text', value: pending })
  return out
}

// Inline content spanning several lines: each line parsed against its OWN offset, with a
// newline between, then merged.
function parseLines(rows, offsetOf, textOf) {
  const kids = []
  rows.forEach((row, n) => {
    if (n > 0) kids.push({ type: 'text', value: '\n' })
    kids.push(...parseInline(textOf(row), offsetOf(row)))
  })
  return mergeText(kids)
}

// ---- blocks -----------------------------------------------------------------

export function parse(source) {
  const rows = lines(source)
  const children = []
  let i = 0

  while (i < rows.length) {
    const row = rows[i]
    const text = stripEnd(row.text)

    if (isBlank(text)) {
      i++
      continue
    }

    // A tab has a different width in every dialect, so a format promising one reading cannot
    // accept one where indentation matters.
    if (text[0] === '\t') {
      throw new BmxError('BMX-E010', row.offset, 'a tab in leading whitespace has no defined width')
    }
    if (text[0] === ' ') {
      throw new BmxError('BMX-E012', row.offset, '0.1 has no nesting; this line is indented')
    }

    if (text[0] === '#') {
      let level = 0
      while (level < text.length && text[level] === '#') level++
      if (level > 6) throw new BmxError('BMX-E011', row.offset, 'a heading is one to six #')
      if (text[level] !== ' ') {
        throw new BmxError('BMX-E011', row.offset, 'a heading needs exactly one space after its #')
      }
      const body = text.slice(level + 1)
      if (body.length === 0) throw new BmxError('BMX-E011', row.offset, 'a heading may not be empty')
      children.push({ type: 'heading', level, children: parseInline(body, row.offset + level + 1) })
      i++
      continue
    }

    if (text.startsWith('```')) {
      const info = text.slice(3)
      let value = ''
      let j = i + 1
      let closed = false
      while (j < rows.length && !closed) {
        if (stripEnd(rows[j].text) === '```') closed = true
        else value += rows[j].text + '\n'
        j++
      }
      // Markdown closes an open fence at end of document, which is the commonest way a page
      // becomes one giant code block with nobody told why.
      if (!closed) throw new BmxError('BMX-E003', row.offset, 'unterminated code fence')
      // Content is never parsed for inline content — a `{{` in here is two characters.
      children.push({ type: 'code', info, value })
      i = j
      continue
    }

    if (text.startsWith('> ')) {
      if (text.startsWith('> > ')) {
        throw new BmxError('BMX-E012', row.offset, '0.1 has no nested quotes')
      }
      const quoted = []
      let j = i
      while (j < rows.length && stripEnd(rows[j].text).startsWith('> ')) {
        quoted.push(rows[j])
        j++
      }
      children.push({
        type: 'quote',
        children: parseLines(quoted, (r) => r.offset + 2, (r) => stripEnd(r.text).slice(2)),
      })
      i = j
      continue
    }

    const unordered = text.startsWith('- ')
    if (unordered || orderedMarker(text) > 0) {
      const items = []
      let j = i
      while (j < rows.length) {
        const inner = stripEnd(rows[j].text)
        const skip = unordered
          ? (inner.startsWith('- ') ? 2 : -1)
          : orderedMarker(inner)
        if (skip < 0) break
        items.push(parseInline(inner.slice(skip), rows[j].offset + skip))
        j++
      }
      // An ordered list's numbers are content, not instructions: nothing renumbers them.
      children.push({ type: 'list', ordered: !unordered, items })
      i = j
      continue
    }

    const paragraph = []
    let j = i
    while (j < rows.length) {
      const inner = stripEnd(rows[j].text)
      const startsBlock =
        isBlank(inner) ||
        inner.startsWith('#') ||
        inner.startsWith('```') ||
        inner.startsWith('> ') ||
        inner.startsWith('- ') ||
        orderedMarker(inner) > 0
      if (j > i && startsBlock) break
      paragraph.push(rows[j])
      j++
    }
    children.push({
      type: 'paragraph',
      children: parseLines(paragraph, (r) => r.offset, (r) => stripEnd(r.text)),
    })
    i = j
  }

  return { type: 'document', children }
}

// ---- the command line the conformance harness drives ------------------------

if (process.argv[1] && process.argv[1].endsWith('bmx.js')) {
  const { readFileSync } = await import('node:fs')
  const path = process.argv[2]
  if (!path) {
    console.error('usage: node reference/bmx.js <document.bmx>')
    process.exit(2)
  }
  try {
    console.log(JSON.stringify(parse(readFileSync(path, 'utf8'))))
  } catch (e) {
    if (e instanceof BmxError) {
      console.error(e.message)
      process.exit(1)
    }
    throw e
  }
}
