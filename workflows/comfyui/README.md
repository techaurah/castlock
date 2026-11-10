# ComfyUI workflows

Three workflows in ComfyUI API format (the JSON the `/prompt` endpoint accepts):

| File | Layer | Model |
|---|---|---|
| `zimage-stills.api.json` | Stills: scenes, backgrounds, props, thumbnails | Z-Image Turbo (Apache 2.0) |
| `wan22-i2v-character.api.json` | Motion: character shots from the locked reference still | Wan 2.2 I2V 14B fp8 (Apache 2.0) |
| `wan22-i2v-scene.api.json` | Motion: non-character scene shots from a scene still | Wan 2.2 I2V 14B fp8 (Apache 2.0) |

Model files needed, with the official download locations in the ComfyUI templates: `z_image_turbo_bf16.safetensors`, `qwen_3_4b.safetensors`, `ae.safetensors`, `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors`, `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors`, `wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors`, `wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors`, `umt5_xxl_fp8_e4m3fn_scaled.safetensors`, `wan_2.1_vae.safetensors`.

Character workflow settings follow `docs/character-rules.md`: the input image is the character pack's locked reference still (copy it into the ComfyUI input folder and set the LoadImage name to match), the positive prompt describes motion only, the seed is a fixed placeholder (12345) to be replaced by the pack's registered seed per shot, length is 81 frames (about 5 seconds at 16 fps), output is 720x1280 and is finished to the 1080x1920 master in `pipeline/assemble.py`.

Removing the lightx2v LoRA nodes for the full-quality path: delete nodes 8 and 9, point nodes 10 and 11 at nodes 4 and 5, and change both samplers to 20 steps with step ranges 0 to 10 and 10 to 20. Every class name involved is unchanged and verified as below; expect roughly five times the render time (see the timings below).

## WORKFLOWS_STATUS (verification record, 2026-11-10)

What was verified, and how:

- Z-Image Turbo graph: copied from the official ComfyUI workflow templates repository (Comfy-Org/workflow_templates), file `benchmarks/image_z_image_turbo.json`, which is itself in API format, cross-checked against the official blueprint `text_to_image_z_image_turbo.json`. Every node class name, model file name, and sampler setting (8 steps, CFG 1, `res_multistep`, `simple`, ModelSamplingAuraFlow shift 3, CLIPLoader type `lumina2`) comes from those official files. CastLock changes versus the source: clean node ids, a portrait 864x1536 latent (the source benchmark uses 1024x1024), a placeholder prompt, and a fixed placeholder seed.
- Wan 2.2 I2V graph: converted to API format from the official ComfyUI blueprint `image_to_video_wan_2_2.json` (same graph as `archived/03_video_wan2_2_14B_i2v_subgraphed.json`) in the same official repository. The full node list and link wiring were extracted programmatically from the blueprint's subgraph and reproduced: dual UNETLoader (high and low noise fp8 models), dual LoraLoaderModelOnly (lightx2v 4-step LoRAs), dual ModelSamplingSD3 (shift 5), CLIPLoader (umt5, type `wan`), VAELoader (wan_2.1_vae), WanImageToVideo, dual KSamplerAdvanced with the 0-2 and 2-4 step split at CFG 1 with `euler` and `simple`, VAEDecode, CreateVideo at 16 fps, plus LoadImage and SaveVideo endpoints as in the archived template. Model file names are the official ones.
- Render timings quoted in the docs come from the official blueprint's own note (RTX 4090D 24 GB, 640x640, 81 frames): about 97 seconds for a first generation with the 4-step LoRA path, about 536 seconds without it. Measured there, not by us.

What was NOT verified:

- None of the three workflows has been executed yet. There is no GPU in the build environment, so no workflow has been run through a ComfyUI server. They are faithful structural conversions of official templates, validated as JSON and checked node by node against the sources, and they wait for a first run on the chosen GPU route (docs/gpu-routes.md).
- `SaveVideo` in the Wan workflows follows ComfyUI core convention for its inputs (`video`, `filename_prefix`, `format`, `codec`). The class name is verified from the official archived template's top level; its exact widget defaults were not separately confirmed.
- Prompt texts (positive and negative) are CastLock's own, written for the character rules. They are content, not structure.
- The blueprint drives some values (resolution, seed, prompt) in from subgraph inputs; the API files set them as literal values instead. That is a format conversion difference, not a graph difference.
