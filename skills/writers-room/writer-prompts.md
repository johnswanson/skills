# Writer prompts

Three prompts, one per round. Fill the `<...>` slots and send the rest as written. Send every prompt of a round in one
message so the writers run together. Each writer is a fresh subagent: it knows only its prompt and the files it names.

Every prompt ends by asking for a file and a one-word reply. The lyrics reach you by reading the files, which keeps
ten drafts out of the dispatch results and leaves them on disk for the next round.

## Round 1: a first draft

```
You are a songwriter. Read <song folder>/BRIEF.md in full and write the complete lyric for "<title>" plus a Suno
style line, following the brief exactly. Ignore every other file in that project.

Your starting angle (a suggestion to keep <N> writers from converging; leave it if you find something better):
<the angle, in one or two sentences, with any rule that keeps it honest, such as "keep the metaphor consistent so
every line works literally and figuratively">

Before you finish, reread every line and ask: can a listener picture exactly what this says, and does it make sense?
Rewrite any line that fails.

Write your result to <song folder>/r1/<NN>.md (create the folder if needed) in this form: a first line
`Angle: <one sentence>`, then a `## Lyrics` heading with the lyric as plain text, then a `## Style` heading with the
one-line style. Reply with only the word "written" and the path.
```

The wildcard's angle paragraph instead reads:

```
Your starting angle: none. You are the wildcard among <N> writers; the others have <the other angles, each in three
or four words>. Find the framing none of them will, as long as it serves the hook and the sincere turn.
```

Angles that have produced distinct songs: a metaphor held throughout (a breakup, an engagement); the story told
literally in order; the whole song in one room on one afternoon, the past arriving as memories; a letter; an
inventory that escalates; the sad version, where the hook is funny once and then hurts; the crowd anthem with a
call and response; two characters compared; one object followed through the story.

## Round 2: a rewrite

```
You are a songwriter revising a lyric. Read, in this order: <song folder>/BRIEF.md (the brief),
<song folder>/r1/<NN>.md (the draft you are revising), and <song folder>/r1/NOTES.md (the editor's notes on all
first drafts, with a bank of the best lines from the others). Ignore other files.

The editor's line-by-line notes on draft <NN>:
- KEEP, these are the song: <the protected lines, quoted>
- FIX: <a quoted line, why it fails, the direction of the repair>
- FIX: <...>
- <ideas from the line bank worth considering for this song, named>
- Hold one verse shape. Target <range> words.

The sound: <why lanes are being assigned, in one sentence>. Yours: <the sound lane: genre and era, the instruments
that carry it, the vocal, the dynamic shape, in two sentences>. Write the style inside that lane, but make it specific
and a little unusual rather than a list of stock adjectives, and annotate the lyric's sections to match.

Rewrite the whole song. Then reread every line and ask: said to a stranger with no context, does this give one clear
picture and make sense? Fix any that fail.

Write the result to <song folder>/r2/<NN>.md (create the folder) as: a first line `Angle: <one sentence>`, a
`## Lyrics` heading and the lyric as plain text, a `## Style` heading and the one-line style, then a `## Changes`
heading with at most five bullets on what you changed. Reply with only "written" and the path.
```

## Round 3: a polish

```
You are a song editor doing a final polish. Read <song folder>/BRIEF.md and then <song folder>/r2/<NN>.md. Ignore
other files. This lyric is close to finished: change only what is listed below, plus any line that fails your own
sense check. Keep every line that works as it is, keep the verse shape (<the shape>), and keep the word count within
<range>.

Editor's notes:
- <a quoted line, why it fails, the direction of the repair>
- <...>
- Everything else stays, especially <the lines and devices that must survive>.

Then do a fresh-eyes pass on every line: said to a stranger with no context, does it give one clear picture, and is
it literally true to the story? Check the style line is 12 to 20 lowercase tags, names no artist, and that every tag
names something to be heard; delete any tag that names a thing to leave out.

Write the result to <song folder>/r3/<NN>.md (create the folder) as: a first line `Angle: <one sentence>`,
`## Lyrics` and the lyric as plain text, `## Style` and the one-line style, `## Changes` with at most four bullets.
Reply with only "written" and the path.
```
