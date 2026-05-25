# NeuroTune

Generative focus music that runs entirely on your machine. Describe how you want to feel, and a local model composes a binaural-beat session and adapts it to your feedback.

Private by design. No cloud, no telemetry.

![status: active development](https://img.shields.io/badge/status-active%20development-yellow)

_Active development. The core pipeline works end to end; rebuilding parts of the UI, adjusting llm integration alongside getting latency benchmarks and walkthroughs are still in progress._

---

## Session Types

Intent is sorted into a closed taxonomy. The selected type seeds the prompt and the schedule template.

| Type          | You'd ask for             | Targets                  |
| ------------- | ------------------------- | ------------------------ |
| Deep focus    | "heads-down for an hour"  | Sustained concentration  |
| Light focus   | "background while I read" | Low-distraction ambience |
| Creative flow | "loosen up to brainstorm" | Relaxed, open attention  |
| Calm          | "help me settle"          | Lowered arousal          |
| Sleep aid     | "wind down for bed"       | Drift toward sleep       |
| Custom        | anything off-taxonomy     | Free-form generation     |

---

## Why Local Inference

Cloud inference is the obvious path. NeuroTune deliberately does not take it.

- **Privacy is the contract.** Session text describes how you feel and think, and never leaves the machine.
- **Latency floor.** A hosted round-trip costs hundreds of milliseconds per generation, which a real-time audio path cannot absorb.
- **Cost at scale.** Per-session cloud billing compounds; local inference is amortized hardware only.
- **Offline by default.** Trains, planes, and dead zones still work.

The tradeoff is a one-time model download and a few seconds of cold-start, accepted deliberately.

---

## How It Works

A typed intent is classified, matched against past sessions that worked, and turned into a validated JSON schedule of binaural-beat parameters that streams to the browser for synthesis.

```
intent → classify → retrieve similar sessions + render prompt
       → constrained LLM → JSON schedule → validate (fallback on fail)
       → WebSocket → Tone.js synthesis → feedback → example bank
```

---

## Tech Stack

**Frontend:** Next.js 14 (App Router), Tone.js, Redux Toolkit, TypeScript

**Backend:** Python 3.10+, FastAPI, async SQLAlchemy, Pydantic, WebSocket

**ML:** HuggingFace Transformers, sentence-transformers, outlines (constrained decoding), librosa

**Storage:** SQLite by default; MySQL via Docker for development

---

## Running Locally

A CUDA GPU or Apple Silicon is strongly recommended; CPU-only inference is slow. The LLM (several GB) downloads on first backend run. Requires Python 3.10+, Node 20+, and ~16 GB RAM.

```bash
# backend
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/main.py            # http://localhost:8000  

# frontend (separate terminal)
cd frontend && npm install && npm run dev   # http://localhost:3000
```

Configuration lives in `backend/config.py`, overridable via a project-root `.env`. SQLite is the default store; MySQL is available with `docker compose up -d`. The settings most likely to matter:

| Variable       | Default                              | Why you'd change it                          |
| -------------- | ------------------------------------ | -------------------------------------------- |
| `HF_MODEL_ID`  | `Qwen/Qwen3.5-9B-Instruct`           | Swap the local model                         |
| `QUANTIZATION` | `Q8_0`                               | Trade schema fidelity for memory (`Q6_K`)    |
| `DATABASE_URL` | `sqlite+aiosqlite:///./neurotune.db` | Point at MySQL instead of SQLite             |

---

## Project Structure

```
backend/
  nlp/            intent classifier, prompt templates, example bank, validators, fallback
  llm_engine/     model loading, constrained-decoding wrapper, latency instrumentation
  audio_processor/ librosa track analysis
  routers/        REST + WebSocket endpoints
  models/         ORM + Pydantic schemas
  db/             async engine, session factory, queries
frontend/src/
  app/            Next.js routes (onboarding, session, history, settings)
  lib/            Tone.js synth, REST + WebSocket clients
  stores/         Redux Toolkit slices
```

---

MIT License In Progress
