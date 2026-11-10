# The stack

CastLock layers four tools. Each layer was chosen because it is open-weights or open source, runs without a per-call API bill, and has a licence that permits commercial use at TechAura's scale. Licences below are stated as of 2026-11-10; check the upstream source before relying on them for a different business.

## Z-Image Turbo (stills)

- What: text-to-image model family from the Z-Image Team at Tongyi-MAI (Alibaba Group). 6 billion parameters, Scalable Single-Stream DiT (S3-DiT) architecture with a Qwen3-4B text encoder. The Turbo variant is distilled to 8 function evaluations at CFG 1.0.
- Licence: Apache 2.0, on the repository licence file and the Hugging Face model cards. Commercial use allowed, no revenue threshold, no separate agreement.
- Files in ComfyUI: `z_image_turbo_bf16.safetensors` (about 12.3 GB), `qwen_3_4b.safetensors` text encoder (about 8 GB, offloads to system RAM after encoding), `ae.safetensors` VAE (about 335 MB, shared with FLUX.1).
- VRAM: the team states Turbo fits comfortably within 16 GB VRAM devices. FP8 builds run at about 8 GB; GGUF quantised builds go lower.
- Role in CastLock: scenes, backgrounds, props, thumbnails and supporting visuals. Never a locked character's face (see `character-rules.md`).
- Settings used by the reference workflow: 8 steps, CFG 1.0, `res_multistep` sampler, 1536x864 landscape or 864x1536 portrait stills, locked seed per shot.

## Wan 2.2 (motion)

- What: Alibaba's Wan 2.2 image-to-video, the 14B tier in CastLock's workflows. A mixture-of-experts design with two diffusion models, a high-noise model for early steps and a low-noise model for late steps, sharing a UMT5 XXL text encoder and the Wan 2.1 VAE.
- Licence: Apache 2.0. Commercial use allowed, no revenue threshold, no separate agreement. Chosen under the models policy (docs/models-policy.md): the pipeline's original motion model, LTX-2.5, was dropped before v0.1 shipped because its Community License is source-available with revenue conditions, not open source.
- Files in ComfyUI (from the official ComfyUI repackaged set): `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` and `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`, `umt5_xxl_fp8_e4m3fn_scaled.safetensors` text encoder, `wan_2.1_vae.safetensors`, and the two lightx2v 4-step LoRAs (`wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors` and its low-noise twin).
- VRAM: the official workflow's own note (RTX 4090D 24 GB, 640x640, 81 frames) reports about 83 to 84 percent of 24 GB used, so plan on a 24GB-class card for the reference settings. Larger frames use more.
- Known weakness: faces drift in image-to-video, as with every model in this class. The mitigations CastLock bakes into its character workflow are short clips (2 to 5 seconds), a fixed or near-fixed camera, locked seeds, prompts that describe motion only, pinned first frames, and a mandatory frame check before a shot is accepted.
- The honest trade-off: Wan 2.2 is not a distilled-speed model. The official template's own measurements (RTX 4090D 24 GB, 640x640, 81 frames, read 2026-11-10) are about 97 seconds for a first generation with the shipped 4-step lightx2v LoRA path (about 71 seconds for later generations) and about 536 seconds without the LoRAs at full steps. A distilled model like LTX-2.5 generates a comparable clip faster; CastLock accepts the slower render as the price of a clean Apache 2.0 licence. The template also notes the lightx2v LoRA path reduces video dynamics, which for CastLock's subtle-motion character shots is an acceptable, even useful, side effect. GPU budgets in docs/gpu-routes.md are built from these numbers.

## Kokoro (narration)

- What: Kokoro-82M, an 82 million parameter text-to-speech model by hexgrad, StyleTTS 2 lineage. 54 preset voices across 9 languages in v1.0. Voice IDs encode language and gender: `am_michael` is American English male, `af_heart` is American English female.
- Licence: Apache 2.0. Commercial use allowed, no per-character cost.
- There is no voice cloning; the voice set is fixed presets, which suits a locked narrator voice. CastLock runs it on CPU through kokoro-onnx, so the voice layer needs no GPU.
- Role in CastLock: one named voice per character, recorded in `character.yaml`.

## faster-whisper (word timings)

- What: SYSTRAN's faster-whisper, a CTranslate2 reimplementation of OpenAI's Whisper. CastLock runs the small model over the finished narration to get word-level timestamps for captions.
- Licence: MIT (code). Model weights follow the Whisper model terms.
- On CPU it runs around real time or somewhat slower for the small model on short narration. When faster-whisper is not installed, `timings.py` falls back to a character-count estimation and labels its output `estimated: true`. Estimated timings are a drafting aid, not a delivery standard.

## ffmpeg (assembly)

- What: the assembly layer. Concatenates shots, mixes narration over ducked music, burns in captions, and normalizes loudness with a two-pass loudnorm.
- Licence: LGPL or GPL depending on the build configuration.
- CastLock targets about -14 LUFS integrated with true peak at or below -1 dBFS, measured and printed by `assemble.py` on every export.

## ComfyUI (workflow host)

- What: the node-based host that runs the Z-Image and Wan 2.2 workflows.
- Licence: GPL-3.0.
- CastLock ships its workflows in ComfyUI API format (the format the `/prompt` endpoint accepts) in `workflows/comfyui/`. See that folder's README for the verification status of each workflow.
