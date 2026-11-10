# GPU routes

CastLock's stills, voice and assembly layers run on modest hardware, including CPU for voice and assembly. The Wan 2.2 motion layer decides the route: its official ComfyUI workflow is tuned for a 24GB-class card (the template's own note reports about 83 to 84 percent of 24 GB used at 640x640). This page compares the routes a team with no local GPU can take. Prices are snapshots read on 2026-11-10 and move often; verify live before any spend.

Baseline workload for the cost maths: one finished 45 second vertical video, 10 motion shots of about 5 seconds each, 16 stills, narration and assembly on CPU. Render times come from the official Wan 2.2 workflow note (RTX 4090D 24 GB, 640x640, 81 frames): about 97 seconds for a first generation with the shipped 4-step lightx2v LoRA path and about 71 seconds for later generations, or about 536 seconds per clip without the LoRAs at full steps. CastLock renders at 720x1280, larger than the note's 640x640, so treat these as floor estimates: the motion layer is roughly 20 to 30 minutes of GPU time per finished video on the LoRA path, and roughly 90 minutes on the full-step path, once a machine is warm.

## Recommended: RunPod or vast.ai hourly rental

- RunPod list prices checked 2026-11-10: RTX 3090 about $0.22/hr (Community Cloud), RTX 4090 about $0.34/hr (Community) or $0.89/hr (Secure), RTX 5090 about $0.69/hr (Community). Per-second billing. Network volumes about $0.07/GB/month.
- vast.ai marketplace medians the same week: RTX 3090 about $0.22 to $0.24/hr, RTX 4090 about $0.47/hr median.
- Runs both models: a 3090 or 4090 is the 24GB class the official Wan workflow is tuned for, and Z-Image Turbo runs comfortably inside it. A 5090 (32 GB) adds headroom for larger frames.
- Cost per finished video at 4090 Community rates: roughly $0.15 to $0.35 of GPU time on the LoRA path, roughly $0.50 to $0.70 on the full-step path, once a persistent volume holds the model set, plus a one-time download of the model files. Human time to babysit the session is the real cost, not the GPU line.
- Human step: the account and payment method must belong to the operator. After that, pod start and stop and workflow runs can be scripted within the loaded credit.

## Hosted model APIs

Several providers serve Wan 2.2 image-to-video as an API, which removes GPU management entirely. We did not verify a per-second price for Wan 2.2 on 2026-11-10, so no number is quoted here; price this route at decision time. Expect it to be the fastest route to a first demo and the most expensive route at volume, the usual shape for hosted generation. Human step: account and billing first, then calls are an API key away.

## Free proof of concept: Google Colab

- Free tier: a T4 (16 GB) when one is available, sessions up to 12 hours, idle disconnects, no guaranteed quota.
- Paid tiers: Pay As You Go $9.99 per 100 compute units; Pro $9.99/month (100 units); Pro+ $49.99/month (500 units). Measured burn reported in November 2026 sources: 100 units buys roughly 80 to 90 hours on T4, about 60 hours on L4 (24 GB), about 18 hours on A100 40 GB. Units expire after 90 days and no specific GPU is guaranteed.
- Z-Image Turbo runs comfortably on a T4 (FP8 or GGUF build). Wan 2.2's official workflow is tuned for 24 GB, so on a free T4 expect offloading and slow runs; the paid tiers' L4 (24 GB) matches the reference class and an A100 is comfortable, when one is assigned.
- Cost per finished video on an assigned A100 via Pro: under $1 of compute units on the LoRA path, plus setup friction. On a free T4: $0 cash, hours of wall clock, disconnect risk. Treat free Colab as a stills and proof-of-concept route.

## Hugging Face Spaces and Inference Endpoints

- Spaces hardware, official price page November 2026: T4 small 16 GB $0.40/hr, T4 medium $0.60/hr, L4 24 GB $0.80/hr, A100 large 80 GB $2.50/hr.
- Inference Endpoints (AWS list): T4 $0.50/hr, L4 $0.80/hr, A100 $2.50/hr, H100 $4.50/hr, billed per minute while the endpoint runs, including idle time.
- Z-Image Turbo runs trivially. Wan 2.2 on an L4 endpoint is the same 24GB reference class as the rental route; A100 is comfortable but pricier than renting. Endpoints are an inference API shape, not a ComfyUI session, so workflows need wrapping into a custom handler.
- Human step: account and payment method first.

## ComfyUI cloud services

- Comfy Cloud (official, cloud.comfy.org): runs on RTX PRO 6000 Blackwell cards with 96 GB VRAM, so VRAM stops being a constraint. Plans: Standard $20/month (about 4,200 credits), Creator $35/month (7,400 credits, adds importing your own models and LoRAs), Pro $100/month (21,100 credits, 1 hour max runs; Standard and Creator cap runs at 30 minutes). New users get 5 free runs with no card. Credits burn only while a workflow executes. Comfy's own reference point is that a 5 second Wan 2.2 image-to-video clip costs about 11 credits, which puts a 10-shot video near $0.50 in credits at Standard monthly rates; treat that as an estimate from their reference figure, and verify the catalogue carries the Wan 2.2 I2V workflow and the lightx2v LoRAs before subscribing.
- RunComfy and ThinkDiffusion: hosted ComfyUI machines by the hour (24 GB tiers around $1.75/hr on ThinkDiffusion; RunComfy from $0.99/hr for 16 GB tiers upward). Full machine access, so custom nodes and exact workflows carry over.

## The recommendation, in one paragraph

Rent an RTX 4090 (or 3090 for the cheapest runs) on RunPod Community Cloud with a persistent volume holding the model set: it runs the exact workflow stack unchanged for well under a dollar per finished video, even at Wan 2.2's slower render pace. Use a hosted Wan API for the first demo if speed matters more than unit cost. Keep Colab free for the stills layer and workflow testing. Every paid route needs one human step first: an account and payment method in the operator's own name.
