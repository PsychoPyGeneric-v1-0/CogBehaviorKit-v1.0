"""
testing.py - checks to run BEFORE collecting data: display, timing, keyboard, stimulus preview.
Used through:  python run_experiment.py <experiment> --check display|timing|keyboard|preview|all
"""
import numpy as np
from psychopy import core, visual

from .config import pixels_per_degree
from .experiment import AbortExperiment, Experiment
from .stimuli import build_stimulus


def _open(config):
    exp = Experiment(config, test_mode=True)
    exp.setup_window()
    return exp


def check_display(config):
    exp = _open(config)
    try:
        s, win = exp.cfg["screen"], exp.win
        ppd = pixels_per_degree(exp.cfg)
        print("\n=== DISPLAY CHECK ===")
        print(f"requested size : {s['size']}   actual window size: {list(win.size)}")
        print(f"fullscreen     : {s['fullscreen']}   units: {s['units']}   colour space: {s['color_space']}")
        print(f"background     : {s['bg_color']}")
        print(f"frame rate     : {exp.fps:.2f} Hz (nominal {s['frame_rate']})  -> frame = {1000 / exp.fps:.2f} ms")
        print(f"pixels/degree  : {ppd:.1f}  (screen {s['width_cm']} cm wide, {s['distance_cm']} cm away)")
        if list(win.size) != list(s["size"]) and not s["fullscreen"]:
            print("NOTE: window size differs from screen.size (HiDPI scaling?)")
        for name, spec in exp.cfg["stimuli"].items():
            if spec["type"] == "gabor" and s["units"] == "deg" and spec.get("sf", 2.0) > 0.4 * ppd:
                print(f"WARNING: stimulus '{name}' sf={spec['sf']} cycles/deg is close to the display's limit ({ppd / 2:.1f}).")
        ref = visual.Rect(win, width=10, height=10, lineColor="white", fillColor=None, lineWidth=2, units="deg")
        label = visual.TextStim(win, text=f"10 x 10 deg reference\n{win.size[0]}x{win.size[1]} px, {exp.fps:.1f} Hz\nPress SPACE",
                                color=s["text_color"], height=0.8, units="deg")
        ref.draw(); label.draw(); win.flip()
        exp.kb.waitKeys(keyList=["space", exp.cfg["keys"]["escape"]])
    finally:
        exp.win.close()


def check_timing(config, durations=(0.05, 0.1, 0.2, 0.5), n_reps=10):
    """Show a full-screen white patch for each duration and compare requested vs measured time."""
    exp = _open(config)
    try:
        win = exp.win
        patch = visual.Rect(win, width=2, height=2, units="norm", fillColor="white", lineColor=None, colorSpace="rgb")
        print("\n=== TIMING CHECK (flip-to-flip timestamps) ===")
        for dur in durations:
            n_frames = max(1, int(round(dur * exp.fps)))
            errs = []
            for _ in range(n_reps):
                a, b = {}, {}
                win.callOnFlip(exp._stamp, a)
                for _ in range(n_frames):
                    patch.draw()
                    win.flip()
                win.callOnFlip(exp._stamp, b)
                win.flip()
                errs.append((b["t"] - a["t"]) - dur)
                core.wait(0.05)
            errs = np.array(errs) * 1000
            print(f"requested {dur * 1000:6.0f} ms = {n_frames:3d} frames | error mean {errs.mean():+6.2f} ms, "
                  f"max |err| {np.abs(errs).max():5.2f} ms")
        print(f"dropped frames during check: {getattr(win, 'nDroppedFrames', 'n/a')}")
        print("Errors above ~1 frame (%.1f ms) indicate a timing problem (see README)." % (1000 / exp.fps))
    finally:
        exp.win.close()


def check_keyboard(config):
    exp = _open(config)
    try:
        keys = list(exp.cfg["keys"]["responses"]) or ["space"]
        print("\n=== KEYBOARD CHECK ===")
        for k in keys:
            msg = visual.TextStim(exp.win, text=f"Press the key: {k}", color=exp.cfg["screen"]["text_color"], height=1.0, units="deg")
            msg.draw()
            state = {}
            exp.win.callOnFlip(exp._stamp, state, True)
            exp.win.flip()
            got = exp.kb.waitKeys(keyList=None, waitRelease=False, maxWait=15)
            if not got:
                print(f"expected '{k}': nothing pressed in 15 s")
            else:
                ok = "OK" if got[0].name == k else "WRONG KEY"
                print(f"expected '{k}': got '{got[0].name}' ({ok}), RT = {got[0].rt * 1000:.0f} ms")
    finally:
        exp.win.close()


def preview_stimuli(config, screenshot_dir=None):
    """Show each stimulus of the config one by one (SPACE = next, ESC = quit)."""
    exp = _open(config)
    try:
        win, cs = exp.win, exp.cfg["screen"]["color_space"]
        label = visual.TextStim(win, text="", pos=(0, -9), height=0.7, color=exp.cfg["screen"]["text_color"], units="deg")
        for name, spec in exp.cfg["stimuli"].items():
            spec = {k: v for k, v in spec.items() if k != "visible"}
            stim = build_stimulus(win, spec, cs, exp.rng)
            label.text = f"{name} ({spec['type']}) - SPACE: next, ESC: quit"
            stim.draw(); label.draw(); win.flip()
            if screenshot_dir:
                from pathlib import Path
                Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
                win.getMovieFrame()
                win.saveMovieFrames(str(Path(screenshot_dir) / f"{name}.png"))
            keys = exp.kb.waitKeys(keyList=["space", exp.cfg["keys"]["escape"]])
            if keys[0].name == exp.cfg["keys"]["escape"]:
                break
    finally:
        exp.win.close()


def run_all(config):
    check_display(config)
    check_timing(config)
    check_keyboard(config)
    preview_stimuli(config)
