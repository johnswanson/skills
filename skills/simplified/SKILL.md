---
name: simplified
description: Explain the provided input, or the last message in the conversation, in ASD-STE100 Simplified Technical English, with a little context. Use when the user invokes /simplified, asks for a Simplified Technical English or STE explanation, or asks to have something restated in controlled/simplified language.
---

# Simplified Technical English Explainer

## Quick start

Take the input the user provided with the command. If they provided none, take the
last message in the conversation (your own last reply, or theirs if it came after).
Explain it — do not just translate it word for word. Add a little context: what it
is about, and why it matters here. Write the whole explanation in ASD-STE100
Simplified Technical English.

Example: given "the rebase completed but two tests errored due to a missing fixture",
respond:

> We moved our changes on top of the newest code. This step was successful.
> Then we did the tests again. Two tests did not complete. The cause is a
> known problem in the test setup, not in our changes. Our changes are safe.

## STE writing rules

Obey these ASD-STE100 rules:

- Use short sentences: maximum 20 words in an instruction, 25 in a description.
- Use short paragraphs: maximum 6 sentences. One topic for each paragraph.
- Use the active voice. Say who or what does the action.
- Use the imperative for instructions: "Run the tests", not "the tests should be run".
- Use only one meaning for each word, and the same word for the same thing everywhere.
- Use simple present tense for facts, past tense only for events that occurred.
- Do not use -ing verb forms. Write "the test that runs", not "the running test".
- Do not make clusters of more than three nouns. Break them apart with "of" or "for".
- Use articles ("the", "a") — do not delete them to save space.
- Use "make sure" for checks: "Make sure that the branch is clean."
- Prefer approved simple verbs: do, make, get, put, remove, start, stop, show, use.
- Give warnings and important facts as short, clear, separate sentences.

Technical names (file paths, function names, commands, error text) are permitted
as-is: quote them exactly and treat them as names, not as vocabulary.

## Workflow

1. Identify the subject: the given input, or the last message.
2. Find the two or three facts the reader must know.
3. Give one or two sentences of context first: what the subject is about.
4. Explain the facts in STE, in the order they occurred or matter.
5. If there is a necessary action for the reader, give it as an instruction at the end.
6. Read your text again. Remove each sentence that is too long. Divide it into two.

Keep the full explanation short: usually one to three paragraphs.
