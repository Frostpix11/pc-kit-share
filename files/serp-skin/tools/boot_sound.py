#!/usr/bin/env python3
"""serp-skin: «Пробуждение»'s sound, synthesized (numpy), on the show's clock (3.4 s, p × 3.4):
an airy swell out of the quiet, the drop hitting the water at 0.48 s (p 0.14), a warm chord rising
under the halo while six glass notes climb with its light, a soft chime as the screen opens (2.9 s).
Kept above ~180 Hz (laptop speakers).   boot_sound.py OUT.wav
"""
import sys
import wave

import numpy as np

SR = 48000
rng = np.random.default_rng(1113)


def t_(sec):
    return np.arange(int(SR * sec)) / SR


def place(buf, sig, at):
    i = int(at * SR)
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s
        y[i] = s
    return y


def reverb(x, mix=0.4):
    y = np.copy(x)
    for d, g in ((0.0297, 0.62), (0.0371, 0.57), (0.0411, 0.52), (0.0437, 0.47), (0.053, 0.42)):
        k = int(d * SR)
        c = np.copy(x)
        for i in range(k, len(c), k):
            c[i:i + k] += g * c[i - k:i][:len(c[i:i + k])]
        y += mix * 0.2 * c
    return y


def bell(f, dur=1.2, amp=1.0):
    t = t_(dur)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2)
         + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 8)
         + 0.1 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 14))
    return amp * s * np.minimum(1, t / 0.004) * np.minimum(1, (dur - t) / 0.3)


def drop(f0, f1, dur, amp):
    t = t_(dur)
    f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.02))
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.002) * np.exp(-t * 22)


def main(out):
    buf = np.zeros(int(SR * 4.2))
    # the swell: noise through a rising low-pass, out of the quiet to the hit
    t = t_(0.55)
    n = rng.standard_normal(len(t))
    sw = np.empty_like(n)
    s = 0.0
    for i, v in enumerate(n):
        a = np.exp(-2 * np.pi * (300 + 2200 * (i / len(n)) ** 2) / SR)
        s = (1 - a) * v + a * s
        sw[i] = s
    place(buf, 0.10 * sw * (t / 0.55) ** 2, 0.0)
    # the drop and its splash
    place(buf, drop(380, 1250, 0.18, 0.9), 0.48)
    place(buf, drop(800, 2100, 0.10, 0.3), 0.51)
    # the chord under the halo: C E G B D, slow swell, a hair detuned twice
    t = t_(3.2)
    env = (1 - np.exp(-t / 0.7)) * np.exp(-np.maximum(0, t - 2.2) * 2.5)
    chord = np.zeros_like(t)
    for k, f in enumerate((261.6, 329.6, 392.0, 493.9, 587.3)):
        for det in (-0.7, 0.7):
            chord += np.sin(2 * np.pi * (f + det) * t + k) * (0.2 - 0.02 * k)
    place(buf, 0.55 * chord * env, 0.5)
    # six glass notes climbing as the halo fills (p 0.24 … 0.84)
    for i, f in enumerate((659.3, 784.0, 987.8, 1174.7, 1318.5, 1568.0)):
        place(buf, bell(f, 1.1, 0.42 - 0.03 * i), 0.82 + i * 0.36)
    # the opening: a soft high chime and an airy whoosh
    for f, d in ((2093.0, 0.0), (2637.0, 0.03), (3136.0, 0.06)):
        place(buf, bell(f, 1.3, 0.22), 2.92 + d)
    t = t_(0.7)
    n = onepole_lp(rng.standard_normal(len(t)), 4000)
    place(buf, 0.08 * n * np.sin(np.pi * t / 0.7) ** 2, 2.85)
    buf -= onepole_lp(buf, 180)
    buf = reverb(buf, 0.5)
    buf = buf / (np.max(np.abs(buf)) + 1e-9) * 0.6
    fade = int(0.3 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype("<i2").tobytes())
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
