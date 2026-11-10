# Shot list: first CastLock demo (free courses)

Master: vertical 1080x1920, about 25 to 30 seconds, voice am_michael, captions word by word in the safe zone, loudness about -14 LUFS measured. Character: Tara pack v1 (characters/tara). All character shots are Wan 2.2 image-to-video from the locked reference still only, fixed camera, subtle motion, seed recorded per shot before the shot counts as accepted. Scene stills are Z-Image Turbo (seed locked per still). Every character shot passes check_frames review before assembly.

| # | Type | Source | Motion or content | Narration covered |
|---|---|---|---|---|
| 1 | Character | Tara reference still, Wan 2.2 I2V, 4s | Fixed camera. She breathes gently and blinks once. Headline text in the safe zone: 11 courses, 359 lessons, free. | "Eleven complete AI courses. Three hundred fifty-nine lessons. Every single one free." |
| 2 | Scene | Z-Image still: a desk at night, one notebook open, three words written as a simple diagram, model plus tools plus loop | Slow, gentle push in via Wan 2.2 I2V scene workflow, 5s | "An agent is a model plus tools plus a loop." |
| 3 | Scene | Z-Image still: the same diagram, arrows showing the loop repeating | Subtle light movement, 5s | "The model thinks, the tools act, and the loop repeats until the job is done." |
| 4 | Character | Tara reference still, Wan 2.2 I2V, 4s | Fixed camera, slight natural head movement, soft background parallax | "That is exactly how the courses are built. One idea at a time, with real code." |
| 5 | Scene | Z-Image still: a laptop screen with clean code and a green test run, warm light | Gentle drift, 4s | "You can read it, run it and test it yourself." |
| 6 | Character | Tara reference still, Wan 2.2 I2V, 4s | Fixed camera, small warm smile at the end. End card text in the safe zone: GitHub, techaurah. | "Follow for one sharp AI lesson a day. All eleven courses are free on GitHub, at techaurah." |

Assembly: pipeline/assemble.py with narration from pipeline/narrate.py, timings from pipeline/timings.py, captions from pipeline/captions.py. Sidecar JSON carries the seeds and the ai_generated flag for the platform AI label step.
