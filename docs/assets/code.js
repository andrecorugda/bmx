// Colour `burxt` and `bmx` code blocks on a Jekyll site.
//
// **Why this exists rather than a Rouge lexer.** Rouge is Jekyll's highlighter and it knows neither
// language, so a ```burxt block ships as plain `<pre><code class="language-burxt">` — while the
// ```js block beside it comes out coloured. Every page that teaches Burxt or BMX has been showing
// its own language as grey text next to somebody else's language in colour.
//
// A Rouge lexer is the "proper" answer and it is written in Ruby, which is not installed on the
// machine these sites are written on — Jekyll only ever runs on the remote. A lexer nobody here can
// run is a lexer nobody here can test, and this project has been bitten by exactly that.
//
// **The decisions here are not invented.** Both languages already have a TextMate grammar, and the
// classes below map onto the scopes those grammars produce — so what an author sees on the site and
// what they see in their editor are the same decision made once. `editors/vscode/test/agrees.mjs`
// checks that claim against the real grammar rather than asserting it.
//
// No dependencies, no build step, ~10 KB. Runs after the DOM is ready, once, and does nothing if
// there is no code on the page.

(() => {
  'use strict';

  const escapeHtml = (s) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  const span = (cls, text) => (cls ? `<span class="t-${cls}">${escapeHtml(text)}</span>` : escapeHtml(text));

  // ---- Burxt -----------------------------------------------------------------------------------
  //
  // Order is the whole correctness story: a comment containing a keyword is a comment, and a string
  // containing `//` is a string. So comments and strings are consumed before anything else looks.

  const BURXT_KEYWORD = /^(?:if|else|while|match|return|for|in|break|continue|let|mutable|function|pure|class|enum|interface|region|use|const|external|public|private|requires|ensures|touches|decreases|allocates|as|impl|self|Ok|Error|Some|None)\b/;
  const BURXT_RESERVED = /^(?:fn|mut|impl|dyn|extern|struct|trait|record)\b/;
  const BURXT_BUILTIN = /^(?:print|print_error|len|byte_at|byte_as_string|push|read_file|to_string|old|divide_floor|divide_toward_zero|remainder|substring|write_file|write_bytes|argument|argument_count|truncate|hash|exit|bit_and|bit_or|bit_xor|bit_not|shift_left|shift_right_zeros|shift_right_sign|c_is_null|c_string_at|c_bytes_at|c_bytes_to|char_at|char_count|from_bytes|to_bytes|html_render|html_text|html_element|html_attr|bmx_parse|bmx_check|bmx_where)\b/;
  const BURXT_TYPE = /^(?:Decimal|Int|String|Bool|Option|Result|Json|Html|CPointer|CInt|CDouble|Handle)\b/;

  function burxt(src) {
    let out = '';
    let i = 0;
    while (i < src.length) {
      const rest = src.slice(i);

      // a comment runs to end of line, and nothing inside it is anything else
      if (rest.startsWith('//')) {
        const end = rest.indexOf('\n');
        const text = end < 0 ? rest : rest.slice(0, end);
        out += span('comment', text);
        i += text.length;
        continue;
      }

      // a string, with `{…}` interpolation shown as itself rather than as string
      if (rest[0] === '"') {
        let j = 1;
        while (j < rest.length && rest[j] !== '"') {
          if (rest[j] === '\\') j++;
          j++;
        }
        const text = rest.slice(0, Math.min(j + 1, rest.length));
        out += span('string', text);
        i += text.length;
        continue;
      }

      // a money or percent literal: $19.99, 8.25% — exact, and worth looking exact
      let m = /^(?:\$\d+(?:\.\d+)?|\d+(?:\.\d+)?%)/.exec(rest);
      if (m) { out += span('money', m[0]); i += m[0].length; continue; }

      m = /^\d+(?:\.\d+)?/.exec(rest);
      if (m) { out += span('number', m[0]); i += m[0].length; continue; }

      if (/^[A-Za-z_]/.test(rest)) {
        const word = /^[A-Za-z_][A-Za-z0-9_]*/.exec(rest)[0];
        let cls = null;
        if (BURXT_RESERVED.test(word)) cls = 'invalid';       // spellings that do not compile
        else if (BURXT_KEYWORD.test(word)) cls = 'keyword';
        else if (BURXT_BUILTIN.test(word)) cls = 'builtin';
        else if (BURXT_TYPE.test(word)) cls = 'type';
        else if (/^[A-Z]/.test(word)) cls = 'type';           // a user's class or enum
        else if (/^\s*\(/.test(rest.slice(word.length))) cls = 'call';
        out += span(cls, word);
        i += word.length;
        continue;
      }

      m = /^[{}()[\];,:.<>=+\-*/!&|]+/.exec(rest);
      if (m) { out += span('punct', m[0]); i += m[0].length; continue; }

      out += escapeHtml(rest[0]);
      i += 1;
    }
    return out;
  }

  // ---- BMX -------------------------------------------------------------------------------------
  //
  // Line-oriented, and in the same order the grammar uses: a fenced code block wins over
  // everything, because §5 says its content is never parsed — colouring a `{{` inside one would be
  // a lie the author cannot turn off.

  function bmxInline(line) {
    let out = '';
    let i = 0;
    while (i < line.length) {
      const rest = line.slice(i);

      // an escape, and only the five the format allows
      let m = /^\\[`*[{\\]/.exec(rest);
      if (m) { out += span('escape', m[0]); i += 2; continue; }

      // a code span before a slot: `{{ x }}` inside backticks is text
      m = /^`[^`]*`/.exec(rest);
      if (m) { out += span('raw', m[0]); i += m[0].length; continue; }

      // a slot. The delimiters are BMX's; the expression is the HOST's, so it is coloured as an
      // expression rather than as markup — which is the same split the grammar makes by leaving
      // `meta.slot.expression.bmx` for a host to inject into.
      m = /^\{\{(.*?)\}\}/.exec(rest);
      if (m) {
        out += span('slot-mark', '{{') + span('slot', m[1]) + span('slot-mark', '}}');
        i += m[0].length;
        continue;
      }

      // an inline block — deliberately not a slot, because a slot's value is escaped and this is a
      // call to something the host declared
      m = /^::([A-Za-z][A-Za-z0-9_-]*)\[(.*?)\]::/.exec(rest);
      if (m) {
        out += span('slot-mark', '::') + span('name', m[1]) + span('slot-mark', '[')
             + span('slot', m[2]) + span('slot-mark', ']::');
        i += m[0].length;
        continue;
      }

      // The markers are punctuation and the words are the emphasis — which is what every markdown
      // theme does, and what the grammar says: `punctuation.definition.bold.bmx` sits inside
      // `markup.bold.bmx`. Colouring the asterisks as bold too made them shout.
      m = /^\*\*([^*]+)\*\*/.exec(rest);
      if (m) {
        // The content recurses: the grammar includes `#slot` inside `#strong`, so `**{{ x }}**`
        // has a slot in it. `[^*]+` cannot contain another `*`, so this terminates.
        out += span('punct', '**') + '<span class="t-strong">' + bmxInline(m[1])
             + '</span>' + span('punct', '**');
        i += m[0].length;
        continue;
      }
      m = /^\*([^*]+)\*/.exec(rest);
      if (m) {
        out += span('punct', '*') + '<span class="t-em">' + bmxInline(m[1])
             + '</span>' + span('punct', '*');
        i += m[0].length;
        continue;
      }

      m = /^\[([^\]]*)\]\(([^)]*)\)/.exec(rest);
      if (m) {
        out += span('punct', '[') + span('link-text', m[1]) + span('punct', '](')
             + span('link', m[2]) + span('punct', ')');
        i += m[0].length;
        continue;
      }

      out += escapeHtml(rest[0]);
      i += 1;
    }
    return out;
  }

  function bmx(src) {
    const lines = src.split('\n');
    // **The guide step is the language's own, not a constant.** A BMX document indents by two —
    // `tools/fmt.py` decides that and the site's examples follow it — while a `burxt` block indents by
    // four. One shared number would draw a guide where neither language has a level.
    const out = [];
    let fence = null; // the ``` or ~~~ currently open, if any
    let comment = false; // inside a `<!-- … -->` that has not closed on an earlier line

    for (const line of lines) {
      if (fence !== null) {
        out.push(span('raw', line));
        if (line.trim() === fence) fence = null;
        continue;
      }

      // a comment, which may span lines. Tracked like a fence so its content is not painted as markup.
      if (comment) {
        out.push(span('comment', line));
        if (line.includes('-->')) comment = false;
        continue;
      }
      let m = /^(\s*)(<!--.*)$/.exec(line);
      if (m) {
        out.push(m[1] + span('comment', m[2]));
        if (!line.includes('-->')) comment = true;
        continue;
      }

      m = /^(\s*)(`{3,}|~{3,})(.*)$/.exec(line);
      if (m) {
        fence = m[2];
        out.push(m[1] + span('raw', m[2]) + span('info', m[3]));
        continue;
      }

      // a closer: :!name:
      m = /^(\s*)(:!)([A-Za-z][A-Za-z0-9_-]*)(:)([ \t]*)$/.exec(line);
      if (m) {
        out.push(m[1] + span('fence', m[2]) + span('name', m[3]) + span('fence', m[4]) + m[5]);
        continue;
      }

      // an opener: :name: head
      // The whitespace after the marker belongs to neither the name nor the head — the grammar's
      // `[ \t]*` eats it between captures, so a head starting one character early is a real
      // divergence and `agrees.mjs` caught it.
      // **a one-liner, both forms — tried before the two below.** `:name: -> [head] body :!name:` and
      // `:name: head :!name:`. Until 0.11.3 the trailing closer fell into the body or the head and was
      // painted as content: Andre noticed the closer was not styled, and in the EDITOR the same gap was
      // worse, because the grammar treated a one-liner as an opener and every line below it stayed
      // inside the block.
      m = /^(\s*)(:)([A-Za-z][A-Za-z0-9_-]*)(:)(?:([ \t]*)(->)([ \t]*)(\[)([^\]]*)(\])([ \t]*)(.*?)|([ \t]*)(.*?))([ \t]*)(:!)(\3)(:)([ \t]*)$/.exec(line);
      if (m) {
        const headHook = (s) => escapeHtml(s)
          .replace(/(\.)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-class">$1$2</span>')
          .replace(/(#)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-id">$1$2</span>');
        const closer = span('fence', m[16]) + span('name', m[17]) + span('fence', m[18]) + m[19];
        if (m[6]) {
          // delimited: the head is a head, and what follows the `]` is CONTENT
          out.push(m[1] + span('fence', m[2]) + span('name', m[3]) + span('fence', m[4]) + m[5]
                   + span('punct', m[6]) + m[7] + span('punct', m[8])
                   + (m[9] ? '<span class="t-head">' + headHook(m[9]) + '</span>' : '')
                   + span('punct', m[10]) + m[11]
                   + (m[12] ? bmxInline(m[12]) : '') + m[15] + closer);
        } else {
          // undelimited: there is no body, so everything before the closer is head
          out.push(m[1] + span('fence', m[2]) + span('name', m[3]) + span('fence', m[4]) + m[13]
                   + (m[14] ? '<span class="t-head">' + headHook(m[14]) + '</span>' : '')
                   + m[15] + closer);
        }
        continue;
      }

      // a delimited head: :name: -> [head] body      (0.9)
      m = /^(\s*)(:)([A-Za-z][A-Za-z0-9_-]*)(:)([ \t]*)(->)([ \t]*)(\[)([^\]]*)(\])([ \t]*)(.*)$/.exec(line);
      if (m) {
        let head = escapeHtml(m[9])
          .replace(/(\.)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-class">$1$2</span>')
          .replace(/(#)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-id">$1$2</span>');
        out.push(m[1] + span('fence', m[2]) + span('name', m[3]) + span('fence', m[4]) + m[5]
                 + span('punct', m[6]) + m[7] + span('punct', m[8])
                 + (m[9] ? '<span class="t-head">' + head + '</span>' : '')
                 + span('punct', m[10]) + m[11]
                 + (m[12] ? bmxInline(m[12]) : ''));
        continue;
      }

      m = /^(\s*)(:)([A-Za-z][A-Za-z0-9_-]*)(:)([ \t]*)(.*)$/.exec(line);
      if (m) {
        let head = m[6];
        // `.class` and `#id` are the only parts of a head BMX has an opinion about
        head = escapeHtml(head)
          .replace(/(\.)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-class">$1$2</span>')
          .replace(/(#)([A-Za-z][A-Za-z0-9_-]*)/g, '<span class="t-id">$1$2</span>');
        out.push(m[1] + span('fence', m[2]) + span('name', m[3]) + span('fence', m[4])
                 + m[5]
                 + (m[6] ? '<span class="t-head">' + head + '</span>' : ''));
        continue;
      }

      m = /^(\s*)(#{1,6})([ \t]+)(.*)$/.exec(line);
      if (m) {
        // `#inline` runs inside a heading in the grammar, so a slot in a heading is a slot.
        out.push(m[1] + span('punct', m[2]) + m[3]
                 + '<span class="t-heading">' + bmxInline(m[4]) + '</span>');
        continue;
      }

      m = /^(\s*)(>)([ \t]?)(.*)$/.exec(line);
      if (m) {
        out.push(m[1] + span('punct', m[2]) + m[3]
                 + '<span class="t-quote">' + bmxInline(m[4]) + '</span>');
        continue;
      }

      m = /^(\s*)([-*+]|\d{1,9}[.)])([ \t]+)(.*)$/.exec(line);
      if (m) { out.push(m[1] + span('punct', m[2]) + m[3] + bmxInline(m[4])); continue; }

      out.push(bmxInline(line));
    }
    // **Every line is boxed HERE, in one place, and that is the whole reason this is safe.**
    //
    // The loop above has 24 exits. star-burxt built the same thing with a wrapper called at each exit,
    // wrapped one of three, and got a gutter that numbered most of a panel and silently skipped the
    // rest — **numbers that stop at line 5 are worse than no numbers**, because the ones before it stop
    // meaning anything. This painter pushes exactly one entry per line, so wrapping the ARRAY cannot
    // miss an exit no matter how many are added later.
    //
    // `inline-block`, not `block`, and the newline stays OUTSIDE the box. star measured why: a
    // block-level line swallows the `\n`, and then what a reader copies depends on how a browser
    // rejoins block boundaries. Left between two inline-blocks it is still text, so the clipboard is
    // exactly the document — the same rule the display-indent follows. **Newlines are text,
    // indentation is padding, a line number is neither.**
    return out.join('\n');
  }

  /**
   * Wrap every line of painted HTML in one box, for the gutter and the indent guides.
   *
   * **One wrapper for both languages, at the only point they share.** The `bmx` painter has 24 exits
   * and `burxt` builds a single string character by character, so a wrapper called at each exit would
   * have to be right 25 times. star-burxt built exactly that, wrapped one of three exits, and got a
   * panel where the numbers stopped partway — **a gutter with unnumbered lines in it is worse than no
   * gutter**, because the numbers before the gap stop meaning anything. Applied to the finished string
   * it cannot miss an exit that does not exist yet.
   *
   * `inline-block`, not `block`, and the newline stays OUTSIDE the box — star measured why. A
   * block-level line swallows the `\n`, and what a reader copies then depends on how a browser rejoins
   * block boundaries. Left between two inline-blocks it is still text, so the clipboard is exactly the
   * document. **Newlines are text, indentation is padding, a line number is neither.**
   *
   * `step` is the language's own: a BMX document indents by two — `tools/fmt.py` decides that — and a
   * `burxt` block by four. One shared number would draw a guide where neither language has a level.
   */
  function boxLines(painted, step) {
    // **A blank line inherits the depth above it**, or the guide column breaks wherever a document
    // breathes — which is every real component. A blank line has no leading spaces to measure, so
    // measuring is the wrong question: what a reader wants to see is that the level continues.
    let carried = 0;
    return painted.split('\n').map((html) => {
      const text = html.replace(/<[^>]*>/g, '');
      // The depth comes from the PAINTED line's own leading spaces, which survive painting as text.
      const lead = /^(?:&nbsp;| )*/.exec(text)[0].length;
      const depth = text.trim() === '' ? carried : Math.min(8, Math.floor(lead / step));
      if (text.trim() !== '') carried = depth;
      return `<span class="cl${depth > 0 ? ' w' + depth : ''}">${html}</span>`;
    }).join('\n');
  }

  // ---- wiring ----------------------------------------------------------------------------------

  // Each language paints, and carries the indent step its own documents use.
  const LANGUAGES = { burxt: [burxt, 4], bmx: [bmx, 2] };

  function paint() {
    for (const [language, [fn, step]] of Object.entries(LANGUAGES)) {
      const blocks = document.querySelectorAll(
        `pre > code.language-${language}, pre.language-${language} > code`,
      );
      blocks.forEach((block) => {
        if (block.dataset.painted) return;
        // textContent, never innerHTML: the text arrives already escaped by Jekyll, and reading
        // the markup back would double-escape every `<` in a Decimal<2>.
        block.innerHTML = boxLines(fn(block.textContent), step);
        block.dataset.painted = '1';
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', paint, { once: true });
  } else {
    paint();
  }
})();
