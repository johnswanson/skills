---
name: writers-room
description: "Run a writers' room for one song: many subagents draft lyrics and a Suno style from one brief, an editor critiques every line, and the best drafts are rewritten over two rounds into a ranked set of finals."
disable-model-invocation: true
---

Run a writers' room for the song the user names. You are the editor: you write the brief, you read every line, and
you decide what advances. The writers are subagents; each one writes or revises a single lyric and never sees the
conversation, so everything a writer needs goes in a file.

Defaults, unless the user says otherwise: 10 writers, 5 finalists, a 4-minute song (340 to 400 sung words), one
rewrite round and one polish round.

All work lives in one folder per song, `<song-slug>/` in the project:

```
BRIEF.md            the only thing every writer reads
r1/01.md ... 10.md  first drafts        r1/NOTES.md  your notes on them
r2/NN.md            rewrites            r3/NN.md     polished
final/<title>.md    what you present
```

The prompts you send are in [`writer-prompts.md`](writer-prompts.md); the brief's outline is in
[`brief-outline.md`](brief-outline.md). Read both before step 1.

`example/` holds one finished run to calibrate against: its `BRIEF.md`, the editor's `NOTES.md` after round 1, and
one `final.md`. Read `example/NOTES.md` before you write your first notes.

## Steps

### 1. Write the brief

Settle with the user, from the conversation or by asking once: who sings (a recurring character gets a biography),
what the song is about, and whether the sound is open or given. Then write `BRIEF.md` to the outline. Invoke the
`lyrics` and `suno-style` skills and copy their format rules into the brief, so the writers get the user's
current rules.

Done when a stranger given only `BRIEF.md` could write the song: the singer, the story,
the facts that may be used and the ones that may not, the craft rules and the output format are all on the page.

### 2. Round 1: fan out

Give every writer a different **angle** (a framing, a point of view, a structure or a register), and make the last
writer the wildcard, told what the others have and asked for the framing none of them will find. Angles are what keep
ten writers from handing back one song. Leave the sound to each writer unless the user fixed it.

Dispatch all writers in one message with the round-1 prompt. Each writes `r1/NN.md` and replies with the path only.

Done when every `r1/NN.md` exists and holds an angle line, a lyric and a style.

### 3. Edit round 1

Read every draft in full and edit it as described under [Editing](#editing). Then:

- Choose the finalists. Pick for the strength of the central idea and its best lines, since weak lines can be fixed
  and a weak idea cannot. Keep the set varied in angle.
- Write `r1/NOTES.md`: the problems most drafts share, each with the offending lines quoted, and the **line bank**.
- Give each finalist a **sound lane**: its own genre, era, tempo and instrumentation, distinct from the other
  finalists'. First-round styles converge on one record (in the first run of this process all ten chose the same
  fingerpicked acoustic arrangement at the same tempo), and a set of finals that sound alike gives the user no choice.
  When the user fixed the sound, give each finalist a different treatment within it.

Done when every line of every draft has been judged, each finalist has KEEP and FIX notes and a sound lane, and
every draft that did not advance has had its best lines moved into the line bank.

### 4. Round 2: rewrite

Dispatch one fresh writer per finalist, in one message, with the rewrite prompt: the brief, the draft, `NOTES.md`,
that draft's KEEP and FIX notes, and its sound lane. Each writes `r2/NN.md` with a short list of changes.

Done when every `r2/NN.md` exists.

### 5. Edit round 2

Read every rewrite in full and edit it again. Check each FIX was made and each KEEP survived. A rewrite that has
fixed its notes needs only a polish; write FIX notes for the lines that remain and name what stays.

### 6. Round 3: polish

Dispatch one fresh editor per finalist with the polish prompt. A polish changes the listed lines and any line that
fails the stranger test, and leaves the rest alone. Each writes `r3/NN.md`.

### 7. Final edit

Diff each `r3` file against its `r2` file and judge only the changed lines; a polish sometimes swaps one broken line
for another. Fix what is still wrong yourself, and keep a list of the lines you wrote. Check each word count with
`wc -w` on the lyric with annotations removed. Copy the finals to `final/`, named by title, without the change lists.

Done when every line of every final passes the stranger test and every style passes the style checks below.

### 8. Present

Show the finals in the chat, best first, each with a one-line reason for its rank, its lyric in a fenced block and its
style in a second fenced block, so both paste cleanly. Then state plainly: the weak spots that remain, the lines you
wrote yourself, any place the song simplifies the facts, and where the files are. Ask which the user wants to take
forward.

## Editing

Editing is line by line. For each draft, read every line and sort it:

- **KEEP**: a line the song should be built round. Quote it. These go to the writer as protected, and the best of
  them from drafts that do not advance go into the line bank.
- **FIX**: a line that fails. Quote it, say why in a few words, and point at the repair.

A line fails for one of these reasons:

- **It is filler**, there to complete a rhyme or a line count.
- **It breaks the verse shape.** One line count, rhyme scheme and line length per section type, so the melody repeats.
- **It breaks a running metaphor**, working on one level and not the other.

Then check the song as a whole:

- The story is in order and survives one hearing.
- Sung words fall in the target range.

**The line bank** is the part of `NOTES.md` that carries good ideas between drafts: the best lines from all drafts,
quoted with their draft number, grouped by what they do in the song. Tell writers to take two or three that fit and
reword them to their own metre.

**Style checks.** One line of 12 to 20 lowercase tags; the singer's voice named; no artist, song or album names;
every tag says what should be heard, because a tag such as "no pedal steel" summons the thing it names; specific
enough to be a record that does not exist yet rather than a list of stock adjectives; section annotations in the lyric
agree with it.
