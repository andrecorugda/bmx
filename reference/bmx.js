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

// **Leading spaces are removed HERE and nowhere else**, and that is the whole implementation of
// SPEC §1's insignificance rule. Doing it in the row builder rather than at each of the twenty
// places that read a line means every offset downstream is already a real source position — the
// alternative was `row.offset + indent` at each of them, which is twenty chances to forget one and
// hand the language server a column that points at whitespace.
//
// `raw` is kept because a code block's content is the one thing that must not be dedented per-line:
// it loses its FENCE's indentation and keeps the rest (§2.4).
function dedent(text) {
  let n = 0
  while (n < text.length && text[n] === ' ') n++
  return n
}

function lines(source) {
  const out = []
  let start = 0
  const push = (raw, offset) => {
    const indent = dedent(raw)
    out.push({ text: raw.slice(indent), raw, indent, offset: offset + indent })
  }
  for (let i = 0; i < source.length; i++) {
    if (source[i] === '\n') {
      let stop = i
      if (stop > start && source[stop - 1] === '\r') stop--
      push(source.slice(start, stop), start)
      start = i + 1
    }
  }
  if (start < source.length) push(source.slice(start), start)
  return out
}

// **The nesting refusal, in one place with three callers**, because three loops consume lines and
// each consumes its own: the top of the block loop sees a construct that STARTS indented, while the
// list and quote loops swallow their continuation lines before that top is ever reached again. I
// could not collapse them into one arm the way a recursion allows, so the thing holding this is the
// FIXTURES — a fourth consuming loop added later will not call this by itself. `- one` / `  - two`
// silently became a flat list until `014-nested-list` failed, and the quote shape was silently
// flattened with no fixture to say so until this pass added one.
function noNesting(row, what, fix) {
  throw new BmxError('BMX-E012', row.offset,
    `a ${what} may not nest; this line is indented. ${fix} — see §4a.2`)
}

// Removes up to `n` leading spaces — the opening fence's indentation and no more. A content line
// indented LESS than its fence keeps what it has rather than going negative.
function stripFenceIndent(raw, n) {
  let i = 0
  while (i < n && i < raw.length && raw[i] === ' ') i++
  return raw.slice(i)
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

// A block or attribute name: a letter, then letters, digits, `-` and `_`. The same rule
// everywhere a name appears, so there is one thing to remember and one thing to implement.
function isName(text) {
  return /^[A-Za-z][A-Za-z0-9_-]*$/.test(text)
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
        offset: base + i,
      })
      i = close + marker.length
      continue
    }

    if (c === ':' && text[i + 1] === ':') {
      // An inline block: `::name[head]::`. NOT a slot — a slot's value is escaped and this is a
      // call to something the host declared, so the two must look different at a glance.
      const open = text.indexOf('[', i + 2)
      const name = open < 0 ? '' : text.slice(i + 2, open)
      if (open < 0 || !isName(name)) {
        throw new BmxError('BMX-E034', base + i, 'an inline block is ::name[head]::')
      }
      const shut = text.indexOf(']::', open + 1)
      if (shut < 0) {
        throw new BmxError('BMX-E034', base + i, 'unterminated inline block: no ]:: on this line')
      }
      flush()
      out.push({
        type: 'inline_block',
        name,
        head: text.slice(open + 1, shut),
        offset: base + i,
        head_offset: base + open + 1,
      })
      i = shut + 3
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
        offset: base + i,
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

// How many colons a line opens or closes with.
// **A block opens with `:name:` and closes with `:!name:`, and nesting is by NAME.** 0.6 nested by
// fence length — a longer `::::` contained a shorter `:::` — and that rule is gone, along with the
// counting it asked of a reader. Andre's spelling, and the argument for it is one line of a real
// component: `:!button:` says what it closes, where `:::` said only *something ends here*.
//
// The closer is checked, which is what makes it worth writing: `:!for:` against an open `button` is
// refused (`BMX-E035`), so a closer can be wrong but it cannot LIE. That distinction is the whole
// reason it is not merely a comment.
const OPENER = /^:([A-Za-z][A-Za-z0-9_-]*):(.*)$/
const CLOSER = /^:!([A-Za-z][A-Za-z0-9_-]*):[ \t]*$/
// A one-liner ends with its own closer: `:span: class=box :!span:`. Matched at END of line only, so a
// `:!x:` inside a head's expression is untouched.
const ONELINER = /^(.*?)[ \t]*:!([A-Za-z][A-Za-z0-9_-]*):[ \t]*$/
// 0.6's spelling, recognised ONLY to say so. A document written for 0.6 fed to 0.7 would otherwise
// render its fences as paragraph text — the format's whole claim is that it does not do that.
const OLD_FENCE = /^:{3,}/
// A line that reaches for an opener and misses. Without this, `:9lives:` is a paragraph beginning with
// a colon rather than a refusal — silence in the one place the format promises noise.
const MALFORMED = /^:([^:\s]*):/

export function parse(source) {
  const rows = lines(source)
  const [children, end] = parseBlocks(rows, 0, null, -1)
  if (end !== rows.length) {
    // parseBlocks only stops early on a closer, and at the top level nothing is open.
    throw new BmxError('BMX-E032', rows[end].offset, 'a closer with no open block')
  }
  return { type: 'document', children }
}

// `open` is the name of the enclosing block, or null at the top level — a NAME rather than 0.6's
// fence length, because that is what a closer now carries.
function parseBlocks(rows, from, open, openRow) {
  const children = []
  let i = from

  while (i < rows.length) {
    const row = rows[i]
    const text = stripEnd(row.text)

    if (isBlank(text)) {
      i++
      continue
    }

    // A tab has a different width in every dialect, so a format promising one reading cannot accept
    // one in leading whitespace — even though the spaces around it mean nothing, a reader aligning by
    // eye and a parser counting bytes would disagree about what they are looking at.
    if (text[0] === '\t') {
      throw new BmxError('BMX-E010', row.offset, 'a tab in leading whitespace has no defined width')
    }

    // **Indentation is insignificant, with exactly two exceptions**, and they are exceptions because
    // those two constructs have no nesting at all in 0.4 (§2.3, §2.5) — so an indented one is not a
    // second spelling of something legal, it is the illegal thing with space in front of it.
    //
    // Until 0.5.1 this was a blanket refusal of every indented line, wearing the nested-list message.
    // `::: div` / `  hello` / `:::` was told *a list may not nest* about a document containing no
    // list, which is the worst shape a diagnostic can have: it is confident, it is specific, and it
    // names something the reader did not write.
    // **An indented list or quote is NOT a nest, and 0.6 through 0.7 refused it as one.**
    //
    // Found by round-tripping the suite through `tools/fmt.py`: indenting `:for:` / `- item` produced
    // *a list may not nest* on a document with one list in it. So the readable form of the single most
    // motivating example — a loop over a list — was illegal, in the release whose entire point was
    // making that form legal.
    //
    // The rules that replace it are narrower and say what nesting actually is:
    //
    // - **A quote's nesting is spelled `> > `**, so indentation plays no part in it at all. An indented
    //   `> ` is just an indented quote. Refusing it was symmetry copied from the list rule, and the
    //   list rule's reason did not transfer.
    // - **A list nests when a marker is DEEPER than the list already open** — `- one` / `  - two`.
    //   A marker with no list open starts one, whatever column it is in.

    // **A 0.6 document is refused by name rather than rendered as text.** This is the one diagnostic
    // in 0.7 that most people will meet, so it says what to run.
    if (OLD_FENCE.test(text)) {
      throw new BmxError('BMX-E036', row.offset,
        'this is the 0.6 fence: 0.7 opens with `:name:` and closes with `:!name:`. Run `python3 tools/migrate-0.7.py` over the file')
    }

    // ---- a closer: `:!name:` ----
    let m = CLOSER.exec(text)
    if (m) {
      if (open === null) {
        throw new BmxError('BMX-E032', row.offset, 'a closer with no open block')
      }
      if (m[1] !== open) {
        const at = rows[openRow]
        // **The check that makes a named closer worth writing.** Without it `:!for:` against an open
        // `button` would close the button anyway and the document would read as something it is not —
        // a closer that can be wrong AND is believed is worse than the bare `:::` it replaced.
        // **Both positions, opened-at and closed-at.** A message with one position sends the reader
        // back to counting, which is the exact work a named closer exists to delete. The Burxt session
        // asked for this and was right.
        throw new BmxError('BMX-E035', row.offset,
          `\`:!${m[1]}:\` closes nothing here — the open block is \`${open}\`, opened at ` +
          `${openRow + 1}:${at.indent + 1}, so its closer is \`:!${open}:\``)
      }
      return [children, i]
    }

    // A `:something:` whose something is not a name. Checked AFTER the closer and the real opener, so
    // `:!name:` and `:name:` reach their own branches first.
    m = MALFORMED.exec(text)
    if (m && !isName(m[1])) {
      throw new BmxError('BMX-E030', row.offset,
        'a block name is a letter, then letters, digits, - and _')
    }

    // ---- an opener: `:name:` and its head ----
    m = OPENER.exec(text)
    if (m) {
      const name = m[1]
      let rest = m[2]
      // A one-liner closes on its own line: `:span: class=box :!span:`. The trailing closer is taken
      // only at END of line and only when it names THIS block, so `:!x:` inside a head is left alone.
      let oneLiner = false
      const trailing = ONELINER.exec(rest)
      if (trailing && trailing[2] === name) {
        rest = trailing[1]
        oneLiner = true
      }
      const head = rest.replace(/^[ \t]+|[ \t]+$/g, '')
      // At most one #id. Everything else in the head belongs to the host.
      if ((head.match(/(^|[ \t])#[A-Za-z]/g) || []).length > 1) {
        throw new BmxError('BMX-E033', row.offset, 'a block may carry at most one #id')
      }
      let pad = 0
      while (pad < rest.length && (rest.charCodeAt(pad) === SPACE || rest.charCodeAt(pad) === TAB)) pad++
      // The head's first byte: past `:`, the name, `:`, and any spaces.
      const headOffset = row.offset + 1 + name.length + 1 + pad

      // **A one-liner's body is EMPTY, and that is a decision rather than an omission.** A head is
      // opaque to BMX by §4a.1 — the bytes after the name, unparsed, because heads belong to the host
      // — so in `:span: class=text {{ label }} :!span:` the format cannot tell where `class=text`
      // ended and the label began. There is no delimiter, and inventing one is a rule added. So
      // everything before the closer is head, and a block that needs a BODY takes three lines, where
      // the newline is the delimiter.
      const [body, end] = oneLiner ? [[], i] : parseBlocks(rows, i + 1, name, i)
      if (!oneLiner && end >= rows.length) {
        throw new BmxError('BMX-E031', row.offset, `unterminated block: no \`:!${name}:\``)
      }
      children.push({
        type: 'block',
        name,
        head,
        // **`one_line` exists because two documents that mean different things produced the same
        // node.** `:span: class=text hello :!span:` and the two-line form both came out as
        // `head: "class=text hello", children: []` — so a host wanting to treat trailing text as
        // BODY on the one-liner had to guess, and guessing would silently change the meaning of the
        // two-line form as well. star-burxt asked for it, having measured that its own head parser
        // turns a bare word into a boolean attribute and drops the text: `<span class="text" hello>`,
        // no refusal. The format cannot fix that — head meaning is the host's — but it can stop
        // withholding the one fact the host needs to fix it.
        one_line: oneLiner,
        offset: row.offset,
        head_offset: headOffset,
        children: body,
      })
      i = oneLiner ? i + 1 : end + 1
      continue
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
      children.push({
        type: 'heading',
        level,
        children: parseInline(body, row.offset + level + 1),
        offset: row.offset,
      })
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
        // The FENCE's indentation comes off; everything past it stays. So an indented fence holds
        // exactly the code you would have written at column 0, relative indentation included —
        // dedenting each line by its own indent would silently flatten the code instead.
        else value += stripFenceIndent(rows[j].raw, row.indent) + '\n'
        j++
      }
      // Markdown closes an open fence at end of document, which is the commonest way a page
      // becomes one giant code block with nobody told why.
      if (!closed) throw new BmxError('BMX-E003', row.offset, 'unterminated code fence')
      // Content is never parsed for inline content — a `{{` in here is two characters.
      children.push({ type: 'code', info, value, offset: row.offset })
      i = j
      continue
    }

    if (text.startsWith('> ')) {
      if (text.startsWith('> > ')) {
        throw new BmxError('BMX-E012', row.offset, "a quote may not nest. A block nests — see the format's §4a.2")
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
        offset: row.offset,
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
        // **This is where list nesting is caught, and it is the only place it can be.** A
        // continuation line never reaches the top of the block loop, because this loop consumes it.
        // Deeper than the item that opened the list is a nest; the same column, or shallower, is
        // another item — indentation means nothing except this one thing.
        if (rows[j].indent > row.indent) {
          noNesting(rows[j], 'list', 'Put the `- ` in the same column as the item above it, or make it a block')
        }
        // An ITEM is a node rather than a bare array, so it can carry its own position: "point
        // at the third item" is what a host needs and a list-level offset cannot say it.
        items.push({
          type: 'item',
          children: parseInline(inner.slice(skip), rows[j].offset + skip),
          offset: rows[j].offset,
        })
        j++
      }
      // An ordered list's numbers are content, not instructions: nothing renumbers them.
      children.push({ type: 'list', ordered: !unordered, items, offset: row.offset })
      i = j
      continue
    }

    const paragraph = []
    let j = i
    while (j < rows.length) {
      const inner = stripEnd(rows[j].text)
      const startsBlock =
        isBlank(inner) ||
        OPENER.test(inner) || CLOSER.test(inner) || OLD_FENCE.test(inner) ||
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
      offset: row.offset,
    })
    i = j
  }

  return [children, i]
}

// ---- lint: what parses and is still probably wrong ---------------------------
//
// **A linter for a format has one hard boundary and it is the same one as everything else.** BMX
// owns structure; a head's contents and a slot's expression are the host's. So there is no rule here
// about naming, about whether `on:click` should be there, or about how a component ought to be
// written — those are opinions only a host can hold, and a linter that held them would be the format
// acquiring a runtime by the back door.
//
// What is left is small, and that is the honest size rather than a first instalment. Each rule below
// is about the DOCUMENT: something the parser accepts and a reader would still call a mistake.
//
// Warnings, never errors. An error means BMX refuses the document; these all render fine. A linter
// that fails a build is a linter people turn off.

// **Names for which an empty body is correct rather than an oversight.**
//
// **`br` being void is not a claim about what a block MEANS.** It is a claim about what HTML permits
// inside a tag of that name, and the thirteen names are a list rather than a type system — which is
// the test `BOUNDARY.md` sets: *could a language with no types implement this?* Yes.
//
// star-burxt put it better than my first attempt, which reached for "the renderer emits HTML tags so
// neutrality is already gone". True but vague. The precise form: **Burxt's HTML renderer already
// depends on exactly this knowledge** — `lib/html.bx:182` returns early for a void tag so it writes
// `<br>` with no closing tag, and `html_element` refuses children on one at all. So exempting the
// thirteen adds no knowledge to the format; it makes explicit something a renderer already needs.
//
// One qualification, because their version was slightly too broad and that is the shape of half the
// corrections made today: it is the BURXT renderer that relies on it. The JavaScript one below never
// emits a void element, because it refuses blocks outright (BMX-R003) — so the dependency is real on
// one path and absent on the other. The BOUNDARY test above is what settles it either way.
//
// star-burxt reported this: `html_element` carries
// `requires !html_is_void(tag) || len(children) == 0`, so a void element MUST have an empty body and
// the rule was warning on correct code. Their example — `::: input on:input=…` — turned out already
// clean, because it has a head; the real false positive was narrower, `::: br` and `::: hr` with no
// head at all. A host with a different vocabulary passes its own list.
const SELF_CLOSING = [
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'source', 'track', 'wbr',
]

const LINTS = [
  {
    code: 'BMX-W001',
    // A heading level skip breaks the document outline, which is what a screen reader navigates by
    // and what a table of contents is built from. Structural, and invisible when you look at a page.
    //
    // **WITHIN the document, never "must start at h1".** A component that opens at `##` is correct —
    // the `#` belongs to the page embedding it — so the first heading sets the baseline whatever it
    // is. star-burxt asked which of the two this was; it was already the right one and the message
    // did not say so, which is the same thing as being unclear.
    check(blocks, source, warn) {
      let previous = 0
      for (const block of blocks) {
        if (block.type !== 'heading') continue
        if (previous && block.level > previous + 1) {
          warn(block.offset,
            `a heading jumps from level ${previous} to ${block.level} within this document. The ` +
            `outline a reader navigates by has a gap in it — use h${previous + 1}, or make the ` +
            `parent shallower. (Opening at any level is fine: only the jump is flagged.)`)
        }
        previous = block.level
      }
    },
  },
  {
    code: 'BMX-W002',
    // A block with no body renders as an empty element. It is almost always an unfinished edit, and
    // the cases where it is deliberate are exempt: a block with a HEAD is carrying its meaning there
    // (`props`, `input on:input=…`), and a void element must have an empty body by contract.
    check(blocks, source, warn, options) {
      const closing = options.selfClosing ?? SELF_CLOSING
      const walk = (list) => {
        for (const block of list) {
          if (block.type === 'block') {
            if (block.children.length === 0 && block.head.trim() === ''
                && !closing.includes(block.name)) {
              warn(block.offset,
                `\`${block.name}\` has no head and no body, so it renders as nothing. ` +
                `Give it content, give it a head, or delete it.`)
            }
            walk(block.children)
          }
        }
      }
      walk(blocks)
    },
  },
  {
    code: 'BMX-W005',
    // **Indentation cannot be wrong, which is exactly why it needs a warning.**
    //
    // Leading space means nothing to the parser (SPEC §1), so a block indented to the wrong depth is a
    // perfectly legal document that LIES to a reader — and a reviewer who trusts the columns is
    // trusted into the wrong block. That is the one hazard the insignificance rule introduced, and a
    // lint is the only thing that can see it.
    //
    // **It stays silent on a document that does not indent at all**, because a flat document is
    // correct and always was: every star-burxt component is flat and none is wrong. A warning that
    // fired on those would be the `BMX-W002` mistake again — a rule that flags correct code is a rule
    // people disable, taking the useful half with it. So it fires only where a document has ALREADY
    // chosen to indent and then contradicts itself, which is a mistake rather than a style.
    check(blocks, source, warn) {
      // Column of a line by byte offset, and the depth the document itself uses per level.
      const columnOf = (offset) => {
        const start = source.lastIndexOf('\n', offset - 1) + 1
        return offset - start
      }
      // The step is measured from the document rather than assumed: a file indenting by four is
      // consistent, and telling its author that two is correct would be this format having an opinion
      // about whitespace, which §1 spends its whole length refusing.
      let step = 0
      const learn = (list, depth) => {
        for (const block of list) {
          if (block.type !== 'block') continue
          const col = columnOf(block.offset)
          if (depth === 1 && col > 0 && step === 0) step = col
          learn(block.children, depth + 1)
        }
      }
      // Depth 0 is the top level, whose blocks sit at column 0 — so the step is learned from the
      // first block one level IN. Numbering the top level 1 meant looking for an indented block where
      // there cannot be one, and the rule stayed silent on every document.
      learn(blocks, 0)
      if (step === 0) return          // a flat document, or one whose first nested block is flat

      const walk = (list, depth) => {
        for (const block of list) {
          if (block.type !== 'block') continue
          const col = columnOf(block.offset)
          const want = depth * step
          if (col !== want) {
            warn(block.offset,
              `this block sits at column ${col} but is ${depth} level${depth === 1 ? '' : 's'} deep, ` +
              `where the document indents by ${step}, so ${want} is expected. ` +
              'Indentation means nothing to the parser, which is why a wrong one misleads a reader ' +
              'with nothing to catch it — `python3 tools/fmt.py` fixes the file.')
          }
          walk(block.children, depth + 1)
        }
      }
      walk(blocks, 0)
    },
  },
  {
    code: 'BMX-W003',
    // An empty link target is a link to the current page, which is never what anybody meant.
    check(blocks, source, warn) {
      const inline = (nodes) => {
        for (const node of nodes) {
          if (node.type === 'link' && node.target.trim() === '') {
            warn(node.offset, 'a link with an empty target points at the current page. ' +
              'Give it a target, or write the text without brackets.')
          }
          if (node.children) inline(node.children)
        }
      }
      const walk = (list) => {
        for (const block of list) {
          if (block.children) block.type === 'block' ? walk(block.children) : inline(block.children)
          if (block.items) for (const item of block.items) inline(item.children)
        }
      }
      walk(blocks)
    },
  },
]

/**
 * Everything a linter can say about a document that PARSES.
 *
 * `options.selfClosing` replaces the list of block names for which an empty body is expected. The
 * default is HTML's void elements; a host whose vocabulary differs passes its own.
 *
 * Returns `{ code, message, offset, line, column }` objects, in document order. A document that does
 * not parse has one error and no warnings — there is nothing to lint in a tree that does not exist,
 * and reporting style notes about a broken document buries the reason it is broken.
 */
export function lint(source, options = {}) {
  let blocks
  try {
    blocks = parse(source).children
  } catch (e) {
    if (e instanceof BmxError) return []
    throw e
  }
  const found = []
  for (const rule of LINTS) {
    rule.check(blocks, source, (offset, message) => {
      found.push({ code: rule.code, message, offset, ...at(source, offset) })
    }, options)
  }
  return found.sort((a, b) => a.offset - b.offset)
}

/** A byte offset as a line and a CHARACTER column, both one-based. */
export function at(source, offset) {
  const upto = source.slice(0, Math.max(0, Math.min(offset, source.length)))
  const line = upto.split('\n').length
  const lastBreak = upto.lastIndexOf('\n') + 1
  // Characters, not bytes — a byte column is right on every ASCII line and wrong on the first line
  // with an accent in it. The same decision `bmx_where` makes on the Burxt side.
  return { line, column: [...upto.slice(lastBreak)].length + 1 }
}

// ---- level 1: rendering ------------------------------------------------------
//
// **This existed as a claim before it existed as code.** `README.md` listed this file as "1 —
// renders" while it exported only `parse`, and `BOUNDARY.md` defines level 1 as parsing *and*
// substituting slot values with escaping applied. So the table was describing a level this
// implementation had not reached — the third claim of that shape found in these docs, and this one
// was load-bearing, because "any language can reach level 1" is the sentence that makes BMX
// adoptable and the reference implementation is the proof.
//
// Every rule below is measured against Burxt's renderer rather than inferred from the spec, and
// `tests/renders.mjs` compares the two over the whole corpus. Where they differ, one of them is
// wrong and the suite says so.

const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }

/** The one escaping rule, and there is no way to opt out of it — that is ESCAPING.md. */
const escape = (s) => s.replace(/[&<>"']/g, (c) => ESCAPES[c])

/** `/path`, or a scheme BMX's renderer allows. A scheme it does not know is refused, not stripped. */
function targetAllowed(target) {
  const colon = target.indexOf(':')
  const slash = target.indexOf('/')
  if (slash >= 0 && (colon < 0 || slash < colon)) return true
  if (colon < 0) return true
  return ['http', 'https', 'mailto'].includes(target.slice(0, colon))
}

function renderInline(nodes, bindings) {
  let out = ''
  for (const node of nodes) {
    switch (node.type) {
      case 'text':
        out += escape(node.value)
        break
      case 'emphasis':
        out += `<em>${renderInline(node.children, bindings)}</em>`
        break
      case 'strong':
        out += `<strong>${renderInline(node.children, bindings)}</strong>`
        break
      case 'code_span':
        out += `<code>${escape(node.value)}</code>`
        break
      case 'link':
        if (!targetAllowed(node.target)) {
          throw new BmxError('BMX-R001', node.offset,
            `refused a link target whose scheme is not http, https or mailto: ${node.target}`)
        }
        out += `<a href="${escape(node.target)}">${renderInline(node.children, bindings)}</a>`
        break
      case 'slot': {
        // **A missing binding is an error, never an empty string.** The empty string is how a page
        // ships with a missing total nobody sees, which is the whole thing BMX exists to stop.
        if (!(node.expression in bindings)) {
          throw new BmxError('BMX-R002', node.offset,
            `no binding for slot \`${node.expression}\``)
        }
        // Escaped, always. There is no syntax that opts out.
        out += escape(String(bindings[node.expression]))
        break
      }
      case 'inline_block':
        // SPEC §4a.5: a host must refuse a block it did not declare, and never render it or skip it
        // silently. This renderer declares none — a component's value is the compiler checking the
        // call, which is level 2.
        throw new BmxError('BMX-R003', node.offset,
          `this renderer declares no blocks, and \`${node.name}\` is one. Compile the document instead.`)
      default:
        throw new BmxError('BMX-R004', node.offset ?? 0, `unknown inline node \`${node.type}\``)
    }
  }
  return out
}

function renderBlocks(blocks, bindings) {
  let out = ''
  for (const block of blocks) {
    switch (block.type) {
      case 'heading':
        out += `<h${block.level}>${renderInline(block.children, bindings)}</h${block.level}>`
        break
      case 'paragraph':
        out += `<p>${renderInline(block.children, bindings)}</p>`
        break
      case 'quote':
        out += `<blockquote>${renderInline(block.children, bindings)}</blockquote>`
        break
      case 'list': {
        const tag = block.ordered ? 'ol' : 'ul'
        const items = block.items
          .map((item) => `<li>${renderInline(item.children, bindings)}</li>`)
          .join('')
        out += `<${tag}>${items}</${tag}>`
        break
      }
      case 'code': {
        // The info string becomes the class every highlighter expects — and is checked as a NAME
        // first, because an info string is author text and an unchecked one is a markup hole.
        const cls = block.info && isName(block.info) ? ` class="language-${escape(block.info)}"` : ''
        out += `<pre><code${cls}>${escape(block.value)}</code></pre>`
        break
      }
      case 'block':
        throw new BmxError('BMX-R003', block.offset,
          `this renderer declares no blocks, and \`${block.name}\` is one. Compile the document instead.`)
      default:
        throw new BmxError('BMX-R004', block.offset ?? 0, `unknown block \`${block.type}\``)
    }
  }
  return out
}

/**
 * A document and its slot values, in; a page, out.
 *
 * `bindings` maps a slot's expression text to a value. BMX does not evaluate expressions — that is
 * the host's, per BOUNDARY.md — so a level-1 renderer can only look one up by the exact text the
 * author wrote. A level-2 host compiles them instead, which is why only a typed language reaches it.
 */
export function render(source, bindings = {}) {
  return `<article class="bmx">${renderBlocks(parse(source).children, bindings)}</article>`
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
