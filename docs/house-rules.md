# House rules for every export

These are TechAura's standing delivery rules for video. `pipeline/assemble.py` and `pipeline/captions.py` bake in the machine-checkable parts; the rest are checked before anything is published.

## Framing: the center safe zone

Platform interfaces cover the edges of a vertical video: the right side carries the action rail (like, comment, share), the bottom carries the username and caption block, the top carries the header. Anything important placed there gets hidden.

For a 1080x1920 master:

- Left margin at least 140px.
- Right margin at least 200px (the action rail).
- Top at least 240px clear.
- Bottom at least 360px clear.
- All important content sits inside that center zone as one centered block.
- Burned-in captions sit inside the safe zone, with the caption band baseline around y 1400 to 1500, never at the frame bottom.

Every video is frame-checked against these zones before delivery. The rule applies to new content; already-published posts are not reworked for it.

## Voice: always on, always measured

- Every video carries a voiceover. Silent text-only videos are not the standard.
- Narration is Kokoro, one voice per character (see the character pack).
- Loudness is normalized to about -14 LUFS integrated with true peak at or below -1 dBFS, using a two-pass ffmpeg loudnorm, and the measured numbers are printed before the export is declared done. A video whose loudness was not measured is not finished.

## Captions

- Word-by-word captions, timed from the narration with faster-whisper (or the labelled estimation fallback during drafting).
- Burned in, small and legible, white bold with a black outline, lower-center inside the safe zone.
- Spelling is checked during the frame review.

## AI disclosure

- AI-generated content is labelled on every platform that offers an AI label. TechAura's standing decision (2026-11-09) is that carrying the label is fine.
- Every export writes a sidecar JSON recording the models used, their licences, the seeds, and `ai_generated: true`, so the facts are at hand at posting time.

## Content discipline

- One declared goal per piece, one call to action, matched to the goal.
- No invented statistics, no borrowed earnings claims, no superlatives the evidence does not carry.
- No em dashes in scripts, captions or on-screen text.
- Pacing: one day's content per day in its scheduled slots. Extra content queues to the following days. No same-day stacking unless the owner orders it for that day.
