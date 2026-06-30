# SCORE

Generate focus and study music tailored to what you're doing, from an AI model that runs entirely on your own machine. No cloud, no telemetry.

You pick a focus style, and a local language model composes a binaural-beat session (binaural beats: two slightly offset tones the ear blends into one steady pulse) that plays in your browser and is built to adapt to your feedback over time.

![status: active development](https://img.shields.io/badge/status-active%20development-yellow)

**Demo:** runs locally in a few commands; see [Run, Build, Test](#run-build-test).

---

## At a Glance

You choose a focus style (deep focus, light focus, sleep aid, and more), and SCORE generates a custom session of binaural-beat parameters that change over time to hold your attention. The session streams to your browser, plays instantly, and you can adjust any setting live.

Everything runs locally: an 8B-parameter model on a consumer GPU, with every generated session checked for validity before it plays.

**Status.** The core pipeline runs end to end: pick a style, a local model generates a validated session, and it plays in the browser. In progress: text intent understanding, retrieval of past sessions you rated well, and tighter server-side validation.

---

## Architecture

You choose an intent, which seeds a prompt for a local language model. The model returns a JSON session of binaural-beat parameters across time. The session is checked for schema, value ranges, and smooth transitions; anything invalid falls back to a safe per-intent preset. The valid session streams to the browser, where Tone.js plays it with smooth ramps, and your feedback feeds back into the examples that shape the next one.

```mermaid
flowchart LR
    A[Intent] --> B[Classify]
    B --> C[Retrieve examples]
    C --> D[Local LLM]
    D --> E{Valid?}
    E -->|yes| F[Stream to browser]
    E -->|no| G[Fallback]
    G --> F
    F --> H[Synthesize audio]
```

---

## Features

**Intent-based sessions.** You pick a focus style (deep focus, light focus, creative flow, calm, sleep aid) and describe it in your own words. The choice seeds both the prompt and the session template. A small classifier sorts your input into the fixed set of styles and generates schedule based on intent.

**Real-time control.** Beat frequency, tempo, and audio layers ramp smoothly across each step of the session, and you can override any slider while it plays. Tone.js ramps every parameter on the client so nothing jumps abruptly.

**Learns from your feedback.** Sessions you rate well are designed to bias the next generation as examples, improving results rather than retraining the model.

**Validated output.** Every session is checked against a fixed schema and value ranges before it plays. Constrained decoding will bound the JSON as the model generates it, and a per-intent fallback catches anything invalid.

---

## Key Decisions and Tradeoffs

| Decision | Why | Alternative rejected |
|---|---|---|
| Local inference, not a cloud API | Session text describes how you feel and think so it should not leave your machine. Cloud also adds a latency floor and per-session cost. | Hosted API (forces telemetry by default, 200-800 ms network latency floor, unnecessary cost at session scale) |
| Fixed set of session styles | Canonical labels keep accuracy meaningful and give the fallback concrete targets | Open-set classification by similarity |
| Retrieval before fine-tuning | Cheapest signal that compounds with use: no training cost, no GPU, improvement at generation time | LoRA fine-tuning (data to be added) |
| Constrained decoding | Bounds the JSON structure as the model generates, removing the malformed-output retry path | Generate then validate-and-retry (adds a latency tail and a failure path) |
| llama.cpp GGUF for serving, HuggingFace for training | llama.cpp Q8_0 serving cut end-to-end latency from 34 s to 15 s on a 12 GB card. The HuggingFace stack with bitsandbytes stays the QLoRA fine-tuning home. | One runtime for both (rejected: serving speed and training tooling pull in different directions) |
| Q8_0 quant for serving | Output is JSON, so quantization noise becomes a validation error rather than slightly worse meaning. High precision protects schema fidelity, the critical path. | Q4 (rejected for now: faster but lower raw validity, traded against fidelity) |

---

## Designed for Focus

The focus-first design is enforced in code, not left to the model:

- **Smooth transitions.** No parameter jumps more than 20% of its range per second
- **You stay in control.** Sliders override the model in real time, and each edit becomes a feedback signal.
- **Instant stop.** A keyboard shortcut and a large button stop audio with no confirmation dialog, so sensory overwhelm is never trapped behind a multi-step flow.

---

## Benchmarks

Measured on an RTX 3060 (12 GB), Qwen3-8B.

- Serving on llama.cpp with a GGUF `Q8_0` model cut end-to-end latency from 34.3 s (HuggingFace 8-bit) to 15.2 s P50, and peak GPU from 10.2 GB to 8.7 GB.
- Every delivered schedule is valid: constrained decoding fixes the JSON structure and a deterministic clamp pins numeric ranges and smoothing, so schedules reach the player with zero retry (0% fallback over a 30-session run, both backends).
- Non-LLM pipeline stages run far under budget: intent classify 4 ms, render + retrieval under 2 ms, validation under 1 ms (P50).
- The local 8B model still has a latency at ~12.6 s P50 generation. Reaching sub-3 s needs better optimization.

---

## Run, Build, Test

**Requires:** Python 3.10+, Node 20+, 16 GB RAM. A CUDA GPU or Apple Silicon is recommended. Docker optional. The model downloads on first backend run which will be several gigabytes.

```bash
git clone https://github.com/Abhi6310/SCORE.git
cd SCORE

# backend
python -m venv .venv && source .venv/bin/activate
pip install -e ./backend

# frontend (separate terminal)
cd frontend && npm install

# optional: MySQL via Docker
docker compose up -d
```

Run both servers in separate terminals:

```bash
# terminal 1: backend (downloads the model on first run)
source .venv/bin/activate && python backend/main.py

# terminal 2: frontend
cd frontend && npm run dev  #http://localhost:3000
```

Configuration lives in `backend/config.py`, overridable via a project-root `.env`:

---

## Tech Stack

**Frontend:** Next.js 14 (App Router), Tone.js, Redux Toolkit, TypeScript

**Backend:** Python 3.10+, FastAPI, async SQLAlchemy, Pydantic, WebSocket

**ML:** llama.cpp (GGUF serving), HuggingFace Transformers, sentence-transformers, constrained decoding (GBNF on llama.cpp, outlines on the HF path), librosa. Serving runs Qwen3-8B as a GGUF `Q8_0` model on llama.cpp; the HuggingFace path with bitsandbytes (`8bit`, `4bit` for tighter memory) stays the fine-tuning home. `LLM_BACKEND` selects between them.

**Storage:** SQLite by default; MySQL via Docker for development

---

## Known Limitations

- **Single-user, local deployment by design.** No multi-tenant serving and no hosted endpoint; the on-device story is the point.
- **Adaptation ships as retrieval first.** Classifier retraining and preference tuning are deferred until the retrieval signal plateaus.
- **On-device 8B generation is the latency cost.** llama.cpp Q8_0 serving brings end-to-end P50 to ~15 s on a 12 GB card, down from ~34 s on the HuggingFace stack. Sub-3 s would need a lighter GGUF quant.

---

## Project Structure

```
SCORE/
├── backend/
│   ├── nlp/             prompt classifiers, templates, validators
│   ├── llm_engine/      llm model and decoding
│   ├── audio_processor/ librosa-driven track analysis
│   ├── routers/         REST + WebSocket endpoints
│   ├── models/          ORM + Pydantic schemas
│   ├── db/              async session engine
│   └── config.py
├── frontend/src/
│   ├── app/             Next.js routes
│   ├── lib/             Tone.js synth, REST + WebSocket clients
│   └── stores/          Redux Toolkit slices
└── docker-compose.yml
```

---

MIT License
