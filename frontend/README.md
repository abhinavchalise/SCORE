# NeuroTune Frontend

Next.js UI for the adaptive focus-music platform. It takes a
natural-language intent, requests a binaural-beat schedule from the backend, and
synthesizes the audio in the browser with Tone.js. Client state is held in Redux Toolkit.

See the project root `README.md` for the full system overview.

## Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Scripts

- `npm run dev` — start the dev server.
- `npm run build` — production build.
- `npm run lint` — run ESLint.
- `npm run format` — format with Prettier.
