"""Synthesize original background music + SFX (no external samples)."""
import sys, os, wave
import numpy as np
from scipy import signal

SR = 48000
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x, stereo=None):
    if stereo is None:
        x = np.stack([x, x], 1) if x.ndim == 1 else x
    else:
        x = stereo
    peak = np.max(np.abs(x)) + 1e-9
    x = x / peak * 0.89
    d = (x * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(d.tobytes())


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def env_ad(n, a, d):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / d)
    return e


def lp(x, f, order=2):
    b, a = signal.butter(order, min(f / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, x)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# ---------------------------------------------------------------- drums
def kick(dur=0.45):
    t = t_(dur)
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.22)
    click = hp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.004) * 0.3
    return np.tanh((x + click) * 1.6)


def clap(dur=0.3):
    t = t_(dur)
    n = bp(rng.standard_normal(len(t)), 900, 5000)
    e = np.zeros_like(t)
    for o in (0, 0.011, 0.022):
        e += (t >= o) * np.exp(-np.maximum(t - o, 0) / (0.009 if o < 0.02 else 0.12))
    return n * e * 0.8


def hat(dur=0.08, open_=False):
    t = t_(dur if not open_ else 0.25)
    n = hp(rng.standard_normal(len(t)), 7500, 4)
    return n * np.exp(-t / (0.018 if not open_ else 0.08)) * 0.5


# ---------------------------------------------------------------- synths
def saw(f, t):
    return signal.sawtooth(2 * np.pi * f * t)


def pad_chord(notes, dur):
    t = t_(dur)
    x = np.zeros(len(t))
    for m in notes:
        for det in (-0.12, 0.0, 0.12):
            x += saw(mtof(m + det), t)
    x = lp(x, 1400, 2)
    a = np.minimum(t / 0.25, 1) * np.minimum((dur - t) / 0.3, 1).clip(0, 1)
    return x * a * 0.05


def pluck(m, dur=0.35):
    t = t_(dur)
    x = signal.square(2 * np.pi * mtof(m) * t, 0.3) * 0.5 + saw(mtof(m + 12), t) * 0.2
    x = lp(x, 3000)
    return x * env_ad(len(t), 0.003, 0.11) * 0.33


def bass(m, dur):
    t = t_(dur)
    f = mtof(m)
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    e = np.minimum(t / 0.01, 1) * np.minimum((dur - t) / 0.04, 1).clip(0, 1)
    return np.tanh(x * 1.4) * e * 0.55


# ---------------------------------------------------------------- music
BPM = 102
beat = 60 / BPM
bar = beat * 4
DUR = 62.0
N = int(DUR * SR)
L = np.zeros(N); R = np.zeros(N)


def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i >= N: return
    j = min(N, i + len(x))
    buf[i:j] += x[: j - i] * gain


# progression (A minor): Am - F - C - G   (roots in midi)
prog = [(57, [69, 72, 76]), (53, [65, 69, 72]), (48, [64, 67, 72]), (55, [62, 67, 71])]
arp_pat = [0, 2, 1, 2, 0, 2, 1, 2]
nbars = int(DUR / bar) + 1
for b in range(nbars):
    t0 = b * bar
    root, ch = prog[b % 4]
    section = "intro" if b < 2 else ("main")
    # pad
    p = pad_chord(ch, bar)
    add(L, p, t0, 1.0); add(R, p, t0, 1.0)
    # arp plucks 8ths
    if b >= 1:
        for k in range(8):
            m = ch[arp_pat[k]] + (12 if k % 4 == 3 else 0)
            x = pluck(m)
            pan = 0.3 if k % 2 else -0.3
            add(L, x, t0 + k * beat / 2, 1 - pan); add(R, x, t0 + k * beat / 2, 1 + pan)
    if section == "main":
        # bass: root on 1, and-of-2, 3
        for (pos, ln) in ((0, 1.4), (1.5, 0.45), (2.0, 1.0), (3.5, 0.45)):
            x = bass(root - 12, ln * beat)
            add(L, x, t0 + pos * beat); add(R, x, t0 + pos * beat)
        # kick
        for pos in (0, 1.75, 2.0, 2.5) if b % 2 else (0, 2.0, 2.75):
            k = kick(); add(L, k, t0 + pos * beat, 0.9); add(R, k, t0 + pos * beat, 0.9)
        # clap on 2 & 4
        for pos in (1, 3):
            c = clap(); add(L, c, t0 + pos * beat, 0.55); add(R, c, t0 + pos * beat, 0.55)
        # hats 8ths + 16th rolls at bar end
        for k in range(8):
            h = hat(open_=(k == 7 and b % 4 == 3))
            add(L, h, t0 + k * beat / 2, 0.35 if k % 2 else 0.22)
            add(R, h, t0 + k * beat / 2 + 0.004, 0.35 if k % 2 else 0.22)
        if b % 2 == 1:
            for k in range(4):
                h = hat(); add(L, h, t0 + 3.5 * beat + k * beat / 8, 0.2); add(R, h, t0 + 3.5 * beat + k * beat / 8, 0.2)

# end: gentle fade last 2.5s
fade = np.ones(N)
fl = int(2.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
mix = np.stack([L * fade, R * fade], 1)
mix = np.tanh(mix * 1.2)
save("music.wav", None, stereo=mix)

# ---------------------------------------------------------------- SFX
# whoosh: noise through sweeping bandpass, swell
d = 0.55; t = t_(d); n = rng.standard_normal(len(t))
out = np.zeros(len(t)); blk = 256
fc = 300 * (25 ** np.sin(np.pi * t / d))
for i in range(0, len(t), blk):
    f = fc[i]
    seg = bp(n[max(0, i - 2048): i + blk], f * 0.7, min(f * 1.4, 20000))[-blk:]
    out[i:i + len(seg)] = seg[: len(out[i:i + blk])]
out *= np.sin(np.pi * t / d) ** 2
save("whoosh.wav", out)

# impact / boom (sub drop + noise burst)
d = 1.4; t = t_(d)
f = 38 + 90 * np.exp(-t / 0.08)
boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
burst = lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.06) * 0.6
save("impact.wav", np.tanh((boom + burst) * 1.8))

# pop (UI bubble)
d = 0.14; t = t_(d)
f = 500 + 900 * (1 - np.exp(-t / 0.02))
save("pop.wav", np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(len(t), 0.002, 0.035))

# tick/click (checklist)
d = 0.06; t = t_(d)
save("tick.wav", hp(rng.standard_normal(len(t)), 2000) * np.exp(-t / 0.006) + np.sin(2 * np.pi * 2200 * t) * np.exp(-t / 0.01))

# success ding (two-note bell)
d = 0.9; t = t_(d); x = np.zeros(len(t))
for on, m in ((0, 84), (0.09, 91)):
    tt = np.maximum(t - on, 0); g = (t >= on)
    for h, a in ((1, 1), (2.76, 0.35), (5.4, 0.12)):
        x += g * np.sin(2 * np.pi * mtof(m) * h * tt) * np.exp(-tt / (0.35 / h ** 0.5)) * a
save("ding.wav", x)

# wrong / buzz
d = 0.32; t = t_(d)
x = signal.square(2 * np.pi * 140 * t) * 0.5 + signal.square(2 * np.pi * 147 * t) * 0.5
x = lp(x, 1800) * np.minimum(t / 0.005, 1) * np.minimum((d - t) / 0.05, 1)
save("buzz.wav", x)

# riser (noise + rising tone, 1.6s)
d = 1.6; t = t_(d)
f = 200 * (8 ** (t / d))
tone = saw(1, t) * 0
tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
nz = hp(rng.standard_normal(len(t)), 1500) * 0.4
x = (tone + nz) * (t / d) ** 2
save("riser.wav", x)

# camera shutter-like "swipe tick" for cuts (short)
d = 0.18; t = t_(d)
x = bp(rng.standard_normal(len(t)), 1500, 8000) * np.exp(-t / 0.03)
save("swipe.wav", x)

# cash / coin chime (for rate)
d = 0.7; t = t_(d); x = np.zeros(len(t))
for on, m in ((0, 96), (0.06, 100), (0.12, 103)):
    tt = np.maximum(t - on, 0); g = (t >= on)
    x += g * np.sin(2 * np.pi * mtof(m) * tt) * np.exp(-tt / 0.15)
save("coin.wav", x)

print("ok")
