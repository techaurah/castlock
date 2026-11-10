# CastLock

A consistent-character video pipeline: locked reference stills, open-weights image-to-video, local narration, and a checked final export.

Most AI video tools treat the character as a prompt detail. CastLock treats the character as a locked asset. A character is a versioned pack: one canonical reference still, a permitted-motion list, a seed registry, and a named voice. Every shot of that character is image-to-video generated from the locked still and nothing else, every rendered shot is frame-checked against the reference before it is accepted, and the final export follows fixed house rules for framing, loudness, captions and AI disclosure.

## The stack

| Layer | Tool | Licence | Notes |
|---|---|---|---|
| Stills (scenes, backgrounds, thumbnails) | Z-Image Turbo (Tongyi-MAI, Alibaba) in ComfyUI | Apache 2.0 | 6B parameter model, 8 steps at CFG 1.0. Never used to generate a locked character's face. |
| Motion (image-to-video) | Wan 2.2 I2V 14B, fp8 build, in ComfyUI | Apache 2.0 | Dual high-noise and low-noise models with the official 4-step lightx2v LoRA path, or the slower full-step path. See the trade-off note in `docs/stack.md`. |
| Narration | Kokoro-82M via kokoro-onnx, on CPU | Apache 2.0 | Fixed preset voices, no cloning. One voice per character, named in the pack. |
| Word timings | faster-whisper (small) | MIT (code) | Falls back to a labelled estimation mode when unavailable. |
| Assembly | ffmpeg | LGPL/GPL depending on build | Concat, music ducking, two-pass loudnorm, burned-in captions. |
| Workflow host | ComfyUI | GPL-3.0 | Runs the two model layers from the workflow JSONs in this repo. |

Model weights keep their own licences. The MIT licence in this repo covers CastLock's own code and documentation only. See `docs/stack.md` for the full breakdown.

## Models policy

CastLock uses only models under true open licences (Apache, MIT, GPL class). Conditionally-free community licences do not qualify, however generous their free tier looks. LTX-2.5 is explicitly excluded under this policy: its LTX-2 Community License is source-available with revenue conditions, not open source. Full policy: `docs/models-policy.md`.

## The character pack

A character lives in `characters/<name>/` and is a contract the pipeline enforces:

- `character.yaml` names the character, the locked reference still, the voice, the seed registry, permitted motions and forbidden motions.
- `reference/` holds the locked still or stills. For a locked character these are real source photographs or approved artwork, never model output.
- The `lora` field is explicit. For a locked real-person character it reads `forbidden`, and `pipeline/validate_pack.py` fails any pack that tries to allow face generation for a locked character.

The bundled example is `characters/tara/`. `characters/_template/` is a blank pack to copy for a new character. Full rules: `docs/character-rules.md`.

## Pipeline scripts

All in `pipeline/`, all runnable from the command line, no network calls:

| Script | What it does |
|---|---|
| `narrate.py` | Narration text in, Kokoro ONNX WAV out. Voice selectable, default `am_michael`. |
| `timings.py` | Word timings JSON from a narration WAV, via faster-whisper when installed, else a clearly labelled character-count estimation. |
| `captions.py` | Word-by-word ASS captions styled into the center safe zone for a 1080x1920 frame. |
| `assemble.py` | ffmpeg assembly: shots plus narration plus optional ducked music, two-pass loudnorm to about -14 LUFS, loudness measured and printed, sidecar JSON with model list, licences, seeds and an `ai_generated: true` flag. |
| `check_frames.py` | Contact sheet of frames from a rendered video next to the locked reference, for human or agent drift review. |
| `validate_pack.py` | Validates a character pack against the lock rules. Used by the test suite and CI. |

## House rules

Every export follows the same rules, documented in `docs/house-rules.md`:

- Vertical 1080x1920 master. All important content sits in the center safe zone (at least 140px clear left, 200px right, 240px top, 360px bottom), because platform interfaces cover the edges.
- Voice on every video, always, normalized to about -14 LUFS integrated with true peak at or below -1 dBFS, measured before the export is declared done.
- Word-by-word captions burned in, inside the safe zone, never at the frame edge.
- AI content is labelled on every platform that offers a label, and the export sidecar records the models and licences behind the video.

## GPU routes

The stills and voice layers run on modest hardware. The Wan 2.2 video layer is tuned by its official workflow for a 24GB-class card. `docs/gpu-routes.md` compares the routes (RunPod and vast.ai hourly rentals, Colab, Hugging Face, Comfy Cloud, hosted APIs) with dated prices and an honest cost per finished video.

## Quickstart (CPU-only parts)

```bash
# 1. Validate the bundled character pack
python3 pipeline/validate_pack.py characters/tara

# 2. Narrate a script (needs kokoro-onnx and the Kokoro v1.0 model files)
python3 pipeline/narrate.py examples/demo-script.md --voice am_michael --out build/narration.wav

# 3. Word timings, then captions
python3 pipeline/timings.py build/narration.wav --out build/timings.json
python3 pipeline/captions.py build/timings.json --out build/captions.ass

# 4. Assemble (shots rendered via the ComfyUI workflows, see workflows/comfyui/)
python3 pipeline/assemble.py shot1.mp4 shot2.mp4 --narration build/narration.wav --captions build/captions.ass --out build/final.mp4

# 5. Frame-check the result against the locked reference
python3 pipeline/check_frames.py build/final.mp4 characters/tara/reference/tara-founder-face-reference.png --out build/contact-sheet.jpg
```

## Limitations, stated plainly

- Image-to-video faces drift, Wan included. Short clips (2 to 5 seconds), a fixed camera, locked seeds and subtle motion keep a character recognisable; nothing makes it perfect. Every character shot must pass the frame check before use.
- The Wan 2.2 layer's official workflow is tuned for a 24GB-class card (its own note reports about 84 percent of 24 GB used at 640x640). Smaller cards run it with offloading at slower speeds.
- Wan 2.2 renders slower than a distilled video model: the official template's own measurements are about 97 seconds per 5 second clip with its 4-step LoRA path and about 536 seconds without it, on an RTX 4090D. Per-video GPU time is budgeted from those numbers in `docs/gpu-routes.md`.
- Free Colab tiers are a proof-of-concept route for the stills layer, not a production route for the video layer.
- This is v0.1: scripts, workflows, docs and one scripted demo. No web UI, no batch rendering, no LoRA training.

## Licence

CastLock's own code and documentation: MIT (see `LICENSE`). Model weights and third-party tools keep their own licences, listed in the stack table above and in `docs/stack.md`.
