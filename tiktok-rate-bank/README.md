# TikTok edit: "Kenapa rate loan kereta beza?" (Bang Taf Motorsport)

HyperFrames project, 1080x1920, 58 s.

- `index.html`: the whole edit (hook, infographic cards, motion-graphic B-roll, word captions, zoom/reframe on jump cuts, SFX, music and the outro logo).
- `assets/aroll.mp4`: **not committed** (too big). It is the talking-head clip with silences removed, the voice cleaned and the iPhone HDR tonemapped to SDR. Rebuild it from `IMG_0150.MOV` (see the cut list in `index.html` → `CUTS`).
- `assets/music.mp3`, `assets/sfx/*`: original audio made by `tools/synth_audio.py`, so there are no copyright issues.

Render: `npx hyperframes@0.9.70 render -q high -f 30 -o renders/master.mp4`
