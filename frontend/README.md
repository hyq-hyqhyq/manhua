# Frontend

Next.js / React frontend for the comic generator.

## Run

Start the backend first on port `8000`, then:

```bash
cd comic_project/frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

The API base URL defaults to `http://localhost:8000`. Override it with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

For a server build, set the public backend URL before building:

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.example npm run build
npm run start
```

## Pages

- `/`: create a comic from story prompt, layout, and style.
- `/comics/[comic_id]`: view final comic, panels, reference sheets, Entity Pool, provider status, warnings, and revision controls.

The UI calls:

- `POST /api/comics`
- `GET /api/comics/{comic_id}/status`
- `GET /api/comics/{comic_id}`
- `POST /api/comics/{comic_id}/revise-global`
- `POST /api/comics/{comic_id}/revise-panel`
