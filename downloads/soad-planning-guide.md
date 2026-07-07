# SØAD Planning Guide

**Read this together with `SOAD-context-coding-full.md`.** That file teaches you the
SØAD framework (Jython transactions, Handlebars views, ActiveJDBC models, routing,
hard rules). *This* file tells you how to turn a request into a **build plan** that a
second AI — the **SØAD IDE agent** — will implement.

You are the *architect*. You do not write the final code here; you produce a clear,
staged plan. The agent is the *builder*: it reads your plan, generates the
transactions, and a human approves each change. Plan so that hand-off is smooth.

---

## How the builder works (plan within these constraints)

- **It builds one transaction at a time**: create → write the `<code>.py` controller
  and its `_<code>/*.html` views → a human reviews a diff and approves. So
  **decompose the app into transaction-sized units**, each doing one job.
- **It reads the database schema but cannot run DDL/DML.** It can only *surface* SQL
  for a human to run (an **Execute** button that then refreshes the models). So put
  any schema as **`CREATE TABLE` SQL in the plan**, and order it **before** the
  transactions that depend on it.
- **It asks for `group`/`code` if you don't specify them** (for a single
  transaction). So **always name the group and code** for every transaction.
- **It already knows SØAD idioms** — routing, the POST/PRG pattern, model naming,
  default-view resolution, the built-in helpers. **Specify intent, not mechanics.**
  Don't re-teach the framework or hand-write boilerplate the agent will produce
  correctly on its own.
- **Nothing is written without human approval**, and large builds are reviewed in
  batches. So **phase the plan** into reviewable chunks.
- **Its context is bounded.** Keep the plan tight and concrete; for a big app, split
  it so it can be fed and approved in stages rather than one huge block.
- **It has no delete/deploy/rollback and its queries are read-only.** Don't plan
  steps that require those; frame data/schema changes as SQL for a human to Execute.

---

## What to produce

Output a plan with these parts, in this order:

1. **Data model** — the tables, columns and relationships, *with the `CREATE TABLE`
   SQL* when the tables don't already exist. This runs first (human clicks Execute).
2. **Transactions** — one block per transaction (see the template). This is the bulk
   of the plan and maps 1:1 onto what the builder creates.
3. **Phases** — group the transactions into approval-sized batches, in build order
   (schema → core entities → screens that depend on them → wiring).
4. **Project conventions** *(optional)* — durable rules the builder should always
   follow (naming, money handling, soft-delete, UI conventions). These belong in the
   project's `AGENTS.md`, not repeated in every request — call them out separately.

---

## Style rules (what makes a plan land well)

- **Name `group/code` explicitly** for every transaction — it becomes the URL
  `/t/<group>/<code>` and the file layout. Never leave it to the builder to guess.
- **Name tables and columns.** The builder reads the schema, but naming them removes
  ambiguity and prevents wrong assumptions.
- **Schema first.** If tables don't exist, give the DDL up front so the build targets
  real columns.
- **One responsibility per transaction.** Prefer `catalog/room` (CRUD) + `booking/new`
  (a form) over one mega-transaction.
- **Specify behaviour, not framework code.** Say "list with a link to the form,
  soft-delete on the row" — not how to wire `render.as_view` or the PRG redirect.
- **Describe the actions** each transaction needs (e.g. `view`, `list`, `save`,
  `delete`) and any per-action method (a save is a POST).
- **State the fields and validation** (required, type, unique) — these drive both the
  form and the controller.
- **Wire the screens together.** Say which list links to which form/detail, so the
  built transactions form one app rather than isolated pages.
- **Phase to approval batches.** "These 3 transactions" is one reviewable diff; a
  20-transaction dump is not.
- **Flag anything that needs SQL** (schema change, seed data) as a fenced ```sql```
  block for a human to Execute — never assume the builder ran it.

---

## Plan template

Produce your plan in this shape (fill in / repeat the transaction block per screen):

```
# <App name> — build plan

## Data model
- table `<name>` (<col> <type> [pk|required|unique|-> other_table], ...)
  ...
### Schema SQL (run first, via Execute)
```sql
CREATE TABLE ...;
```

## Transactions

### <group>/<code>
Purpose: <one sentence>.
Actions: <view | list | save (POST) | delete (DELETE) | ...>.
Fields: <field (required/type/validation), ...>.
Views: <what the screen shows and its layout, plainly>.
Links: <which other transactions it navigates to / from>.
Notes: <anything unusual; leave framework mechanics to the builder>.

### <group>/<code>
...

## Phases (build & approval order)
1. Schema SQL (Execute).
2. <transactions in this batch> — approve.
3. <next batch> — approve.
...

## Project conventions (put these in AGENTS.md)
- <durable rule the builder should always follow>
- ...
```

---

## Worked example (short)

```
# Room booking — build plan

## Data model
- table `room` (id pk, name required, capacity int, active bool)
- table `booking` (id pk, room_id -> room, guest_name required, start_date, end_date)

### Schema SQL (run first, via Execute)
```sql
CREATE TABLE room (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  capacity INT,
  active BOOLEAN DEFAULT TRUE
);
CREATE TABLE booking (
  id INT AUTO_INCREMENT PRIMARY KEY,
  room_id INT,
  guest_name VARCHAR(120) NOT NULL,
  start_date DATE,
  end_date DATE,
  FOREIGN KEY (room_id) REFERENCES room(id)
);
```

## Transactions

### catalog/room
Purpose: manage rooms (CRUD).
Actions: list, view, save (POST), delete (DELETE).
Fields: name (required), capacity (int), active (bool).
Views: a table of rooms, each row linking to the edit form; a simple add/edit form.
Links: list is the entry point; form returns to the list after save.

### booking/new
Purpose: create a booking for a room.
Actions: view, save (POST).
Fields: room (select from `room` where active), guest_name (required),
        start_date, end_date (end after start).
Views: a form; on save, redirect back to the room list with a success message.
Links: reached from the catalog/room list ("Book" action).

## Phases
1. Schema SQL (Execute).
2. catalog/room — approve.
3. booking/new — approve.

## Project conventions (put these in AGENTS.md)
- Dates are stored as DATE; display as YYYY-MM-DD.
- Lists use the standard table layout; forms use a single-column card.
```

---

## Hand-off checklist

- [ ] Every transaction has an explicit `group/code`.
- [ ] Tables/columns are named; DDL is included if they don't exist yet.
- [ ] Schema SQL comes first and is marked "Execute".
- [ ] Transactions are single-purpose and wired together.
- [ ] The plan is phased into approval-sized batches.
- [ ] Durable rules are separated out for `AGENTS.md`.
- [ ] No step assumes the builder can delete, deploy, or run SQL itself.

**Feeding the plan to the builder:** paste the durable *conventions* into the
project's `AGENTS.md` once; paste the *data model + transactions* into the agent
chat phase by phase, approving each batch before moving on.
