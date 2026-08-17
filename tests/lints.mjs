#!/usr/bin/env node
// The linter's rules, and — more importantly — what they must NOT fire on.
//
// **A lint that fires on correct code is worse than no lint**, because the fix is to switch the
// linter off and then none of the rules run. So the cases below are half positives and half
// negatives, and the negatives are the ones that came from a consumer rather than from imagination:
// star-burxt reported `BMX-W002` warning on void elements, whose bodies must be empty by contract.
//
// Measuring the report found it narrower than described — their own example was already clean,
// because it has a head — which is why the exact cases live here rather than a paraphrase of them.
//
//   node tests/lints.mjs

import { lint } from '../reference/bmx.js'

let failures = 0

function expect(what, source, codes, options) {
  const got = lint(source, options).map((w) => w.code)
  const same = got.length === codes.length && got.every((c, i) => c === codes[i])
  if (same) console.log(`  ok    ${what}`)
  else {
    console.log(`  FAIL  ${what}\n        wanted ${codes.join(',') || '(nothing)'}` +
                `\n        got    ${got.join(',') || '(nothing)'}`)
    failures++
  }
}

console.log('what each rule catches');
expect('a heading skip within the document', '# One\n\n### Three\n', ['BMX-W001'])
expect('an empty block with no head', ':card:\n:!card:\n', ['BMX-W002'])
expect('a link with an empty target', 'A [dead]() link.\n', ['BMX-W003'])

// BMX-W005 — indentation that contradicts the nesting. The interesting half of this rule is the
// negatives below: a flat document is correct and must stay quiet, or the rule flags every component
// star-burxt has ever written.
expect('a block indented to the wrong depth', ':a:\n  :b:\n      :c:\ntext\n      :!c:\n  :!b:\n:!a:\n', ['BMX-W005'])
expect('and one level too shallow', ':a:\n  :b:\n :c:\ntext\n :!c:\n  :!b:\n:!a:\n', ['BMX-W005'])

console.log('\nwhat it must NOT catch — correct code a warning would drive people to disable it over');
// A component's headings are relative to the page embedding it, so opening at `##` is correct. The
// rule is about a JUMP, never about starting at h1.
expect('a component opening at h2', '## Card\n\nBody.\n', [])
expect('h2 then h3, no jump', '## Two\n\n### Three\n', [])
// `html_element` carries `requires !html_is_void(tag) || len(children) == 0`, so a void element MUST
// have an empty body. Warning on it would flag every `<br>` and every form input.
expect('a void element with no head', ':br:\n:!br:\n', [])
expect('another void element', ':hr:\n:!hr:\n', [])
// Already exempt before the report, because a head carries the block's meaning.
expect('an empty block WITH a head', ':input: on:input=Msg.Typed(value)\n:!input:\n', [])
expect('props, which is a head and no body', ':props: order: Order\n:!props:\n', [])
expect('a block that contains a block',
  ':outer:\n:inner:\nbody\n:!inner:\n:!outer:\n', [])
expect('a real link', 'A [live](/page) link.\n', [])

console.log('\na host may replace the vocabulary');
expect('its own self-closing name is exempt', ':spacer:\n:!spacer:\n', [], { selfClosing: ['spacer'] })
expect('and an ordinary block is still flagged', ':card:\n:!card:\n', ['BMX-W002'],
  { selfClosing: ['spacer'] })
// The default list is HTML's, so replacing it un-exempts HTML's names — which is the point of
// replacing it, and worth pinning so nobody "fixes" it into a merge.
expect('replacing the list means br is no longer exempt', ':br:\n:!br:\n', ['BMX-W002'],
  { selfClosing: ['spacer'] })

console.log('\na document that does not parse');
// One error and no warnings. Style notes beside a refusal bury the refusal.
expect('reports nothing, because there is no tree to lint', 'Unterminated **bold\n', [])

console.log()
if (failures) { console.log(`${failures} failed`); process.exit(1) }
console.log('every rule fires where it should and stays quiet where it should')

// A document that does not indent at all is correct, and always was.
expect('a flat document', ':a:\n:b:\ntext\n:!b:\n:!a:\n', [])
// The step is the document's own: a file indenting by four is consistent, and telling its author that
// two is right would be this format having an opinion about whitespace.
expect('a four-space document is its own standard', ':a:\n    :b:\n        :c:\n        text\n        :!c:\n    :!b:\n:!a:\n', [])
expect('a correctly indented two-space document', ':a:\n  :b:\n    :c:\n    text\n    :!c:\n  :!b:\n:!a:\n', [])
// A one-liner does not open a level, so what follows it is not one level deeper.
expect('a one-liner beside a block', ':a:\n  :b: x :!b:\n  :c:\n  text\n  :!c:\n:!a:\n', [])
