# Character rules

A CastLock character pack is a contract. These rules define what a pack may and may not contain, and `pipeline/validate_pack.py` enforces the machine-checkable parts.

## The pack

```
characters/<name>/
  character.yaml     the contract: identity, voice, seeds, motion rules, lora policy
  reference/         the locked source still or stills
  notes.md           per-shot settings log (optional but recommended)
```

## Locked characters

A pack with `locked: true` describes a real person (or an approved character design) whose face is an asset, not a generation target.

Rules for a locked character:

1. The face comes only from the stills in `reference/`. Those stills are source photographs or approved artwork. Nothing in `reference/` may be model-generated.
2. `lora` must be `forbidden` in the pack. A LoRA, img2img character sheet, or any other face-generation route for a locked character is a rule violation, and validation fails on it. LoRAs remain available for fictional characters and for scene or style control that never touches a locked face.
3. Motion shots are image-to-video from a `reference/` still, using the character workflow (`workflows/comfyui/wan22-i2v-character.api.json`). Text-to-video of a locked character is forbidden.
4. Permitted motion is conservative by default: fixed or near-fixed camera, subtle motion only (breathing, a blink, a slight head turn, background parallax), clips of 2 to 5 seconds. Forbidden by default: camera orbits, large head turns, scene relighting, anything that asks the model to invent a new angle of the face.
5. Prompts for character shots describe motion only. They never describe the person's appearance; the reference still carries the appearance.
6. Seeds are locked per shot and recorded in the pack's seed registry and the shot's notes, so any accepted shot can be reproduced.
7. Every rendered character shot goes through `check_frames.py` and a human or agent review against the reference before assembly. A shot whose face has moved off the reference is rejected, whatever the rest of the shot looks like.

## Unlocked (fictional) characters

A pack with `locked: false` describes a fictional character. img2img character sheets and a character LoRA are permitted routes to build the reference set, and once the reference set is approved the same discipline applies: shots come from the approved stills, seeds are registered, frames are checked. The difference is only in how the reference set may be created.

## Voice

Each pack names exactly one Kokoro voice in `voice.id`, with a fixed `voice.speed`. A character does not change voice between videos. If a voice ever has to change, that is a pack version change and gets noted in `notes.md`.

## Versioning

A pack is versioned as a folder in git. Changing the reference set, the permitted motions, or the voice means editing `character.yaml` in a commit that says why. Silent swaps of a reference still are the failure mode this whole system exists to prevent.
