---
name: comment-review
description: Review every comment and docstring a branch adds or edits, decide keep/delete/change against a fixed standard, apply the decisions, and fold each change into the commit that introduced the comment. Use when the user wants a branch's comments trimmed, reviewed, or cleaned up before review.
---

# Comment review

## 1. Extract

Create a list of all of the comments that were modified or added by the relevant changes.

Split the items into batches of about 30, keeping each file whole, and give each batch to its own subagent.

## 2. Decide

Each subagent applies the standard below and writes a decisions file, one item per line changed or deleted.

Unchanged lines don't need to be included here.

```
path/to/file.clj:129 delete this comment, it restates `delete-router!`
path/to/file.clj:103-111 change this comment to "Exact new text, without comment markers or docstring quotes." - delete everything after the first sentence.
```

### The standard

A comment earns its place by telling the reader something the code next to it cannot: what a function returns, a
fact about the data or the outside world, or why a strange-looking line has to be that way. Write it as one plain
sentence where one will do.

**Keep** a comment that:
- is a short docstring saying what a function returns or does
- is a section header
- states a non-obvious fact the code relies on
- briefly explains why something unusual exists
- is an existing comment the branch only edited to stay accurate, for example by adding a new value to a list it
  already enumerates

**Delete** a comment that:
- restates the code (`;; delete the DatabaseRouter` above `(delete-router! id)`)
- labels test data, fixtures or trivial constants (delete these outright; don't trim them to a first sentence)
- points to where something else is tested or covered
- is an essay: paragraphs of design rationale, an argument that an approach is correct, an account of which mistakes
  a test catches, or a namespace docstring that argues the case for the namespace
- justifies an implementation detail at length ("`pr-str` rather than `str` because ...")
- explains a decision the code doesn't show, at a level only the author needs

**Change** a comment that has a useful first sentence followed by elaboration. Keep that sentence, or rewrite it
plainly, and drop the rest: extra paragraphs on parameters, "see [[...]]" pointers, why it was done this way, what
the alternative was, and a closing sentence that restates the point. Prefer describing behaviour over mechanism:

> before: "Throw the query-time refusal for router database `db-id`, which no admin has granted anonymous access: a
> 400 saying only that anonymous access is refused, carrying `:message-for-viewer` naming the database and the
> setting when the viewer may manage that database (see [[...]]). Logs a warning naming both either way."
>
> after: "Throws an error explaining that anonymous database access is disabled. Provides more details if the
> viewer is a superuser or database manager."

Constraints:
- Never delete the docstring of a public var under `src/`, because the linter requires one. Cut it to one sentence
  instead.
- Don't reword a docstring that is already one or two short sentences.
- On an `edited` item, judge only the branch's part. Don't remove text the branch didn't write.
- Some `:description` strings live in API schemas. Changing one changes the generated API docs, so say so when you
  report back.

## 3. Apply

One agent applies every decisions file to the working tree. It finds each comment by its exact `text` from the
items file, never by line number alone, because earlier edits shift the lines. A delete keeps the form valid: a
docstring removed from `(def x "doc" v)` leaves `(def x v)`, and a closing paren that ends up alone on a line joins
the line above. Then it checks the result:
- `./bin/mage kondo <changed .clj files>`
- `bun run prettier --check <changed ts files>`
- every decision is accounted for
