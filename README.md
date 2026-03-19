# ✨ StellarInk

**StellarInk** generates a personal constellation from your name using only real stars visible from your location on a specific date and time. Every star is a genuine naked-eye star from the Hipparcos catalogue. The connections trace actual letter strokes, so the constellation spells your name in the night sky.

---

## How it works

```
Enter name + date + location
         ↓
Load Hipparcos star catalogue (~5 000 naked-eye stars)
         ↓
Compute alt/az for every star from your coordinates at your time (Skyfield)
         ↓
Filter: altitude > 5°  (above the horizon)
         ↓
Each letter is defined as a set of directed strokes
         ↓
Sample 4 points along each stroke → snap to the nearest real visible star
         ↓
Connect stars in stroke order → constellation lines trace the letter
         ↓
Render in 3-D (Three.js / React Three Fiber) with IAU star name labels
```

---

## Project structure

```
StellarInk/
├── backend/
│   ├── app.py            # Flask API server
│   ├── star_utils.py     # Star catalogue, visibility, constellation engine
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx       # Input controls and layout
    │   └── StarMap.jsx   # Three.js 3-D star map
    └── package.json
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- ~50 MB disk space (Hipparcos catalogue + DE421 ephemeris, downloaded on first run)

---

## Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The server starts on `http://localhost:5000`. On first run it downloads two data files automatically:

| File           | Size   | Purpose                                  |
| -------------- | ------ | ---------------------------------------- |
| `hip_main.dat` | ~10 MB | Hipparcos star catalogue                 |
| `de421.bsp`    | ~17 MB | JPL planetary ephemeris (Earth position) |

### requirements.txt

```
flask
flask-cors
skyfield
numpy
pandas
scipy
```

---

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

### Key dependencies

| Package              | Purpose                                                |
| -------------------- | ------------------------------------------------------ |
| `@react-three/fiber` | React renderer for Three.js                            |
| `@react-three/drei`  | Helpers: `Stars`, `Text`, `Billboard`, `OrbitControls` |
| `three`              | 3-D engine                                             |
| `axios`              | HTTP client for API calls                              |

---

## API

### `POST /api/constellation`

Generate a constellation for a name at a given location and time.

**Request body**

```json
{
  "name": "JISHNU",
  "latitude": 13.0,
  "longitude": 77.7,
  "date": "2026-03-15",
  "time": "20:00"
}
```

**Response**

```json
{
  "name": "JISHNU",
  "location": { "lat": 13.0, "lon": 77.7 },
  "datetime": "2026-03-15 20:00",
  "total_visible_stars": 2147,
  "star_count": 38,
  "constellation_stars": [
    {
      "x": 182.4,
      "y": 43.1,
      "x_norm": 0.51,
      "y_norm": 0.72,
      "mag": 1.35,
      "ra": 6.75,
      "dec": -16.7,
      "hip_id": 32349,
      "star_name": "Adara",
      "letter": "J"
    }
  ],
  "connections": [
    [0, 1],
    [1, 2],
    [3, 4]
  ]
}
```

Each star in `constellation_stars` includes its IAU common name (e.g. `"Aldebaran"`) or `"HIP XXXXX"` for unnamed stars, and the letter it belongs to.

### `GET /api/health`

```json
{ "status": "healthy", "stars_loaded": 4995 }
```

---

## Star catalogue

StellarInk uses the **Hipparcos catalogue** (ESA, 1997), filtered to stars with apparent magnitude < 6 — roughly the limit of naked-eye visibility. This gives ~5 000 stars.

Each star contributes:

- Right Ascension and Declination (J2000)
- Visual magnitude
- Hipparcos ID (used to look up the IAU common name)

**Skyfield** converts RA/Dec -> altitude/azimuth for the observer's location and time using the DE421 ephemeris for Earth's position. Stars below 5° altitude are excluded to account for horizon obstructions and atmospheric refraction.

---

## Constellation engine

### Letter strokes

Every supported letter (A–Z) is defined as an ordered list of directed strokes in normalised (0–1, 0–1) space. For example:

```
H  →  left leg (bottom→top)
      right leg (bottom→top)
      crossbar (left→right)
```

This means connections follow pen-stroke order rather than arbitrary proximity, so the rendered lines actually look like the letter.

### Star selection

For each stroke, `STARS_PER_STROKE = 4` points are sampled evenly along the segment using linear interpolation. A `scipy.spatial.KDTree` finds the nearest visible star to each sample point. Stars are deduplicated across strokes within the same letter.

### Connections

Stars are connected in sample-point order within each stroke. The result is a chain that traces the stroke from start to end, producing legible letter shapes.

---

## 3-D viewer controls

| Action            | Control                 |
| ----------------- | ----------------------- |
| Rotate            | Left-click + drag       |
| Zoom              | Scroll wheel            |
| Pan               | Right-click + drag      |
| Auto-rotate       | On by default (0.4 rpm) |
| Toggle star names | Button top-right        |

Star brightness is mapped to sphere radius. Each constellation star renders a bright core plus a soft glow halo. Background stars use Three.js `<Stars>` with 3 000 particles.

### Star name labels

Each constellation star displays:

- Its IAU common name or HIP ID in lavender (`#e8d8ff`)
- The letter it belongs to in gold (`[J]`)

Labels use `@react-three/drei`'s `Billboard` so they always face the camera regardless of rotation. The **Show/Hide Names** toggle in the top-right corner of the viewer controls visibility.

---

## Extending the project

**More stars per letter** — increase `STARS_PER_STROKE` in `star_utils.py` (currently 4). Higher values produce denser, smoother letter shapes at the cost of selecting more stars.

**Lower-case support** — add entries to `LETTER_STROKES` for `a`–`z` and remove the `.upper()` call in `create_constellation_from_text`.

**Export as image** — add a `<button>` that calls `gl.domElement.toDataURL()` inside a `useThree()` hook and triggers a download.

**Share link** — encode the name, date, and coordinates as URL query parameters so a generated constellation can be bookmarked or shared.

**More IAU names** — the full IAU Working Group on Star Names list (339 stars) is available at `https://www.iau.org/public/themes/naming_stars/`. Extend the `IAU_NAMES` dict in `star_utils.py`.

---

## Limitations

- Time input is treated as **UTC**. Add a timezone offset field if you want local time to be correct automatically.
- The letter-to-star mapping is deterministic for a given sky but will differ night to night as different stars rise and set.
- Very short names (1–2 characters) or names with unsupported characters (digits, punctuation) are silently skipped.
- The Flask development server is single-threaded; each request blocks while ~5000 altitude calculations run (~3 s on a modern laptop). For production use, run under Gunicorn with a pre-computed nightly cache.

---

## Acknowledgements

- [Hipparcos Catalogue](https://www.cosmos.esa.int/web/hipparcos) — ESA
- [Skyfield](https://rhodesmill.org/skyfield/) — Brandon Rhodes
- [DE421 Ephemeris](https://naif.jpl.nasa.gov/naif/data.html) — NASA/JPL
- [React Three Fiber](https://docs.pmnd.rs/react-three-fiber) — Poimandres
- [IAU Star Names](https://www.iau.org/public/themes/naming_stars/) — International Astronomical Union
