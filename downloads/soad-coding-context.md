# SØAD Framework — Coding Context

SØAD is a convention-over-configuration MVC web framework on the JVM. Controllers (called **Transactions**) are written in **Jython** (Python 2.7 syntax on Java), views in **Handlebars.java**, models via **ActiveJDBC** (auto-generated from DB tables). Use this file as context when writing transaction code, view templates, or SQL.

**Naming:** Canonical spelling is **SØAD**. "SOAD" and "soad" are accepted shorthand — treat them as identical on input. Use **SØAD** in generated prose, docs, and comments. Keep lowercase `soad` as-is in code identifiers, module names, and file paths — do NOT "correct" those.

---

## HARD RULES (DO NOT VIOLATE)

These break code silently if ignored. They always apply.

- **Language is Jython = Python 2.7 syntax**, running on the JVM (not CPython).
- **DO NOT use f-strings.** `f"Hi {name}"` does NOT work. Use `%` (`"Hi %s" % name`) or `.format()` (`"Hi {}".format(name)`) — both work.
- **`except Exception as e:` IS allowed** (verified in this Jython build) — use it.
- **`print()` works**, but in containers its output may not reach the IDE log. Prefer `Log.info(ctx, "...")` for anything that must be visible.
- **DO NOT use pip or any CPython package** (`requests`, `numpy`, `pandas`, etc.) — they do not exist here.
- **Add libraries as Java JARs only.** Import Java classes directly, e.g. `from java.io import File`, `from java.time import LocalDateTime`. Bundled: Guava, Apache Commons (lang3, io, text), Apache POI (Office docs), openpdf (PDF). Full version list in the Utilities section.
- **DO NOT write any routing/config file.** Routing is convention-based from folder/file/method names.
- **DO NOT hand-write Model classes.** They are auto-generated from DB tables; just `from models import Capitalizedname`. The class name is the **table name with the first letter capitalized and the rest exact — NO English inflection.** SØAD disables ActiveJDBC's default pluralization, so `persons` → `Persons` (not `Person`), `categories` → `Categories` (not `Category`). Match the table spelling exactly.
- **`saveIt()` vs `insert()`:** auto-generated id → `saveIt()` for both insert and update. **Manually set id (e.g. UUID) → `insert()` for a NEW record, `saveIt()` for updates.** Calling `saveIt()` on a manually-id'd new record silently runs an UPDATE and inserts nothing.
- **DO NOT set `created_at` or `updated_at`.** If a table has these (Timestamp) columns, ActiveJDBC auto-manages them — setting them in code throws an error. To control timestamps yourself, name the columns `created_date`/`updated_date` instead (not auto-managed) and set those.
- **Every action method takes `ctx`:** `def view(self, ctx):`. All public methods on a transaction class are reachable as URL actions.
- **Default class base is `object`:** `class Foo(object):`. Layout/base inheritance is optional.
- **Auto-render: if a method never assigns `ctx.go_to`, the framework renders the default view `_{code}/{code}.html` automatically.** Do NOT call `render.as_view` just to render the default view — leave `ctx.go_to` unset. Assign `ctx.go_to` ONLY for something else: a *different* view (`render.as_view(ctx, "other")`), JSON, a file, or a redirect string. Prefer the default view first; add extra `.html` views only when a transaction needs more than one screen.

---

## Routing

URL pattern: **`/t/{group}/{code}/{action}`**
- `/t` fixed prefix · `{group}` folder/module · `{code}` = `.py` filename AND class name (capitalized) · `{action}` = method, **defaults to `view`** if omitted.
- `/t/web/home` → `web/home.py`, class `Home`, method `view()`
- `/t/app/user/edit?id=5` → `User.edit()`, read `id` from request

On disk (transaction `example/contact`):
```
example/
  contact.py            # class Contact
  _contact/             # views: underscore + code name
    contact.html        # default view (matches code name)
    edit.html           # optional extra views
```
Class name = code with first letter capitalized (`address_book` → `Address_book`).

### Imports

- **Built-in SØAD utilities and models — no prefix:** `from utils import render`, `from models import Members`.
- **Another custom transaction / utility / layout — `default.<group>.<code>` prefix** (imports its Capitalized class from the transaction at `<group>/<code>.py`):
  - `from default.org.members import Members` — the `org/members` transaction
  - `from default.utils.member_number_generator import MemberNumberGenerator` — a `utils/member_number_generator` transaction used as a helper
  - `from default.org.layout import Layout` — a shared layout is just a normal transaction other transactions inherit

  Pattern: `default.<group>.<code>` → the Capitalized class in `<group>/<code>.py`. You don't manage these paths yourself — `create_transaction(group, code)` lays them out; this is only how one transaction references another.

---

## Transaction skeleton

```python
from models import Contact

class Contact(object):
    def view(self, ctx):                      # GET, default action
        ctx.output["contacts"] = Contact.findAll().orderBy("name ASC")
        # No ctx.go_to assignment => auto-renders _contact/contact.html

    def save(self, ctx):
        """POST"""                            # docstring marks POST-only
        r = ctx.getRequest()
        id = r.getParameter("id")
        c = Contact.findById(id) if id else Contact()
        c.set("name", r.getParameter("name"))
        c.saveIt()
        ctx.go_to = "/t/example/contact"      # PRG: string => redirect
```
`render` is only imported when a method needs a non-default response (a different view, JSON, file, PDF). The skeleton above needs no `render` import.

---

## ctx (WebContext)

- `ctx.getRequest()` / `ctx.getResponse()` — servlet request/response
- `ctx.output` — map of data passed to the view
- `ctx.go_to` — the response. **Unset → auto-renders the default view `_{code}/{code}.html`**; **string → redirect** (`sendRedirect`); **`render.*` result → that rendered output**
- `ctx.ctxPath` — app context path; prefix links/redirects with it across environments
- `ctx.getGroup()`, `ctx.getCode()`, `ctx.getMethod()`, `ctx.getAppName()`
- Read input: `ctx.getRequest().getParameter("name")`
- Session: `ctx.getRequest().getSession(True)`

---

## Models (ActiveJDBC — auto-generated)

Never define a model class — import it by its table name with the **first letter capitalized and the rest kept exactly as-is**. Table `contact` → `Contact`; `hr_employee` → `Hr_employee`; `persons` → `Persons`; `categories` → `Categories`.

**DO NOT apply English inflection.** Stock ActiveJDBC maps `persons` → `Person` and `boxes` → `Box` by default — **SØAD disables this and uses strict exact naming.** So `persons` is `Persons` (NOT `Person`), `categories` is `Categories` (NOT `Category`), `people` is `People`. Always the literal table name with a capital first letter, including any plural `s`.

```python
from models import Contact

c = Contact()                                  # create
c.set("name", "John"); c.set("email", "j@x.com")
c.saveIt()

Contact.findAll()                              # read
Contact.findById(1)
Contact.where("name LIKE ?", "%John%")
Contact.findAll().orderBy("name ASC").limit(10)
Contact.findAll().orderBy("grade DESC, name ASC")

c = Contact.findById(1)                        # update
c.set("name", "Jane"); c.saveIt()

c.delete()                                     # delete

Contact.findAll().toMaps()                     # list of dict — handy for render.as_json

# Single record by condition: use Model.first(...), NOT .where(...).first()
c = Contact.first("name = ?", "John")          # correct
# c = Contact.where("name = ?", "John").first()  # WRONG — LazyList has no .first()
```

The framework wraps each request in a DB transaction: **auto-commit on success, auto-rollback on any exception.** Do NOT manage transactions manually. To force a rollback, raise an exception.

**Auto-managed timestamps.** ActiveJDBC treats `created_at` and `updated_at` (Timestamp columns) as magic: it sets `created_at` once on insert and `updated_at` on every update, automatically.
- **DO NOT set `created_at`/`updated_at` in code** — `obj.set("created_at", ...)` throws an error in SØAD; ActiveJDBC owns them.
- To control timestamps yourself, name the columns `created_date`/`updated_date` (or anything non-magic) — these are NOT auto-managed, so set them normally (`obj.set("created_date", LocalDateTime.now())`). **This is the recommended default.**

**saveIt() vs insert() — IDs.** ActiveJDBC picks INSERT vs UPDATE by whether the record looks new:
- **Auto-generated id** (`AUTO_INCREMENT`) → `saveIt()` for both create and update.
- **Manually set id** (e.g. UUID) → `insert()` for a NEW record, `saveIt()` for updates. Calling `saveIt()` on a new manually-id'd record runs an UPDATE that matches nothing — row silently never inserted, no error.

```python
from java.util import UUID

m = Members()
m.set("id", str(UUID.randomUUID()))
m.set("name", "John")
m.insert()                       # correct: INSERT (manual id, new record)
# m.saveIt()  # WRONG: UPDATE, inserts nothing

# Add/edit in one method with manual ids:
if record_id:
    record = Members.findById(record_id); new_record = False
else:
    record = Members(); record.set("id", str(UUID.randomUUID())); new_record = True
record.set("name", "value")
record.insert() if new_record else record.saveIt()
```

---

## SQL & Schema changes

**You cannot run DDL or write `.sql` files** — you have no SQL tool, and `write_file` only accepts a transaction's `<code>.py` and `.html` views. So when a task needs a new table or column:

- **Show the SQL as a fenced `sql` code block in your reply.** Do NOT try to stage it as a file — that call is rejected.
- Tell the developer to **run it in the IDE SQL editor**, then **Introspect** to regenerate the models. In-IDE schema changes regenerate models automatically; only external changes need a manual Introspect.
- One logical change per block (a `CREATE` or an `ALTER`) so they can be run in order.
- **Seed/sample data:** provide it the same way (a code block) only when the user explicitly asks — never by default.

Rules for `CREATE TABLE` so the auto-generated model aligns:

- **Every table MUST have a PK column named `id`** — typically `INT PRIMARY KEY AUTO_INCREMENT`.
- **Model class name = table name with first letter capitalized, rest exactly as-is. NO inflection** — `persons` → `Persons` (not `Person`), `categories` → `Categories`. SØAD disables ActiveJDBC's default pluralization.
- **A BLOB column auto-expands into THREE columns.** `resume` (BLOB) → `resume`, `resume_fn`, `resume_ft`. Do NOT manually add the `_fn`/`_ft` columns.
- Prefix table names by group/module (e.g. `hr_`) for maintainability.
- After schema changes **outside** the IDE, run **Introspect** to regenerate models. In-IDE changes regenerate automatically.

Supported types: `VARCHAR(n)`, `TEXT`, `MEDIUMTEXT`, `INT`, `BIGINT`, `BIT`, `DECIMAL(n,d)`, `DATE`, `DATETIME`, `TIME`, `BLOB`, `MEDIUMBLOB`.

**MySQL → Java type mapping** (use correct Java type in `.set()` and reads):

| MySQL | Java type |
|---|---|
| VARCHAR / TEXT / MEDIUMTEXT | String |
| INT | Integer |
| BIGINT | java.math.BigInteger |
| BIT | Boolean |
| DECIMAL | java.math.BigDecimal |
| DATE | java.sql.Date |
| DATETIME | **java.time.LocalDateTime** |
| TIME | java.sql.Time |
| BLOB / MEDIUMBLOB | byte[] |

```python
from java.time import LocalDateTime
obj.set("created_date", LocalDateTime.now())
```

Example `CREATE TABLE` (show this in your reply for the developer to run):
```sql
CREATE TABLE contact (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    contact_no VARCHAR(20),
    email VARCHAR(100),
    created_date DATETIME,
    updated_date DATETIME
);
```
→ auto-generates model class `Contact`. A later change is a separate `ALTER` block:
```sql
ALTER TABLE contact ADD COLUMN company VARCHAR(120);
```

---

## Render methods (`from utils import render`)

**First: you often don't need `render` at all.** If a method leaves `ctx.go_to` unset, the framework auto-renders the default view `_{code}/{code}.html`. Use the methods below only to return something *other* than the default view, assigning the result to `ctx.go_to`.

```python
render.as_view(ctx, view, group=None, code=None)   # Handlebars HTML (most common)
render.as_json(ctx, obj=None)                        # JSON; defaults to ctx.output
render.as_html(ctx, code=None)                       # raw HTML file, no Handlebars
render.as_string(ctx, text)                          # raw string/HTML
render.as_file(ctx, file, content_type, filename=None, attachment=True)
render.as_blob(ctx, data, content_type, filename, attachment=False)  # filename required
render.as_pdf(ctx, view, group=None, code=None, filename=None, attachment=False)
```

- `as_view(ctx, "home")` renders `_home/home.html` in the current group. Pass `group=`/`code=` to render a view from another transaction.
- **`render.as_view(...)` returns a callable.** Assign to `ctx.go_to` for normal rendering. To get the HTML **as a string** (email body, PDF input), call it with a trailing `()`:
  ```python
  html = render.as_view(ctx, "invoice")()   # note the extra ()
  ```
- `as_json` with a model list: `render.as_json(ctx, Contact.findAll().toMaps())`.
- `as_file` — `attachment=False` displays inline (e.g. show an image in browser).
- `as_pdf` — template must be well-formed XHTML (openpdf-backed HTML→PDF).

---

## Views (Handlebars.java)

Views are HTML files in the `_{code}/` folder, populated from `ctx.output`. **The default view `_{code}/{code}.html` renders automatically when a method leaves `ctx.go_to` unset** — a simple `view()` needs no `render` call. Call `render.as_view(ctx, "other")` only to render a *different* view. Generated pages are **full standalone HTML** (`<!DOCTYPE html>` … `</html>`) unless using a layout. Use `{{ctxPath}}` for links; inside `{{#each}}` use `{{../ctxPath}}`.

```html
<!DOCTYPE html>
<html>
<head>
  <title>{{page_title}}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <div class="container py-4">
    {{#if contacts}}
      <ul>
        {{#each contacts}}
          <li>{{name}} — {{email}}
            <a href="{{../ctxPath}}/t/example/contact/edit?id={{id}}">Edit</a>
          </li>
        {{/each}}
      </ul>
    {{else}}
      <div class="alert alert-info">No items found</div>
    {{/if}}
  </div>
</body>
</html>
```

### Built-in & logical helpers

`if`, `else`, `unless`, `each`, `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `and`, `or`, `not`, `in`.

Block form and inline-condition form both work:
```html
{{#eq status "pending"}}<span>Pending</span>{{else}}<span>Active</span>{{/eq}}
{{#if (eq role "admin")}}<p>Admin</p>{{/if}}
{{#if (in user_role_id allowed_roles)}}Granted{{else}}Denied{{/if}}
```
Use `{{#eq}}` for equality — **`{{#if_eq}}` does NOT exist in SØAD**, do not use it. Inside `{{#each}}`, current item is `{{this}}`.

**No `range` helper.** Build the list in the transaction and loop over it:
```python
ctx.output["page_numbers"] = list(range(1, total_pages + 1))
```
```html
{{#each page_numbers}}<a href="?page={{this}}">{{this}}</a>{{/each}}
```

### SØAD custom helpers

**`ref_lookup`** — fetch a column value from a table by key:
```html
{{ref_lookup user.id table="user" label="login_id" value="id"}}
```
`label` defaults to `name`, `value` defaults to `id`. Multiple labels: `label="name|email"`. Inside a loop: `{{ref_lookup this.id table="user_details" label="full_name" value="user_id"}}`.

**`select` / `option`** — dropdown from a table:
```html
{{select table="countries" selected=selected_country label="name" value="code"}}
```
Params: `table`, `refs`, `filter="active=1"`, `id`, `name`, `class`, `label`, `value`, `selected`, `required`, `readonly`, `sel_text` (placeholder, default "Please Select"). Use `{{option ...}}` for just the `<option>`s inside your own `<select>`.

**`dateFmt`** — format a date (default `dd/MM/yyyy`): `{{dateFmt registration_date "yyyy-MM-dd"}}`.

**`html`** — sanitize text, newlines → `<br>`, auto-link URLs: `{{html content}}`.

**`session`** — read a session attribute: `{{session "user_id"}}`.

**`get`** — read a `ctx.output` key with spaces/special chars: `{{get "complex key-name"}}`.

**`i18n`** — localized string: `{{i18n "welcome.message"}}`. Set locale via session attribute `__locale__`; strings live in `messages.properties` / `messages_ms.properties`.

**`length` / `size`** — element count of a list/collection/array (same helper, two names): `{{length items}}`, `{{#if (gt (size items) 0)}}...{{/if}}`. Missing/`null` returns `0`. Handlebars templates have **no method-call syntax** — `{{items.size()}}` / `{{products.size()}}` is **NOT valid** and will fail to render; always call the helper instead: `{{size items}}` (or `{{length items}}`), never `{{items.size()}}`.

### Edit-form patterns (both valid)

**A. Reuse the list view** — one view shows list + form; `edit` loads the record then calls `view`. Good for simple screens:
```python
def edit(self, ctx):
    ctx.output["contact"] = Contact.findById(ctx.getRequest().getParameter("id"))
    self.view(ctx)
```

**B. Separate form view** — dedicated `form` action/template for add+edit, list stays clean. Better for large forms:
```python
def form(self, ctx):
    id = ctx.getRequest().getParameter("id")
    if id:
        ctx.output["item"] = Model.findById(id)
    ctx.go_to = render.as_view(ctx, "form")
```
Either way, a single `save` handles both insert (no id) and update (id present), then PRG-redirects.

### Page layout (OPTIONAL)

Default is no layout. To share a header/footer, write a layout as a **normal transaction** (e.g. an `org/layout` transaction) whose class implements `page_layout(self, ctx)`, and have other transactions inherit it. **Both a 2-tuple `(group, code)` and a 3-tuple `(group, code, view)` are valid** (the 2-tuple defaults the view name):
```python
# org/layout.py  — the layout transaction
from utils import render
class Layout(object):
    def page_layout(self, ctx):
        return ("org", "layout")          # or ("org", "layout", "layout")
```
```python
# org/dashboard.py  — a page that uses the layout
from default.org.layout import Layout     # import the layout transaction's class
class Dashboard(Layout):                  # inherit layout (+ its shared helper methods)
    def view(self, ctx):
        ctx.output["page_title"] = "Dashboard"   # ctx.go_to unset => auto-render, wrapped by layout
```
Layout HTML uses placeholders `{{&title}}`, `{{&head}}`, `{{&body}}`; the page view's content is injected into `{{&body}}`. The page template holds only its own content; the layout supplies header/nav/footer. Inheriting the layout class also shares helper methods (e.g. an auth check) across transactions.

---

## File Upload

The form needs `method="post"` and `enctype="multipart/form-data"`. SØAD exposes **three** request parameters per `<input type="file" name="X">`:

- `X` → file content as `byte[]`
- `X_ft` → MIME type (e.g. `image/png`)
- `X_fn` → original filename

```python
from utils import render
from java.io import File
from com.google.common.io import Files

class Image(object):
    def upload(self, ctx):
        """POST"""
        request = ctx.getRequest()
        content = request.getParameter("photo")      # byte[]
        ftype   = request.getParameter("photo_ft")
        fname   = request.getParameter("photo_fn")

        if not content:
            ctx.output["message"] = "Please select a file"
            ctx.go_to = render.as_view(ctx, "upload_status")
            return

        if ftype not in ["image/png", "image/jpeg"]:
            ctx.output["message"] = "Only PNG and JPEG allowed"
            ctx.go_to = render.as_view(ctx, "upload_status")
            return

        Files.write(content, File("/tmp/uploads/" + fname))
        ctx.output["message"] = "Uploaded: " + fname
        ctx.go_to = render.as_view(ctx, "upload_status")
```
Validate type (`_ft`) and size (`len(content)`) before saving. To store in the DB instead, use a BLOB column and serve back with `render.as_blob(ctx, content, ftype, fname, attachment=False)`.

---

## Logging (`from sufia.util import Log`)

```python
from sufia.util import Log

Log.info(ctx, "message")
Log.debug(ctx, "params: %s" % ctx.getRequest().getParameterMap())
Log.warn(ctx, "warning")
Log.error(ctx, "failed: %s" % str(e))   # optional 3rd arg: exception object
Log.print(ctx, "same as info")
Log.trace(ctx, "very detailed")
```
Prefer `Log.*` over `print()`. Use `%` formatting (never f-strings). Common error pattern:
```python
try:
    ...
except Exception as e:
    Log.error(ctx, "Error: %s" % str(e))
    raise e      # re-raise triggers DB rollback
```

---

## Utilities

**Email (`from utils import mailer`):**
```python
mailer.send(sender, receiver, subject, content,
            cc=[], bcc=[], html=False, attachment=[], reply_to=None)
# HTML body from a view:
body = render.as_view(ctx, "welcome_email")()   # trailing ()
mailer.send("from@x.com", "to@x.com", "Subject", body, html=True)
```

**PDF (`from utils import pdf`):**
```python
from utils import pdf, render
html = render.as_view(ctx, "invoice")()        # XHTML string
pdf.generate(html, "/tmp/invoice.pdf")
# Stream to browser instead:
ctx.go_to = render.as_pdf(ctx, "invoice", filename="invoice.pdf", attachment=True)
```

**Bundled Java helpers:**
- File IO: `from com.google.common.io import Files` → `Files.write(bytes, File(path))`, `Files.toString(file, "UTF-8")`
- Base64: `from com.google.common.io import BaseEncoding` → `BaseEncoding.base64().encode(...)`
- Stream: `from com.google.common.io import ByteStreams` → `ByteStreams.copy(in, out)`
- Import Java classes directly; do NOT use pip. Need something else? Drop a JAR into `/webapp/WEB-INF/lib/`.

**Bundled JARs (use when relevant):**
- **guava-33.4.0-jre** — collections, caching, I/O, strings (`com.google.common.*`)
- **commons-io-2.15.1** — file/stream utilities (`org.apache.commons.io.*`)
- **commons-lang3-3.14.0** — core lang utilities (`org.apache.commons.lang3.*`)
- **commons-text-1.11.0** — text processing (`org.apache.commons.text.*`)
- **poi-5.4.0** — Apache POI: Excel, Word, PowerPoint (`org.apache.poi.*`)
- **openpdf-2.0.3** — PDF generation (backs `utils.pdf` / `render.as_pdf`)

---

## Integrations

### JSON API
```python
from utils import render
from models import Product

class Api(object):
    def products(self, ctx):
        ctx.go_to = render.as_json(ctx, Product.findAll().toMaps())

    def create(self, ctx):
        """POST"""
        r = ctx.getRequest()
        p = Product()
        p.set("name", r.getParameter("name"))
        p.saveIt()
        ctx.go_to = render.as_json(ctx, {"status": "ok", "id": p.get("id")})
```

### AJAX (jQuery — bundled)
```html
<script>
$("#load").on("click", function () {
  $.getJSON("{{ctxPath}}/t/api/products", function (data) {
    $("#list").empty();
    $.each(data, function (i, p) { $("#list").append("<li>" + p.name + "</li>"); });
  });
});
</script>
```
For POSTs: `$.post("{{ctxPath}}/t/api/create", {name: "X"}, cb, "json")`.

### htmx (bundled)
```html
<button hx-get="{{ctxPath}}/t/app/todo/count" hx-target="#out" hx-swap="innerHTML">
  Refresh
</button>
<div id="out"></div>
```
```python
def count(self, ctx):
    n = Todo.where("done = ?", False).size()
    ctx.go_to = render.as_string(ctx, "<span>%d open</span>" % n)
```
Return just the HTML fragment, not a full page.

### DataTables (bundled)
```html
<table id="grid" class="table">
  <thead><tr><th>Name</th><th>Email</th></tr></thead>
  <tbody>
    {{#each contacts}}
    <tr><td>{{name}}</td><td>{{email}}</td></tr>
    {{/each}}
  </tbody>
</table>
<link href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css" rel="stylesheet">
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>
<script>$(function () { $("#grid").DataTable(); });</script>
```
For large datasets use server-side mode, pointing `ajax` at a JSON transaction.

### Excel export (Apache POI — bundled)
```python
from org.apache.poi.xssf.usermodel import XSSFWorkbook
from java.io import ByteArrayOutputStream

class Report(object):
    def export(self, ctx):
        wb = XSSFWorkbook()
        sheet = wb.createSheet("Sales")
        sheet.createRow(0).createCell(0).setCellValue("Product")
        rows = Sale.findAll()
        i = 1
        for s in rows:
            row = sheet.createRow(i)
            row.createCell(0).setCellValue(s.get("product"))
            i += 1
        out = ByteArrayOutputStream()
        wb.write(out); wb.close()
        ctx.go_to = render.as_blob(
            ctx, out.toByteArray(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "report.xlsx", attachment=True)
```

---

## Generating a Complete Application

When asked to build an app or feature, **always produce in this order:**

1. **SQL** (only if a table/column is needed) — as a fenced `sql` code block in your reply; tell the user to run it in the IDE SQL editor, then Introspect. You cannot write `.sql` files or run DDL.
2. **Transaction `.py`** — staged via `write_file` as `{code}.py`, with all CRUD actions.
3. **The HTML views** — the default `_{code}/{code}.html` plus any extra views, each staged as its own `.html` file.

Rules:
- One transaction class per logical entity; all CRUD actions as methods on it.
- **Prefer the default view.** `view()` leaves `ctx.go_to` unset and auto-renders `_{code}/{code}.html`. Add extra `.html` views (rendered with `render.as_view(ctx, "name")`) only for additional screens like a separate form.
- Full standalone HTML pages (no layout by default); link Bootstrap from CDN.
- Reads are GET; create, update, delete are **POST** with `"""POST"""` docstring + PRG redirect.
- A single `save` handles both insert (no id) and update (id present).
- **No built-in flash scope** — pass messages via `?msg=saved` query param by default. Only implement a session-based flash mechanism if the user explicitly asks (see Flash Messages below).
- Delete is a POST form with a JS `confirm()`, never a bare link.
- Plain Bootstrap table for lists; DataTables only if the user wants sort/search.

### Golden Template — Todo CRUD

The list is the **default view** (`_todo/todo.html`, auto-rendered, no render call). The form is an **extra view** (`_todo/form.html`, rendered explicitly).

**SQL** (show as a code block; the developer runs it in the IDE SQL editor, then Introspect):
```sql
CREATE TABLE todo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    done BIT DEFAULT 0,
    created_date DATETIME
);
```

**`app/todo.py`:**
```python
from utils import render
from models import Todo
from java.time import LocalDateTime

class Todo(object):
    def view(self, ctx):                       # GET — list (default view)
        ctx.output["todos"] = Todo.findAll().orderBy("created_date DESC")
        ctx.output["msg"] = ctx.getRequest().getParameter("msg")
        # ctx.go_to unset => auto-renders _todo/todo.html

    def form(self, ctx):                       # GET — add/edit form (extra view)
        id = ctx.getRequest().getParameter("id")
        if id:
            ctx.output["todo"] = Todo.findById(id)
        ctx.go_to = render.as_view(ctx, "form")    # non-default view => explicit

    def save(self, ctx):                       # POST — insert or update
        """POST"""
        r = ctx.getRequest()
        id = r.getParameter("id")
        todo = Todo.findById(id) if id else Todo()
        todo.set("title", r.getParameter("title"))
        todo.set("done", r.getParameter("done") == "on")
        if not id:
            todo.set("created_date", LocalDateTime.now())
        todo.saveIt()
        ctx.go_to = "/t/app/todo?msg=saved"

    def delete(self, ctx):                     # POST — delete
        """POST"""
        todo = Todo.findById(ctx.getRequest().getParameter("id"))
        if todo:
            todo.delete()
        ctx.go_to = "/t/app/todo?msg=deleted"
```

**`_todo/todo.html`** (default view — filename matches the code):
```html
<!DOCTYPE html>
<html>
<head>
  <title>Todos</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <div class="container py-4">
    <h1>Todos</h1>
    {{#if msg}}<div class="alert alert-success">{{msg}}</div>{{/if}}
    <a href="{{ctxPath}}/t/app/todo/form" class="btn btn-primary mb-3">Add Todo</a>
    {{#if todos}}
    <table class="table">
      <thead><tr><th>Title</th><th>Done</th><th></th></tr></thead>
      <tbody>
        {{#each todos}}
        <tr>
          <td>{{title}}</td>
          <td>{{#if done}}Yes{{else}}No{{/if}}</td>
          <td>
            <a href="{{../ctxPath}}/t/app/todo/form?id={{id}}" class="btn btn-sm btn-secondary">Edit</a>
            <form action="{{../ctxPath}}/t/app/todo/delete" method="post" class="d-inline"
                  onsubmit="return confirm('Delete this todo?')">
              <input type="hidden" name="id" value="{{id}}">
              <button class="btn btn-sm btn-danger">Delete</button>
            </form>
          </td>
        </tr>
        {{/each}}
      </tbody>
    </table>
    {{else}}
    <div class="alert alert-info">No todos yet.</div>
    {{/if}}
  </div>
</body>
</html>
```

**`_todo/form.html`:**
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{#if todo}}Edit{{else}}Add{{/if}} Todo</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
  <div class="container py-4">
    <h1>{{#if todo}}Edit{{else}}Add{{/if}} Todo</h1>
    <form action="{{ctxPath}}/t/app/todo/save" method="post">
      <input type="hidden" name="id" value="{{todo.id}}">
      <div class="mb-3">
        <label class="form-label">Title</label>
        <input type="text" name="title" class="form-control" value="{{todo.title}}" required>
      </div>
      <div class="form-check mb-3">
        <input type="checkbox" name="done" class="form-check-input" {{#if todo.done}}checked{{/if}}>
        <label class="form-check-label">Done</label>
      </div>
      <button class="btn btn-primary">Save</button>
      <a href="{{ctxPath}}/t/app/todo" class="btn btn-link">Cancel</a>
    </form>
  </div>
</body>
</html>
```

### Flash messages (OPTIONAL — only when asked)

If the user wants messages that survive one redirect then disappear (not in the URL), implement on the session via a shared `Base` class. The read-**then**-remove order makes it show exactly once:

```python
class Base(object):
    def set_flash(self, ctx, text):
        ctx.getRequest().getSession(True).setAttribute("flash", text)

    def get_flash(self, ctx):
        session = ctx.getRequest().getSession(True)
        msg = session.getAttribute("flash")
        session.removeAttribute("flash")       # remove after reading
        ctx.output["flash"] = msg
```
Call `self.set_flash(ctx, "Saved")` before the redirect; `self.get_flash(ctx)` at the start of the next GET; show `{{flash}}` in the view. Transaction must inherit `Base`: `class Todo(Base):`. If also using a page layout, put both `page_layout` and flash helpers on the same `Base` class.
