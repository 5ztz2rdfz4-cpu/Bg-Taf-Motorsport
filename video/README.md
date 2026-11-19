# Bang Taf Motorsport: Saga MC3 TikTok edit (HyperFrames)

`bangtaf-saga/` is the HyperFrames project for the 31s TikTok video (1080x1920, 30fps).

## Edit
| Out (s) | Source IMG_0155 (s) | Beat |
|---|---|---|
| 0.00-8.20 | 1.87-10.07 | Hook: "Gen Strawberry... pinjam kereta mak, ayah, abang, akak" |
| 8.20-9.50 | 10.63-11.93 | "Sampai bila korang nak macam ni?" (zoom slam) |
| 9.50-14.73 | 14.17-19.40 | "Ada kereta mampu milik, iaitu Saga MC3" + motion B-roll |
| 14.73-20.13 | 20.00-25.40 | RM400++/bulan price infographic |
| 20.13-21.97 | 25.80-27.63 | Low maintenance / jimat minyak badges |
| 21.97-25.97 | 32.67-36.67 | CTA "tekan beg biru" |
| 25.62-31.00 | - | Outro: logo, offer, follow |

Cut: "Okay," intro, 2.3s dead pause, the "Dan... marhain" stumble, the closing "Betul ke? Gen Strawberry macam tu".

## Rebuild
`assets/source.mp4` is not committed (64 MB). Recreate it from the original iPhone clip (HDR HLG, tonemapped to SDR, voice cleaned):

```bash
ffmpeg -i IMG_0155.MOV -map 0:v:0 -map 0:a:0 \
  -vf "zscale=t=linear:npl=203:tin=arib-std-b67:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:param=0.3:desat=0,zscale=t=bt709:m=bt709:r=tv,scale=1080:1920:flags=lanczos,fps=30,format=yuv420p" \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:v libx264 -preset slow -crf 17 -g 30 \
  -af "highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7" \
  -ar 48000 -c:a aac -b:a 192k -movflags +faststart bangtaf-saga/assets/source.mp4
```

Then from `bangtaf-saga/`: `python3 tools/build_captions.py` (captions from the corrected transcript), `npx hyperframes check`, `npx hyperframes render -q delivery -o renders/out.mp4`, and normalize loudness to -14 LUFS with a two-pass `loudnorm`.

Music: original track generated locally with MusicGen (no copyright claim). SFX: bundled HyperFrames set, Pixabay Content License (`assets/sfx/CREDITS.md`).
