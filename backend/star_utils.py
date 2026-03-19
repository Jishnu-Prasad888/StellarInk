import numpy as np
from skyfield.api import load, Topos, Star
from skyfield.data import hipparcos
from scipy.spatial import KDTree

# ---------------------------------------------------------------------------
# IAU common star names keyed by Hipparcos ID
# (subset of the brightest / most well-known)
# ---------------------------------------------------------------------------
IAU_NAMES = {
    677: "Alpheratz", 746: "Caph", 1067: "Algenib", 2081: "Ankaa",
    3179: "Schedar", 3419: "Diphda", 4427: "Mirach", 5447: "Achernar",
    6686: "Almaak", 7588: "Hamal", 8903: "Polaris", 9884: "Acamar",
    11767: "Polaris", 14135: "Menkar", 14576: "Algol", 15863: "Almach",
    17702: "Mirfak", 21421: "Aldebaran", 24436: "Rigel", 24608: "Capella",
    25336: "Bellatrix", 25428: "Elnath", 25930: "Alnilam", 26207: "Mintaka",
    26311: "Nihal", 26634: "Alnitak", 27989: "Betelgeuse", 28360: "Menkib",
    30122: "Canopus", 30324: "Alhena", 31681: "Sirius", 32349: "Adara",
    33579: "Wezen", 34444: "Mirzam", 36850: "Castor", 37279: "Procyon",
    37826: "Pollux", 39429: "Naos", 41037: "Avior", 44816: "Suhail",
    45238: "Miaplacidus", 46390: "Alphard", 49669: "Regulus", 50583: "Algieba",
    54061: "Dubhe", 57632: "Denebola", 57939: "Porrima", 59774: "Algorab",
    60718: "Acrux", 61084: "Gacrux", 61932: "Mimosa", 62956: "Alioth",
    63608: "Cor Caroli", 65378: "Mizar", 65474: "Spica", 67301: "Alkaid",
    68702: "Hadar", 69673: "Arcturus", 71683: "Rigil Kentaurus",
    72105: "Izar", 72607: "Kochab", 74785: "Zubenelgenubi",
    76267: "Alphecca", 77070: "Unukalhai", 78401: "Atria",
    80112: "Yed Prior", 80763: "Antares", 84012: "Sabik",
    85670: "Rasalgethi", 85927: "Rasalhague", 86032: "Cebalrai",
    87833: "Etamin", 90185: "Kaus Australis", 91262: "Vega",
    92855: "Sheliak", 93194: "Nunki", 95947: "Albireo",
    97278: "Tarazed", 97649: "Altair", 100453: "Peacock",
    102098: "Deneb", 105199: "Sadalsuud", 107315: "Enif",
    109268: "Sadalmelik", 110997: "Fomalhaut", 112029: "Markab",
    113368: "Fomalhaut", 677: "Alpheratz",
}


def _interpolate_stroke(p0, p1, n=5):
    """Return n evenly-spaced points along the segment p0→p1."""
    return [
        [p0[0] + t * (p1[0] - p0[0]),
         p0[1] + t * (p1[1] - p0[1])]
        for t in np.linspace(0, 1, n)
    ]


# ---------------------------------------------------------------------------
# Letter definitions: list of strokes.
# Each stroke is [start_point, end_point] in normalised (0-1, 0-1) space.
# y=0 = bottom,  y=1 = top   (will be flipped to screen coords later)
# ---------------------------------------------------------------------------
LETTER_STROKES = {
    'A': [
        [(0.1, 0.0), (0.5, 1.0)],   # left diagonal up
        [(0.5, 1.0), (0.9, 0.0)],   # right diagonal down
        [(0.25, 0.45), (0.75, 0.45)],  # crossbar
    ],
    'B': [
        [(0.15, 0.0), (0.15, 1.0)],          # vertical spine
        [(0.15, 1.0), (0.65, 1.0)],          # top horizontal
        [(0.65, 1.0), (0.85, 0.82)],         # top curve out
        [(0.85, 0.82), (0.65, 0.55)],        # top curve in
        [(0.65, 0.55), (0.15, 0.55)],        # mid horizontal
        [(0.15, 0.55), (0.9, 0.55)],         # mid horizontal (lower bump)
        [(0.9, 0.55), (0.9, 0.18)],          # lower curve right
        [(0.9, 0.18), (0.65, 0.0)],          # lower curve bottom
        [(0.65, 0.0), (0.15, 0.0)],          # bottom horizontal
    ],
    'C': [
        [(0.85, 0.82), (0.5, 1.0)],
        [(0.5, 1.0), (0.15, 0.75)],
        [(0.15, 0.75), (0.15, 0.25)],
        [(0.15, 0.25), (0.5, 0.0)],
        [(0.5, 0.0), (0.85, 0.18)],
    ],
    'D': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.6, 1.0)],
        [(0.6, 1.0), (0.9, 0.7)],
        [(0.9, 0.7), (0.9, 0.3)],
        [(0.9, 0.3), (0.6, 0.0)],
        [(0.6, 0.0), (0.15, 0.0)],
    ],
    'E': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.85, 1.0)],
        [(0.15, 0.5), (0.7, 0.5)],
        [(0.15, 0.0), (0.85, 0.0)],
    ],
    'F': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.85, 1.0)],
        [(0.15, 0.5), (0.7, 0.5)],
    ],
    'G': [
        [(0.85, 0.82), (0.5, 1.0)],
        [(0.5, 1.0), (0.15, 0.75)],
        [(0.15, 0.75), (0.15, 0.25)],
        [(0.15, 0.25), (0.5, 0.0)],
        [(0.5, 0.0), (0.85, 0.18)],
        [(0.85, 0.18), (0.85, 0.5)],
        [(0.85, 0.5), (0.55, 0.5)],
    ],
    'H': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.85, 0.0), (0.85, 1.0)],
        [(0.15, 0.5), (0.85, 0.5)],
    ],
    'I': [
        [(0.3, 1.0), (0.7, 1.0)],
        [(0.5, 1.0), (0.5, 0.0)],
        [(0.3, 0.0), (0.7, 0.0)],
    ],
    'J': [
        [(0.3, 1.0), (0.7, 1.0)],
        [(0.6, 1.0), (0.6, 0.2)],
        [(0.6, 0.2), (0.4, 0.0)],
        [(0.4, 0.0), (0.2, 0.2)],
    ],
    'K': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 0.5), (0.85, 1.0)],
        [(0.15, 0.5), (0.85, 0.0)],
    ],
    'L': [
        [(0.15, 1.0), (0.15, 0.0)],
        [(0.15, 0.0), (0.85, 0.0)],
    ],
    'M': [
        [(0.1, 0.0), (0.1, 1.0)],
        [(0.1, 1.0), (0.5, 0.5)],
        [(0.5, 0.5), (0.9, 1.0)],
        [(0.9, 1.0), (0.9, 0.0)],
    ],
    'N': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.85, 0.0)],
        [(0.85, 0.0), (0.85, 1.0)],
    ],
    'O': [
        [(0.5, 1.0), (0.15, 0.75)],
        [(0.15, 0.75), (0.15, 0.25)],
        [(0.15, 0.25), (0.5, 0.0)],
        [(0.5, 0.0), (0.85, 0.25)],
        [(0.85, 0.25), (0.85, 0.75)],
        [(0.85, 0.75), (0.5, 1.0)],
    ],
    'P': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.65, 1.0)],
        [(0.65, 1.0), (0.85, 0.82)],
        [(0.85, 0.82), (0.85, 0.65)],
        [(0.85, 0.65), (0.65, 0.5)],
        [(0.65, 0.5), (0.15, 0.5)],
    ],
    'Q': [
        [(0.5, 1.0), (0.15, 0.75)],
        [(0.15, 0.75), (0.15, 0.25)],
        [(0.15, 0.25), (0.5, 0.0)],
        [(0.5, 0.0), (0.85, 0.25)],
        [(0.85, 0.25), (0.85, 0.75)],
        [(0.85, 0.75), (0.5, 1.0)],
        [(0.6, 0.35), (0.9, 0.05)],   # tail
    ],
    'R': [
        [(0.15, 0.0), (0.15, 1.0)],
        [(0.15, 1.0), (0.65, 1.0)],
        [(0.65, 1.0), (0.85, 0.82)],
        [(0.85, 0.82), (0.85, 0.65)],
        [(0.85, 0.65), (0.65, 0.5)],
        [(0.65, 0.5), (0.15, 0.5)],
        [(0.5, 0.5), (0.85, 0.0)],   # leg
    ],
    'S': [
        [(0.85, 0.82), (0.5, 1.0)],
        [(0.5, 1.0), (0.15, 0.82)],
        [(0.15, 0.82), (0.15, 0.6)],
        [(0.15, 0.6), (0.5, 0.5)],
        [(0.5, 0.5), (0.85, 0.4)],
        [(0.85, 0.4), (0.85, 0.18)],
        [(0.85, 0.18), (0.5, 0.0)],
        [(0.5, 0.0), (0.15, 0.18)],
    ],
    'T': [
        [(0.1, 1.0), (0.9, 1.0)],
        [(0.5, 1.0), (0.5, 0.0)],
    ],
    'U': [
        [(0.15, 1.0), (0.15, 0.25)],
        [(0.15, 0.25), (0.5, 0.0)],
        [(0.5, 0.0), (0.85, 0.25)],
        [(0.85, 0.25), (0.85, 1.0)],
    ],
    'V': [
        [(0.1, 1.0), (0.5, 0.0)],
        [(0.5, 0.0), (0.9, 1.0)],
    ],
    'W': [
        [(0.1, 1.0), (0.25, 0.0)],
        [(0.25, 0.0), (0.5, 0.55)],
        [(0.5, 0.55), (0.75, 0.0)],
        [(0.75, 0.0), (0.9, 1.0)],
    ],
    'X': [
        [(0.1, 1.0), (0.9, 0.0)],
        [(0.9, 1.0), (0.1, 0.0)],
    ],
    'Y': [
        [(0.1, 1.0), (0.5, 0.5)],
        [(0.9, 1.0), (0.5, 0.5)],
        [(0.5, 0.5), (0.5, 0.0)],
    ],
    'Z': [
        [(0.1, 1.0), (0.9, 1.0)],
        [(0.9, 1.0), (0.1, 0.0)],
        [(0.1, 0.0), (0.9, 0.0)],
    ],
}

# Stars per stroke segment (controls density / resolution of each letter)
STARS_PER_STROKE = 4


class StarConstellationGenerator:
    def __init__(self):
        print("Loading star catalog...")
        self.ts = load.timescale()

        with load.open(hipparcos.URL) as f:
            self.stars_df = hipparcos.load_dataframe(f)

        self.stars_df = self.stars_df[self.stars_df['magnitude'] < 6]
        print(f"Loaded {len(self.stars_df)} stars")

        print("Loading ephemeris...")
        self.eph = load('de421.bsp')
        self.earth = self.eph['earth']

        self.star_objects = []
        self.star_coords = []

        for hip_id, row in self.stars_df.iterrows():
            star = Star(ra_hours=row['ra_hours'], dec_degrees=row['dec_degrees'])
            self.star_objects.append(star)
            self.star_coords.append([row['ra_hours'], row['dec_degrees']])

        print(f"Ready with {len(self.star_objects)} stars")

    # ------------------------------------------------------------------
    def get_visible_stars(self, lat, lon, date_str, time_str):
        year, month, day = map(int, date_str.split('-'))
        hour, minute = map(int, time_str.split(':'))

        location = self.earth + Topos(latitude_degrees=lat, longitude_degrees=lon)
        t = self.ts.utc(year, month, day, hour, minute, 0)

        visible_stars = []
        print(f"Calculating visible stars for {lat}, {lon} at {date_str} {time_str}")

        total = len(self.star_objects)
        for i, star in enumerate(self.star_objects):
            if i % 500 == 0:
                print(f"Processing star {i}/{total}")
            try:
                astrometric = location.at(t).observe(star)
                apparent = astrometric.apparent()
                alt, az, distance = apparent.altaz()
                if alt.degrees > 5:
                    magnitude = self.stars_df.iloc[i]['magnitude']
                    hip_id = int(self.stars_df.index[i])
                    visible_stars.append({
                        'x': float(az.degrees),
                        'y': float(alt.degrees),
                        'mag': float(magnitude),
                        'ra': float(self.star_coords[i][0]),
                        'dec': float(self.star_coords[i][1]),
                        'hip_id': hip_id,
                        'star_name': IAU_NAMES.get(hip_id, f"HIP {hip_id}"),
                    })
            except Exception:
                continue

        print(f"Found {len(visible_stars)} visible stars")

        if visible_stars:
            xs = [s['x'] for s in visible_stars]
            ys = [s['y'] for s in visible_stars]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            xr = x_max - x_min or 1
            yr = y_max - y_min or 1
            for s in visible_stars:
                s['x_norm'] = (s['x'] - x_min) / xr
                s['y_norm'] = (s['y'] - y_min) / yr

        return visible_stars

    # ------------------------------------------------------------------
    def create_constellation_from_text(self, stars, text, width=800, height=600):
        """
        For each letter build stroke-aligned star chains so the connections
        actually look like the letter.  Returns:
          result_stars  – list of star dicts, each with 'letter' field added
          connections   – list of [i, j] index pairs into result_stars
        """
        if len(stars) < 10:
            print(f"Not enough visible stars ({len(stars)})")
            return [], []

        text = text.upper()
        star_positions = np.array([[s['x_norm'] * width, s['y_norm'] * height]
                                   for s in stars])
        star_tree = KDTree(star_positions)

        # We will accumulate final stars and connections into these
        result_stars = []
        connections = []
        used_star_indices = {}   # global star index → result index (dedup)

        n_chars = len([c for c in text if c in LETTER_STROKES])
        if n_chars == 0:
            return [], []

        char_w = width  / (n_chars + 1)
        char_h = height * 0.8
        y_baseline = height * 0.1   # bottom of letters in screen coords

        char_slot = 0
        for char in text:
            if char not in LETTER_STROKES:
                continue

            strokes = LETTER_STROKES[char]
            x_offset = (char_slot + 0.5) * char_w

            # ----------------------------------------------------------
            # Build the ordered chain of target points for every stroke
            # stroke_chains[k] = list of result indices (in result_stars)
            # ----------------------------------------------------------
            stroke_chains = []

            for (x0n, y0n), (x1n, y1n) in strokes:
                # Convert normalised letter coords → canvas coords
                # y is flipped: y_norm=1 → top of letter, y_norm=0 → bottom
                def to_canvas(xn, yn):
                    cx = x_offset + (xn - 0.5) * char_w * 0.75
                    cy = y_baseline + yn * char_h
                    return cx, cy

                cx0, cy0 = to_canvas(x0n, y0n)
                cx1, cy1 = to_canvas(x1n, y1n)

                # Sample points along this stroke
                sample_pts = _interpolate_stroke(
                    [cx0, cy0], [cx1, cy1], n=STARS_PER_STROKE
                )

                chain = []
                for pt in sample_pts:
                    dist, idx = star_tree.query(pt)
                    idx = int(idx)

                    if idx in used_star_indices:
                        res_idx = used_star_indices[idx]
                    else:
                        star = dict(stars[idx])
                        star['letter'] = char
                        res_idx = len(result_stars)
                        result_stars.append(star)
                        used_star_indices[idx] = res_idx

                    if chain and chain[-1] != res_idx:
                        chain.append(res_idx)
                    elif not chain:
                        chain.append(res_idx)

                stroke_chains.append(chain)

            # Connect consecutive stars within each stroke
            for chain in stroke_chains:
                for a, b in zip(chain, chain[1:]):
                    edge = [a, b]
                    if edge not in connections and [b, a] not in connections:
                        connections.append(edge)

            char_slot += 1

        print(f"Constellation: {len(result_stars)} stars, {len(connections)} connections")
        return result_stars, connections