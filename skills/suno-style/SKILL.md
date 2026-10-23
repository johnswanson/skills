---
name: suno-style
description: Write a Suno style prompt (the "Style of Music" field) in the chat. Use when the user asks for a Suno style, style prompt, or genre tags for a song.
---

# Suno style prompt

Write the prompt in the chat. Do not write it to a file unless the user asks for one.

## Steps

1. **Collect the sound.** Work from the song in the conversation (lyrics and any annotations about tempo, key and dynamics) and the user's brief: the reference artist or song, the audience, and the mood.
2. **Translate references into descriptors.** Suno rejects artist and song names, so describe what the reference sounds like: its genre and era, vocal type, signature instruments, and dynamic shape. "Wrecking Ball by Miley Cyrus" becomes `emotional piano power ballad, 2010s pop, belted chorus, quiet intimate verses, explosive chorus drops`. The step is done when the prompt names no artist, song or album.
3. **Write the tags.** Give one comma-separated line of lowercase tags in this order: genre and era, vocals, instrumentation and production, dynamics, mood, then tempo and key. Use 12 to 20 tags and stay well under Suno's 1000-character limit. Add tags for the audience when it matters (`kids pop, bright youthful voice, playful`). Leave out lyrics, section structure and full sentences, because Suno reads those from the lyrics field.
4. **Output** the tag line in its own fenced code block so it copies cleanly. Add one or two sentences on how the reference was translated, and remind the user that the style goes in the style field, not the lyrics.
