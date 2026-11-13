#!/usr/bin/env python3
"""kit (privacy-capture): niri-record-region's two recorders, swapped on the fly.

wf-recorder records through niri (screencopy): privacy mode's block-out reaches every frame and can
be switched mid-recording. gpu-screen-recorder grabs the screen past niri (KMS) and costs a game
next to nothing. While a recording runs, `watch` follows niri's events and asks the recorder for
gpu-screen-recorder once a fullscreen game has held the focus for SETTLE, for wf-recorder at once
when it hasn't (and marks that moment unsafe). `niri-record-region --switch` starts the new
recorder 0.8 s before it stops the old one, so the pieces overlap.

On stop, `glue` makes one file of the pieces without re-encoding the picture (both recorders write
the same H.264: High, no B-frames, BT.709 limited — wf-recorder is told so):
  - an overlap comes off the tail of the piece before, where its picture shows what the next
    piece begins with (by_picture; else by the wall clock);
  - a gpu-screen-recorder piece is cut where it stopped being safe (the watcher's mark, or where
    its picture jumps, whichever is first) and its last safe frame is held until the next piece;
  - the sound is built apart: each swap joined where both pieces heard the same thing (matched
    on the sound itself), then eased back onto the new piece's picture with atempo.
The result is checked (length, rising timestamps, the joins decode); should that fail, the pieces
are encoded into one file instead.

  rec-switch.py kind                  gsr or wf, for what is on screen now
  rec-switch.py watch                 while the recording runs (one at a time)
  rec-switch.py glue EVENTS OUT FPS   the pieces in EVENTS into OUT

KIT_REC_GAME_APPS=app-id,…  counts those programs as games; KIT_REC_DEBUG=dir keeps a copy of the
pieces and EVENTS there before glue, to replay it (both for tests).
"""

import importlib.machinery
import importlib.util
import json
import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path

RUN = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}")
PIDFILE = RUN / "niri-record-region.pid"
PAUSED = RUN / "niri-record-region.paused"
EVENTS = RUN / "niri-record-region.parts.events"
WATCH_PID = RUN / "niri-record-region.watch.pid"
WANT = RUN / "niri-record-region.parts.want"  # what the watcher wants now (a swap to gsr checks it)
REC = Path.home() / ".local/bin/niri-record-region"
NGM = Path.home() / ".local/bin/niri-game-mode"
LOG = Path("/tmp/niri-record-region.log")
# a change must hold this long before the recorder is swapped (a quick Alt+Tab there and back)
SETTLE = 0.6
# how much earlier than the watcher's mark gpu-screen-recorder's frames stop being trusted: niri
# draws a desk switch before its event reaches the watcher, and a piece's clock is good to a few
# tens of ms (tested 03.11: 50 ms let a frame through)
UNSAFE_EARLY = 0.25
SIZE_SLACK = 2
# the sound across a swap: matched over a stretch of the new piece's sound (several attacks: with
# one, a beat matches another — seen 03.11), within ±SEARCH of where the picture puts it (the
# recorders' sound and picture sit up to ~90 ms apart, not by a fixed amount), then a crossfade
REF = 0.35
SEARCH = 0.15
XFADE = 0.02
# how fast the sound is eased back onto its picture after a swap: ≤ 3 % of the tempo, pitch kept
EASE = 0.03
PRIVACY = Path.home() / ".local/bin/niri-cast-privacy"
PRIVACY_RULE = Path.home() / ".config/niri/cfg/privacy-block.kdl"


def log(msg: str) -> None:
    try:
        with LOG.open("a") as f:
            f.write(f"[rec-switch {time.strftime('%H:%M:%S')}] {msg}\n")
    except OSError:
        pass


def niri_json(*args: str):
    r = subprocess.run(["niri", "msg", "-j", *args], capture_output=True, text=True, timeout=5)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


_ngm = None


def ngm():
    """niri-game-mode's own is_game (Steam, Proton, Minecraft), loaded as a module"""
    global _ngm
    if _ngm is None:
        try:
            loader = importlib.machinery.SourceFileLoader("niri_game_mode", str(NGM))
            spec = importlib.util.spec_from_loader("niri_game_mode", loader)
            mod = importlib.util.module_from_spec(spec)
            loader.exec_module(mod)
            _ngm = mod
        except Exception as e:  # no niri-game-mode: nothing counts as a game
            log(f"niri-game-mode not loaded: {e}")
            _ngm = False
    return _ngm


def is_game(win: dict) -> bool:
    extra = {a for a in os.environ.get("KIT_REC_GAME_APPS", "").split(",") if a}
    if (win.get("app_id") or "") in extra:
        return True
    m = ngm()
    try:
        return bool(m and m.is_game(win))
    except Exception:
        return False


def output_sizes() -> list[tuple[int, int]]:
    outs = niri_json("outputs") or {}
    sizes = []
    for o in outs.values():
        lg = o.get("logical") or {}
        if lg.get("width") and lg.get("height"):
            sizes.append((int(lg["width"]), int(lg["height"])))
    return sizes


def private_apps() -> set[str]:
    """the programs privacy mode hides right now (none while it is off)"""
    try:
        with PRIVACY_RULE.open() as f:  # off: no need to ask niri-cast-privacy (a whole python)
            if not f.readline().startswith("// privacy block-out on"):
                return set()
    except OSError:
        pass
    try:
        r = subprocess.run([str(PRIVACY), "status"], capture_output=True, text=True, timeout=5)
        st = json.loads(r.stdout)
    except Exception:
        return set()
    if not st.get("on"):
        return set()
    shown = set(st.get("shown") or [])
    return {a["id"] for a in st.get("apps") or [] if a.get("on") and a.get("id") not in shown}


def want_kind(sizes: list[tuple[int, int]]) -> str:
    """gsr while a game covering its screen has the focus, else wf. Never gsr while privacy mode
    hides a program that has a window on the game's desk: gpu-screen-recorder sees past niri, and
    a focused game is not always the one on top (Desktop's floating windows, a swap in progress)"""
    wins = niri_json("windows") or []
    f = next((w for w in wins if w.get("is_focused")), None)
    if not f or f.get("is_minimized") or not is_game(f):
        return "wf"
    hidden = private_apps()
    if hidden and any(w.get("app_id") in hidden and not w.get("is_minimized")
                      and w.get("workspace_id") == f.get("workspace_id") for w in wins):
        return "wf"
    size = (f.get("layout") or {}).get("window_size") or [0, 0]
    try:
        ww, hh = int(size[0]), int(size[1])
    except (TypeError, ValueError, IndexError):
        return "wf"
    if any(abs(ww - w) <= SIZE_SLACK and abs(hh - h) <= SIZE_SLACK for w, h in sizes):
        return "gsr"
    # games angel-satellite stretches over the screen (a 4:3 CS2): they cover it as drawn
    m = ngm()
    stretch = getattr(m, "STRETCH_GAMES", ()) if m else ()
    if (f.get("app_id") or "").lower() in stretch or any(s in (f.get("title") or "").lower() for s in stretch):
        return "gsr"
    return "wf"


def current_kind() -> str:
    kind = "wf"
    try:
        for line in EVENTS.read_text().splitlines():
            p = line.split("\t")
            if p[0] == "start" and len(p) >= 3:
                kind = p[2]
    except OSError:
        pass
    return kind


def recording() -> bool:
    try:
        os.kill(int(PIDFILE.read_text().strip()), 0)
    except (OSError, ValueError):
        return False
    return not PAUSED.exists()


def watch() -> None:
    # one watcher at a time
    try:
        old = int(WATCH_PID.read_text().strip())
        if old != os.getpid():
            os.kill(old, 0)
            return
    except (OSError, ValueError):
        pass
    WATCH_PID.write_text(str(os.getpid()))
    sizes = output_sizes()
    stream = subprocess.Popen(["niri", "msg", "-j", "event-stream"], stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, text=True, bufsize=1)
    log("watching")
    pending, since = None, 0.0
    dirty = True
    seen_ms = None  # when the first event since the last look came (the wall clock, ms)
    procs: list = []  # swaps running: (process, kind)
    try:
        while True:
            if not recording():
                # paused or stopped: a resume starts a new watcher
                time.sleep(0.3)
                if not recording():
                    break
            r, _, _ = select.select([stream.stdout], [], [], 0.5)
            if not r:
                dirty = True  # privacy mode switched, a window's program: no event says so
            if r:
                line = stream.stdout.readline()
                if not line:
                    break
                if '"Window' in line or '"Workspace' in line or '"Output' in line:
                    dirty = True
                    if seen_ms is None:
                        seen_ms = int(time.time() * 1000)
                    if '"Output' in line:
                        sizes = output_sizes()
            # a swap in flight: what it goes to counts as where we are
            procs[:] = [(pr, k) for pr, k in procs if pr.poll() is None]
            going = procs[-1][1] if procs else None
            if not dirty and pending is None:
                continue
            dirty = False
            at_ms, seen_ms = seen_ms or int(time.time() * 1000), None
            want = want_kind(sizes)
            cur = current_kind()
            try:
                WANT.write_text(want)  # a swap to gsr still starting calls itself off on "wf"
            except OSError:
                pass
            if want == (going or cur):
                pending = None
                continue
            # out of the game: at once, no settling, even while the swap into it still starts
            # (the watcher never waits on a swap: it once missed an exit for 0.6 s that way).
            # gpu-screen-recorder sees past niri; from this moment on its frames may show what
            # privacy mode hides: glue cuts them out
            if want == "wf" and "gsr" in (cur, going):
                pending = None
                try:
                    with EVENTS.open("a") as ev:
                        ev.write(f"unsafe\t{at_ms}\n")
                except OSError:
                    pass
                log("switch to wf (out of the game, at once)")
                procs.append((subprocess.Popen([str(REC), "--switch", "wf"], stdin=subprocess.DEVNULL,
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), "wf"))
                dirty = True
                continue
            now = time.monotonic()
            if pending != want:
                pending, since = want, now
                dirty = True  # look again once it has held
                continue
            if now - since < SETTLE:
                dirty = True
                continue
            pending = None
            log(f"switch to {want}")
            procs.append((subprocess.Popen([str(REC), "--switch", want], stdin=subprocess.DEVNULL,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL), want))
            dirty = True
    finally:
        stream.terminate()
        try:
            if WATCH_PID.read_text().strip() == str(os.getpid()):
                WATCH_PID.unlink()
        except OSError:
            pass
        log("watcher out")


def probe(path: str) -> tuple[float, bool, tuple[int, int]]:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                        "-of", "json", path], capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    dur = float((j.get("format") or {}).get("duration") or 0)
    streams = j.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    return dur, any(s.get("codec_type") == "audio" for s in streams), (int(v.get("width") or 0), int(v.get("height") or 0))


def picture_break(path: str, safe: float) -> float | None:
    """where, in the 2 s before `safe` (and a little after), the picture first jumps far more
    than the game moves (a desk switch, a window, Alt+Tab): just before that frame, else None"""
    start = max(0.0, safe - 2.0)
    fr = frames(path, start, safe - start + 0.3)
    if len(fr) < 10:
        return None
    a0 = probe_start(path)
    diffs = []
    for (t0, f0), (t1, f1) in zip(fr, fr[1:]):
        diffs.append((t1 - a0, sum(abs(x - y) for x, y in zip(f0[::2], f1[::2])) / max(1, len(f0[::2]))))
    calm = sorted(d for _, d in diffs[: max(5, len(diffs) // 3)])
    base = calm[len(calm) // 2]
    # the first jump at least half the biggest: a desk or a window replaces the whole frame,
    # the game's own flashes and menus move less
    limit = max(6.0, 5 * base, 0.5 * max(d for _, d in diffs))
    for t, d in diffs:
        if d > limit:
            return max(0.0, t - 0.05)
    return None


def pieces_of(events: str) -> list[dict]:
    pieces, unsafe = [], []
    for line in Path(events).read_text().splitlines():
        p = line.split("\t")
        if p[0] == "unsafe" and len(p) >= 2:
            unsafe.append(int(p[1]) / 1000)
        elif p[0] == "start" and len(p) >= 4:
            pieces.append({"file": p[1], "kind": p[2], "start": int(p[3]) / 1000, "end": None})
        elif p[0] == "end" and len(p) >= 3:
            for pc in pieces:
                if pc["file"] == p[1]:
                    pc["end"] = int(p[2]) / 1000
    pieces = [pc for pc in pieces if os.path.isfile(pc["file"]) and os.path.getsize(pc["file"]) > 0]
    for pc in pieces:
        pc["dur"], pc["audio"], pc["size"] = probe(pc["file"])
        end = pc["end"] if pc["end"] is not None else pc["start"] + pc["dur"]
        pc["began"], pc["end"] = end - pc["dur"], end
    # the overlap of a swap comes off the tail of the piece before; a pause leaves a gap
    for a, b in zip(pieces, pieces[1:]):
        a["cut_tail"] = min(max(0.0, a["end"] - b["began"]), max(0.0, a["dur"] - 0.05))
        if a["cut_tail"] > 0:
            a["cut_tail"] = by_picture(a, b, a["cut_tail"])
    for pc in pieces:
        pc["freeze"] = 0.0
    if pieces:
        pieces[-1]["cut_tail"] = 0.0
    # gpu-screen-recorder's piece ends where it stopped being safe: the watcher's mark, 250 ms
    # early (niri draws the first frames of a desk switch before its event reaches the watcher,
    # and a piece's clock is good to a few tens of ms — tested 03.11: 50 ms let a frame through);
    # until the next piece begins its last safe frame stays
    for a, b in zip(pieces, pieces[1:]):
        if a["kind"] != "gsr":
            continue
        # a mark up to 1 s before it began: the exit came while it was starting (it starts in
        # ~0.6 s); all of it is unsafe. Older marks belong to a swap that was called off
        marks = [u for u in unsafe if a["began"] - 1.0 < u < a["end"]]
        if not marks:
            continue
        safe = max(0.05, min(marks) - a["began"] - UNSAFE_EARLY)
        # the clock can be late (a busy watcher, a recorder's own delays): the picture tells too.
        # A desk sliding in or a window over the game changes the whole frame at once
        cut = picture_break(a["file"], safe)
        if cut is not None and cut < safe:
            log(f"{Path(a['file']).name}: the picture changes at {cut + 0.05:.3f} s, before the mark's {safe:.3f} s")
            safe = max(0.05, cut)
        keep = a["dur"] - a["cut_tail"]
        if safe < keep:
            a["freeze"] = keep - safe
            a["cut_tail"] = a["dur"] - safe
            log(f"{Path(a['file']).name}: unsafe from {safe:.3f} s, {a['freeze']:.3f} s held still")
            # where the next piece begins is the clock's guess (game and desk: no picture to match);
            # the still frame can be any length: make it end where the next piece's sound fits
            if a["audio"] and b["audio"]:
                tau = sound_onset(b["file"])
                sh = sound_shift(a["file"], keep, b["file"], tau)
                if sh and a["freeze"] + sh >= 0.05:
                    a["freeze"] += sh  # the piece itself stays cut where it was safe
                    log(f"{Path(a['file']).name}: still frame {sh * 1000:+.0f} ms to meet the next piece's sound")
    return pieces


def frames(path: str, start: float, length: float) -> list[tuple[float, bytes]]:
    """small grey frames with their own times (from the file's start)"""
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "info", "-ss", f"{max(0.0, start):.3f}", "-t", f"{length:.3f}",
                        "-copyts", "-i", path, "-an", "-vf", "scale=96:54:flags=area,format=gray,showinfo",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True)
    times = []
    for line in r.stderr.decode(errors="replace").splitlines():
        k = line.find("pts_time:")
        if "Parsed_showinfo" in line and k >= 0:
            try:
                times.append(float(line[k + 9:].split()[0]))
            except ValueError:
                pass
    n = 96 * 54
    data = r.stdout
    return [(t, data[i * n:(i + 1) * n]) for i, t in enumerate(times) if len(data) >= (i + 1) * n]


def by_picture(a: dict, b: dict, guess: float) -> float:
    """where the piece before shows what the next one begins with: both recorded the same screen
    while they overlapped. The clock's guess is off by up to a tenth of a second (the recorders
    start and stop with their own delays); a still screen matches anywhere: then the guess stays"""
    try:
        head = frames(b["file"], 0, 0.25)
        if not head:
            return guess
        t0, first = head[0]
        start = probe_start(b["file"])
        tail = frames(a["file"], a["dur"] - guess - 0.35, 0.7)
        a0 = probe_start(a["file"])
        if len(tail) < 3:
            return guess
        def mad(x: bytes, y: bytes) -> float:
            return sum(abs(p - q) for p, q in zip(x[::3], y[::3])) / max(1, len(x[::3]))
        scores = [(mad(f, first), t) for t, f in tail]
        best, bt = min(scores)
        ordered = sorted(sc for sc, _ in scores)
        median = ordered[len(ordered) // 2]
        # a clear match only: the picture moved in the overlap, and one frame is it
        if median < 0.2 or best > 0.75 * median:
            log(f"join by clock (still picture: best {best:.2f}, median {median:.2f})")
            return guess
        # the piece before ends just before the frame the next one begins with
        cut = a["dur"] - (bt - a0) + (t0 - start)
        cut = min(max(0.0, cut), max(0.0, a["dur"] - 0.05))
        if abs(cut - guess) > 0.25:
            log(f"join by clock (the picture's match {cut:.3f} s is too far from {guess:.3f} s)")
            return guess
        log(f"join by picture: cut {cut:.3f} s (clock said {guess:.3f}; best {best:.2f}, median {median:.2f})")
        return cut
    except Exception as e:
        log(f"join by picture failed: {e}")
        return guess


def probe_start(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip() or 0)
    except ValueError:
        return 0.0


def joins_decode(out: str, seams: list[float]) -> bool:
    """the packets' times only go up, and each join (a second either side) decodes without an
    error (frames kept on their own times: gpu-screen-recorder's are not on a 1/fps grid, and
    put on one two of them can land on the same tick — that is not the file's fault)"""
    for sel in ("v:0", "a:0"):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", "packet=dts",
                            "-of", "csv=p=0", out], capture_output=True, text=True)
        prev = None
        for line in r.stdout.split():
            try:
                d = int(line.strip().rstrip(","))
            except ValueError:
                continue
            if prev is not None and d <= prev:
                log(f"{sel}: dts {d} after {prev}")
                return False
            prev = d
    for t in seams:
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{max(0.0, t - 1):.3f}", "-t", "2",
                            "-i", out, "-fps_mode", "passthrough", "-enc_time_base", "demux", "-f", "null", "-"],
                           capture_output=True, text=True)
        if r.returncode != 0 or r.stderr.strip():
            log(f"join at {t:.2f} s: {r.stderr.strip()[-300:]}")
            return False
    return True


def still_clip(norm: str, pc: dict, out: str, fps: str) -> bool:
    """the piece's last kept frame held for pc["freeze"] s (picture only: the sound is laid
    under the whole video at once). Encoded as wf-recorder writes, so it joins as the pieces do"""
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-sseof", "-0.1", "-i", norm,
                        "-filter_complex", f"[0:v]trim=start_frame=0:end_frame=1,setpts=PTS-STARTPTS,"
                        f"tpad=stop_mode=clone:stop_duration={pc['freeze']:.3f},fps={fps},format=yuv420p[v]",
                        "-map", "[v]", "-t", f"{pc['freeze']:.3f}",
                        "-c:v", "h264_nvenc", "-preset", "p4", "-tune", "ll", "-rc", "vbr", "-cq", "23", "-b:v", "0",
                        "-g", str(fps), "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-color_range", "tv", "-video_track_timescale", "90000", out], capture_output=True, text=True)
    if r.returncode != 0:
        log(f"still clip failed: {r.stderr.strip()[-300:]}")
        return False
    return True


def sound_onset(path: str) -> float:
    """when a piece's sound really begins (its first 10 ms that is not near-silent), 0.06 s if
    it is quiet all along"""
    import numpy as np
    x = pcm(path, 0.0, 1.0)
    if len(x) < 4800:
        return 0.06
    rms = np.sqrt((x[: len(x) // 480 * 480].reshape(-1, 480) ** 2).mean(axis=1))
    ref = float(np.median(rms))
    if ref < 50 / 32768:
        return 0.06
    loud = np.nonzero(rms[:25] > 0.1 * ref)[0]
    return min(0.2, float(loud[0]) * 0.01) if len(loud) else 0.06


def pcm(path: str, start: float, length: float):
    """mono float samples at 48 kHz from start (s, the piece's own time) for length s"""
    import numpy as np
    start = max(0.0, start)
    if start < 1.0:
        # a file's head read with -ss loses the sound's first ~20 ms (AAC's start), which atrim
        # keeps: read it from 0 and slice, on atrim's own time line
        r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-t", f"{start + length:.4f}", "-i", path,
                            "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
        return np.frombuffer(r.stdout, dtype=np.float32)[int(start * 48000):]
    r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-ss", f"{start:.4f}", "-t", f"{length:.4f}",
                        "-i", path, "-vn", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32)


def sound_shift(prev: str, at: float, nxt: str, tau: float) -> float:
    """how much later than the picture says the next piece's sound sits on the old one's: the old
    one heard the same thing through the overlap. 0 when they don't match clearly (quiet)"""
    import numpy as np
    ref = pcm(nxt, tau, REF)
    win = pcm(prev, at + tau - SEARCH, REF + 2 * SEARCH)
    if len(ref) < int(REF * 48000 * 0.6) or len(win) < len(ref) + int(SEARCH * 48000) or float(np.std(ref)) < 1e-3:
        log(f"sound left where the picture puts it (ref {len(ref) / 48000:.3f} s std {float(np.std(ref)) if len(ref) else 0:.4f}, "
            f"window {len(win) / 48000:.3f} s from {at + tau - SEARCH:.3f} of {prev.rsplit('/', 1)[-1]})")
        return 0.0
    # matched on the sound's changes, not the sound: a smooth tone (a bass note) looks alike every
    # few ms and pulls the match off by whole periods; the attacks (drums, clicks) don't
    ref = np.diff(ref)
    win = np.diff(win)
    c = np.correlate(win, ref, mode="valid")
    # normalise by the window's energy under the reference at each lag
    e = np.sqrt(np.convolve(win ** 2, np.ones(len(ref)), mode="valid")) * np.sqrt((ref ** 2).sum())
    score = (c / np.maximum(e, 1e-9))[:int(2 * SEARCH * 48000) + 1]  # lags of ±SEARCH only
    k = int(np.argmax(score))
    shift = k / 48000 - SEARCH
    if score[k] < 0.6 or abs(shift) > SEARCH - 0.004:
        log(f"sound left where the picture puts it (match {score[k]:.2f} at {shift * 1000:+.0f} ms)")
        return 0.0
    return shift


def build_sound(pieces: list[dict], spans: list[float], out: str) -> bool:
    """one sound track as long as the picture. Each piece's own sound under its own span (one
    clock per piece: in sync). At a swap the new piece's sound is laid where it fits the old
    one's (both heard the same thing through the overlap: no skip, no repeat); what that puts it
    off its picture (up to ~90 ms) is taken back over the next ≥ 3 s, at most EASE faster or
    slower, pitch kept (atempo)"""
    n = len(pieces)
    swap = [i > 0 and (pieces[i - 1]["cut_tail"] > 0 or pieces[i - 1].get("freeze", 0) > 0) for i in range(n)]
    tau = [sound_onset(pc["file"]) if swap[i] else 0.0 for i, pc in enumerate(pieces)]
    shift = [0.0] * n
    for i in range(1, n):
        if swap[i]:
            shift[i] = sound_shift(pieces[i - 1]["file"], spans[i - 1], pieces[i]["file"], tau[i])
    # where each piece's sound is cut out (its own time)
    start = [tau[i] for i in range(n)]
    end = []
    for i in range(n):
        e = spans[i]
        if i + 1 < n and swap[i + 1]:
            want = e + shift[i + 1] + tau[i + 1] + XFADE
            if want > pieces[i]["adur"]:  # not enough of it past the join: no shift there
                shift[i + 1] = 0.0
                tau[i + 1] = max(0.0, min(tau[i + 1], pieces[i]["adur"] - e - XFADE))
                start[i + 1] = tau[i + 1]
                want = e + tau[i + 1] + XFADE
            e = want  # the old piece's sound ends where the new one's takes over (a shift may be < 0)
        end.append(e)
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]
    chains = []
    fmt = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
    for i, pc in enumerate(pieces):
        cmd += ["-i", pc["file"]]
        s_i = shift[i]
        length = end[i] - start[i]
        d = min(max(3.0, abs(s_i) / EASE), length * 0.8)
        if abs(s_i) > 0.002 and d > 10 * abs(s_i):
            # [start, start+d] played in d - s: the sound comes back onto its picture
            chains.append(f"[{i}:a]asplit=2[p{i}a][p{i}b]")
            chains.append(f"[p{i}a]atrim=start={start[i]:.4f}:end={start[i] + d:.4f},asetpts=PTS-STARTPTS,{fmt},"
                          f"atempo={d / (d - s_i):.5f}[q{i}a]")
            chains.append(f"[p{i}b]atrim=start={start[i] + d:.4f}:end={end[i]:.4f},asetpts=PTS-STARTPTS,{fmt}[q{i}b]")
            chains.append(f"[q{i}a][q{i}b]concat=n=2:v=0:a=1[s{i}]")
        else:
            if abs(s_i) > 0.002:
                log(f"piece {i}: too short to take {s_i * 1000:.0f} ms back, left off its picture")
            chains.append(f"[{i}:a]atrim=start={start[i]:.4f}:end={end[i]:.4f},asetpts=PTS-STARTPTS,{fmt}[s{i}]")
    cur = "s0"
    for i in range(1, n):
        nxt = f"j{i}"
        if swap[i]:
            chains.append(f"[{cur}][s{i}]acrossfade=d={XFADE}:c1=tri:c2=tri[{nxt}]")
        else:
            chains.append(f"[{cur}][s{i}]concat=n=2:v=0:a=1[{nxt}]")
        cur = nxt
    r = subprocess.run(cmd + ["-filter_complex", ";".join(chains), "-map", f"[{cur}]", "-c:a", "aac", "-b:a", "160k", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        log(f"sound failed: {r.stderr.strip()[-300:]}")
        return False
    log("sound cuts: " + "; ".join(f"{i}: {start[i]:.4f}..{end[i]:.4f} span {spans[i]:.4f}" for i in range(n)))
    log("sound joins: " + ", ".join(f"onset {tau[i] * 1000:.0f} ms shift {shift[i] * 1000:+.0f} ms" for i in range(1, n) if swap[i]))
    return True


def glue_copy(pieces: list[dict], out: str, fps: str) -> bool:
    """the picture: each piece copied onto one time scale (gpu-screen-recorder's is 1/1000000,
    wf-recorder's 1/90000: ffmpeg's concat shifts the next piece by the wrong scale), its tail cut
    there, the pieces joined as they are. The sound: laid under it in one go (build_sound)"""
    t0 = time.monotonic()
    work = Path(out).resolve().with_name(Path(out).stem + ".join")
    work.mkdir(exist_ok=True)
    try:
        return _glue_copy(pieces, out, fps, work, t0)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _glue_copy(pieces: list[dict], out: str, fps: str, work: Path, t0: float) -> bool:
    lines, seams, spans, at, ok = [], [], [], 0.0, True
    audio = all(pc["audio"] for pc in pieces)
    for k, pc in enumerate(pieces):
        keep = pc["dur"] - pc["cut_tail"]
        norm = work / f"{k:03d}.mp4"
        r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", pc["file"], "-t", f"{keep:.3f}",
                            "-map", "0:v", "-c", "copy", "-video_track_timescale", "90000",
                            "-avoid_negative_ts", "make_zero", str(norm)], capture_output=True, text=True)
        if r.returncode != 0:
            log(f"piece {pc['file']}: {r.stderr.strip()[-300:]}")
            ok = False
            break
        lines.append(f"file '{norm}'")
        span = probe(str(norm))[0]
        at += span
        seams.append(at)
        if pc.get("freeze", 0) > 0.01:
            still = work / f"{k:03d}s.mp4"
            if not still_clip(str(norm), pc, str(still), fps):
                ok = False
                break
            lines.append(f"file '{still}'")
            held = probe(str(still))[0]
            span += held
            at += held
            seams.append(at)
        spans.append(span)
        if audio:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration",
                                "-of", "csv=p=0", pc["file"]], capture_output=True, text=True)
            try:
                pc["adur"] = float(r.stdout.strip())
            except ValueError:
                pc["adur"] = pc["dur"]
    picture = work / "picture.mp4"
    if ok:
        lst = work / "list.txt"
        lst.write_text("\n".join(lines) + "\n")
        r = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                            "-c", "copy", str(picture)], capture_output=True, text=True)
        if r.returncode != 0:
            log(f"join failed: {r.stderr.strip()[-300:]}")
            ok = False
    if ok:
        mux = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", str(picture)]
        if audio:
            sound = work / "sound.m4a"
            ok = build_sound(pieces, spans, str(sound))
            mux += ["-i", str(sound), "-map", "0:v", "-map", "1:a"]
        if ok:
            r = subprocess.run(mux + ["-c", "copy", "-movflags", "+faststart", out], capture_output=True, text=True)
            if r.returncode != 0:
                log(f"mux failed: {r.stderr.strip()[-300:]}")
                ok = False
    if not ok:
        return False
    # the result must be as long as its pieces, and decode cleanly at every join
    total = probe(out)[0]
    if abs(total - at) > 0.5:
        log(f"joined length {total:.2f} s, pieces {at:.2f} s: timestamps are off")
        return False
    ok = joins_decode(out, seams[:-1])
    log(f"joined {len(pieces)} pieces as they are in {time.monotonic() - t0:.1f} s ({total:.2f} s), joins {'clean' if ok else 'BROKEN'}")
    return ok


def glue_encode(pieces: list[dict], out: str, fps: str) -> bool:
    w, h = pieces[0]["size"]
    w, h = w - w % 2, h - h % 2
    audio = all(pc["audio"] for pc in pieces)
    cmd = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y"]
    chains, labels = [], []
    for i, pc in enumerate(pieces):
        keep, hold = pc["dur"] - pc["cut_tail"], pc.get("freeze", 0.0)
        cmd += ["-t", f"{keep + hold:.3f}", "-i", pc["file"]]
        still = f",trim=end={keep:.3f},tpad=stop_mode=clone:stop_duration={hold:.3f}" if hold > 0.01 else ""
        chains.append(f"[{i}:v]setpts=PTS-STARTPTS{still},fps={fps},scale={w}:{h}:out_color_matrix=bt709:out_range=tv,format=yuv420p,setsar=1[v{i}]")
        labels.append(f"[v{i}]")
        if audio:
            chains.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
            labels.append(f"[a{i}]")
    graph = ";".join(chains) + ";" + "".join(labels) + f"concat=n={len(pieces)}:v=1:a={1 if audio else 0}[v]" + ("[a]" if audio else "")
    tail = ["-filter_complex", graph, "-map", "[v]"] + (["-map", "[a]", "-c:a", "aac", "-b:a", "160k"] if audio else [])
    tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    for venc in (["-c:v", "h264_nvenc", "-preset", "p2", "-rc", "vbr", "-cq", "23", "-b:v", "0", "-g", str(fps)],
                 ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-g", str(fps)]):
        t0 = time.monotonic()
        r = subprocess.run(cmd + tail + venc + tags + ["-movflags", "+faststart", out], capture_output=True, text=True)
        if r.returncode == 0:
            log(f"encoded {len(pieces)} pieces in {time.monotonic() - t0:.1f} s ({venc[1]})")
            return True
        log(f"encode with {venc[1]} failed: {r.stderr.strip()[-400:]}")
    return False


def glue(events: str, out: str, fps: str) -> int:
    dbg = os.environ.get("KIT_REC_DEBUG")
    if dbg:  # a copy of the pieces and the swaps' log, to replay the glue (tests)
        Path(dbg).mkdir(parents=True, exist_ok=True)
        text = Path(events).read_text()
        for line in text.splitlines():
            q = line.split("\t")
            if q[0] == "start" and os.path.isfile(q[1]):
                shutil.copy2(q[1], Path(dbg) / Path(q[1]).name)
                text = text.replace(q[1], str(Path(dbg) / Path(q[1]).name))
        (Path(dbg) / "events").write_text(text)
    pieces = pieces_of(events)
    if not pieces:
        return 1
    for pc in pieces:
        log(f"piece {Path(pc['file']).name} {pc['kind']} {pc['dur']:.2f} s, tail cut {pc['cut_tail']:.3f}, held {pc.get('freeze', 0):.3f}")
    if glue_copy(pieces, out, fps):
        return 0
    return 0 if glue_encode(pieces, out, fps) else 1


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "kind":
        print(want_kind(output_sizes()))
        return 0
    if cmd == "watch":
        watch()
        return 0
    if cmd == "glue" and len(sys.argv) == 5:
        return glue(sys.argv[2], sys.argv[3], sys.argv[4])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
