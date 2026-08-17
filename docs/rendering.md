---
layout: default
title: Turning it into a page
---

{% raw %}
# Turning it into a page

There are two ways, they are not variants of each other, and the difference is the whole reason
BMX exists.

| | **Level 1 — render** | **Level 2 — generate** |
|---|---|---|
| When it runs | at request time | at build time |
| Slots resolved by | looking up expression **text** | **compiling** the expression |
| A slot naming a missing field | an error on the page | **a compile error** |
| A slot holding the wrong type | nobody notices | **a compile error** |
| Available in | any language | a language with types |

**Use level 2 wherever you can.** Level 1 exists because a document sometimes arrives at runtime;
level 2 exists because a template is the last place in most programs where nothing is checked.

---

## Level 1 — rendering at runtime

The document is data. You bind values by name and get HTML back.

```burxt
use "bmx/burxt/bmx.bx";
use "lib/files.bx";

function page(path: String) -> String touches files {
    let bindings: [Binding] = [
        bmx_bind("user.name", "Ada Lovelace"),
        bmx_bind("order.total", "$59.97"),
    ];
    match bmx_to_html(file_read(path), bindings) {
        Error(reason) => { return "<p>could not render</p>"; }
        Ok(html) => { return html; }
    }
}
```

`bmx_to_html` answers a `Result`, and it **refuses rather than guessing** in two cases you would
otherwise discover in production:

- **A slot with no binding is an error, never an empty string.** Every template language in wide
  use renders the empty string here, and that is how a page ships with a missing total nobody
  sees.
- **A link target with a disallowed scheme is refused.** `javascript:` is an attack that escaping
  cannot touch.

If you only need the tree — to walk it, or to render to something that is not HTML — `bmx_parse`
gives you `[Block]` and `bmx_json` gives you the AST the conformance suite compares.

---

## Level 2 — generating a typed view

The document becomes a **function**, and the compiler checks it.

```sh
burxt build burxt/examples/generate.bx -o bmx-generate
./bmx-generate receipt.bmx receipt_view "order: Order" "len(order.reference) > 0" > receipt_view.bx
```

Arguments: the document, the function name, the parameter list, then zero or more `requires`
clauses. **The signature comes from the command line and not from the document** — BMX has no
front matter, and a generator inventing one would be adding to the format from the host side.

From this document:

```bmx
# Receipt {{ order.reference }}

Thanks, **{{ order.customer }}** — {{ to_string(order.total) }}.
```

you get ordinary Burxt:

```burxt
// GENERATED from receipt.bmx by `bmx generate`. Do not edit.
use "lib/html.bx";

pure function receipt_view(order: Order) -> Html
    requires len(order.reference) > 0
{
    return html_element("article", [html_attr("class", "bmx")], [
        html_element("h1", [], [html_text("Receipt "), html_text(order.reference)]),
        html_element("p", [], [html_text("Thanks, "),
            html_element("strong", [], [html_text(order.customer)]),
            html_text(" — "), html_text(to_string(order.total)), html_text(".")]),
    ]);
}
```

Then use it like any function:

```burxt
use "types.bx";
use "receipt_view.bx";

print(html_render(receipt_view(order)));
```

### A document that repeats, branches, and declares itself

A block becomes real Burxt, which is why the compiler can see inside it:

```bmx
::: props order: Order
:::

# Receipt {{ order.reference }}

::: for line in order.lines
- {{ line.sku }} × {{ to_string(line.qty) }}
:::

::: if order.paid
Paid in full.
:::
```

```sh
./bmx-generate receipt.bmx receipt_view ""     # the props block supplies the signature
```

```burxt
pure function receipt_view(order: Order) -> Html
{
    let mutable kids: [Html] = [];
    let p_0_0: Int = push(kids, html_element("h1", [], [...]));
    for line in order.lines {
        let p_0_1_0: Int = push(kids, html_element("ul", [], [...]));
    }
    if order.paid {
        let p_0_2_0: Int = push(kids, html_element("p", [], [...]));
    }
    return html_element("article", [html_attr("class", "bmx")], kids);
}
```

**`::: for` is a real Burxt `for`.** Which means `line` inside it is a real `Line` with a real
type — so a typo in the loop body is a compile error naming the field, and money that would round
without a contract is refused *in there*. No other template language checks the body of a loop,
because no other one hands that body to a compiler that already knows the types.

A block whose name is not `for` or `if` is a **component**: it becomes a call, taking its head as
text and its children as `[Html]`. An unknown name is then an unknown function, which the compiler
reports along with the ones that do exist.

### What the compiler catches

None of this is implemented by the generator. It emits ordinary code and the **language** does the
rest — which is the boundary between format and host paying off.

**A field that does not exist:**

```
error: `Order` has no field named `custmer`. Its fields are: reference: String,
customer: String, total: Decimal<2, RoundHalfEven>, …
```

**A slot that is not a `String`** — `html_text` takes a `String`, and `to_string` of a `String` is
refused, so the conversion is written **in the document** where a reviewer sees it:

```
error: in the call to `html_text`, argument 1 must be String,
       but it has type Decimal<2, RoundHalfEven>
```

**Money that would silently re-round**, inside a view:

```
error: this multiplication of Decimal<2> by Decimal<2> has an exact product with 4
decimal places, and reaching Decimal<2> means rounding it. Say how —
Decimal<2, RoundHalfEven> — or take the exact answer with Decimal<4>.
```

That last one is the point. **A `Decimal<2, RoundHalfEven>` keeps its scale and its tie rule all
the way to the tag.** Every other web stack loses money-correctness at the template boundary,
because every other template language is stringly-typed there.

**A dangerous link target**, refused at build time before any page exists:

```
BMX-G001: refused a link target whose scheme is not http, https or mailto: javascript:steal
```

### And the promise is diffable

A generated view is a function with a signature, so `burxt review` will tell you when a change to
a document weakened it:

```
WEAKENED  badge   lost `requires len(label) > 0`
```

Nothing else in the ecosystem has mechanical semver for a component. It comes free here because a
view is not a special kind of thing.

---

## Serving it

A Burxt binary behind nginx serves pages with no listener, no sockets and no concurrency — CGI,
the interface every web server has spoken since 1993:

```burxt
use "lib/cgi.bx";

let request: Request = cgi_request();
let sent: Int = cgi_respond_html(200, receipt_view(order));
```

`cgi_respond_html` takes an `Html`, never a `String` — a String reaching it would be a page nobody
escaped.

## Writing a document into a Burxt string

You can, and you will not enjoy it:

```burxt
print(shown(bmx_to_html("Hi \{\{ user.name \}\}.", bindings)));
```

Every brace needs escaping, because `{` opens a Burxt interpolation. It compiles and it is
correct; it is unreadable, which is why documents live in `.bmx` files.
{% endraw %}
