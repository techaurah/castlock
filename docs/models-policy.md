# Models policy

CastLock uses only models released under true open licences: OSI-style licences in the Apache, MIT, BSD or GPL class, which grant use, modification and commercial use without revenue thresholds, field-of-use conditions, or separate agreements.

Conditionally-free community licences do not qualify. A licence that is free only below a revenue line, only for some products, or only with conditions attached to the output may be generous, but it is source-available, not open source, and a pipeline built on it inherits every condition.

## Current models

| Model | Licence | Status |
|---|---|---|
| Z-Image Turbo | Apache 2.0 | Used (stills) |
| Wan 2.2 | Apache 2.0 | Used (motion) |
| Kokoro-82M | Apache 2.0 | Used (narration) |
| faster-whisper | MIT (code) | Used (word timings) |

## Explicitly excluded

| Model | Reason |
|---|---|
| LTX-2.5 (Lightricks) | LTX-2 Community License: free commercial use only under 10 million USD annual revenue, a paid agreement above that line, plus disclosure conditions. Source-available, not open source. Excluded 2026-11-10. It was this pipeline's original motion model during design and was replaced by Wan 2.2 (Apache 2.0) under this policy before v0.1 shipped. |
| FLUX.1 dev | Non-commercial licence terms for the dev weights. Same class of problem. |

Tools are a different category from models: ComfyUI (GPL-3.0) and ffmpeg (LGPL/GPL) are open-source tools, and rented GPU infrastructure (for example RunPod) is a service, not a model. Both are fine under this policy.
