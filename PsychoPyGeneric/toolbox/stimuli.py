"""
stimuli.py - THE STIMULUS LIBRARY
=================================
Every kind of stimulus is a small function that is REGISTERED under a name. In a config you create it with
that name:

        "stimuli": {"my_patch": {"type": "gabor", "sf": 3, "size": 4, "pos": [5, 0]}}
                                   ^ the name of the function below      ^ its parameters

Parameters are the keyword arguments of the function (look at each function's signature for the list
and the defaults). Unspecified parameters keep their default.

Available types (details further down):
    gabor        grating patch               bullseye     concentric circles (fixation)
    gap_circle   ring cue with an optional gap     circle, square, rectangle, polygon, triangle, diamond
    line         a line                      arrow        arrow (left/right/up/down/both)
    text         text (e.g. a "+" fixation)  search_array shapes for visual search (target + distractors)

HOW TO READ A BUILDER FUNCTION
    def gabor(win, cs, rng, pos=(0, 0), size=4.0, ...):
        win  = the PsychoPy window (needed by every PsychoPy stimulus)
        cs   = the colour space of the experiment ("rgb255", ...). We pass it on so colours are
               always interpreted the same way
        rng  = the random generator (only used by stimuli with random layouts)
        the rest = the parameters you can set in the config
    It returns a PsychoPy object that has .draw().

ADD YOUR OWN STIMULUS without editing this file (put this in experiments/<name>/custom_stimuli.py):

    from toolbox.stimuli import register_stimulus
    @register_stimulus("my_stim")
    def my_stim(win, cs, rng, pos=(0, 0), size=1.0):
        return visual.Rect(win, width=size, height=size, pos=pos, colorSpace=cs)

Sizes and positions are in the screen units (degrees of visual angle by default). [0, 0] = screen centre,
negative x = left, positive y = up.
"""
import numpy as np
from psychopy import visual
from .config import ConfigError

_REGISTRY = {}


def register_stimulus(name):
    def deco(fn):
        _REGISTRY[name] = fn
        return fn
    return deco


def available_stimuli():
    return sorted(_REGISTRY)


class StimGroup:
    """Several PsychoPy objects used as ONE stimulus: drawing the group draws all of them.
    `info` can carry extra facts (e.g. the target position); they are saved in the data file."""
    def __init__(self, items, info=None):
        self.items = list(items)
        self.info = info or {}

    def draw(self):
        for item in self.items:
            item.draw()


def build_stimulus(win, spec, color_space="rgb255", rng=None):
    """Create a stimulus from its definition, e.g. {"type": "circle", "size": 2}: look up the function
    registered under "type" and call it with the other entries as parameters."""
    spec = dict(spec)
    kind = spec.pop("type", None)
    if kind not in _REGISTRY:
        raise ConfigError(f"Unknown stimulus type {kind!r}. Available: {available_stimuli()}")
    rng = rng if rng is not None else np.random.default_rng()
    try:
        return _REGISTRY[kind](win, color_space, rng, **spec)
    except TypeError as err:
        raise ConfigError(f"Bad parameters for stimulus type '{kind}': {err}") from err


# ---------------------------------------------------------------- gratings / bullseye / cues
@register_stimulus("gabor")
def gabor(win, cs, rng, pos=(0, 0), size=4.0, sf=2.0, ori=0.0, phase=0.0, contrast=1.0,
          mask="gauss", color="white", opacity=1.0):
    """Sinusoidal grating in a Gaussian window. sf = cycles per unit (cycles/deg with units='deg').
    ori in degrees, clockwise from vertical. phase in cycles (0-1). contrast 0-1."""
    return visual.GratingStim(win, tex="sin", mask=mask, pos=pos, size=size, sf=sf, ori=ori,
                              phase=phase, contrast=contrast, color=color, colorSpace=cs, opacity=opacity)


@register_stimulus("bullseye")
def bullseye(win, cs, rng, pos=(0, 0), radius=0.5, n_rings=3, colors=("black", "white"), opacity=1.0):
    """Concentric discs alternating between `colors`. Outer ring is drawn first."""
    radii = np.linspace(radius, radius / n_rings, n_rings)
    discs = [visual.Circle(win, radius=float(r), pos=pos, edges=64, fillColor=colors[i % len(colors)],
                           lineColor=None, colorSpace=cs, opacity=opacity) for i, r in enumerate(radii)]
    return StimGroup(discs)


@register_stimulus("gap_circle")
def gap_circle(win, cs, rng, pos=(0, 0), radius=1.5, gap_side="left", gap_angle=60.0,
               line_width=3.0, color="white", n_points=120):
    """Ring cue. gap_side: 'left', 'right', 'up', 'down' or None (closed circle). gap_angle in degrees."""
    if gap_side in (None, "none"):
        ang = np.deg2rad(np.linspace(0, 360, n_points, endpoint=False))
        closed = True
    else:
        centre = {"right": 0, "up": 90, "left": 180, "down": 270}[gap_side]
        half = gap_angle / 2.0
        ang = np.deg2rad(np.linspace(centre + half, centre + 360 - half, n_points))
        closed = False
    verts = radius * np.column_stack([np.cos(ang), np.sin(ang)])
    return visual.ShapeStim(win, vertices=verts, closeShape=closed, pos=pos, lineWidth=line_width,
                            lineColor=color, fillColor=None, colorSpace=cs)


# ---------------------------------------------------------------- basic shapes
@register_stimulus("circle")
def circle(win, cs, rng, pos=(0, 0), size=1.0, fill_color="white", line_color=None, line_width=2.0, ori=0.0, opacity=1.0):
    """size = diameter."""
    return visual.Circle(win, radius=size / 2.0, pos=pos, edges=64, fillColor=fill_color, lineColor=line_color,
                         lineWidth=line_width, ori=ori, opacity=opacity, colorSpace=cs)


@register_stimulus("square")
def square(win, cs, rng, pos=(0, 0), size=1.0, fill_color="white", line_color=None, line_width=2.0, ori=0.0, opacity=1.0):
    return visual.Rect(win, width=size, height=size, pos=pos, fillColor=fill_color, lineColor=line_color,
                       lineWidth=line_width, ori=ori, opacity=opacity, colorSpace=cs)


@register_stimulus("rectangle")
def rectangle(win, cs, rng, pos=(0, 0), width=2.0, height=1.0, fill_color="white", line_color=None,
              line_width=2.0, ori=0.0, opacity=1.0):
    return visual.Rect(win, width=width, height=height, pos=pos, fillColor=fill_color, lineColor=line_color,
                       lineWidth=line_width, ori=ori, opacity=opacity, colorSpace=cs)


@register_stimulus("polygon")
def polygon(win, cs, rng, pos=(0, 0), size=1.0, edges=5, fill_color="white", line_color=None,
            line_width=2.0, ori=0.0, opacity=1.0):
    """Regular polygon; size = diameter of the circumscribed circle."""
    return visual.Polygon(win, edges=edges, radius=size / 2.0, pos=pos, fillColor=fill_color, lineColor=line_color,
                          lineWidth=line_width, ori=ori, opacity=opacity, colorSpace=cs)


@register_stimulus("triangle")
def triangle(win, cs, rng, **kw):
    return polygon(win, cs, rng, edges=3, **kw)


@register_stimulus("diamond")
def diamond(win, cs, rng, **kw):
    return polygon(win, cs, rng, edges=4, **kw)


@register_stimulus("line")
def line(win, cs, rng, start=(-1, 0), end=(1, 0), color="white", line_width=3.0, opacity=1.0):
    return visual.Line(win, start=start, end=end, lineColor=color, lineWidth=line_width,
                       opacity=opacity, colorSpace=cs)


@register_stimulus("arrow")
def arrow(win, cs, rng, pos=(0, 0), size=2.0, direction="right", fill_color="white", line_color=None,
          line_width=2.0, shaft_width=0.15, head_length=0.4, head_width=0.5, opacity=1.0):
    """Arrow of total length `size`. direction: 'left','right','up','down' or 'both' (double-headed, horizontal)."""
    L = size
    hl, hw, sw = head_length * L, head_width * L / 2.0, shaft_width * L / 2.0
    xs = L / 2.0 - hl
    if direction == "both":
        verts = [(-L / 2, 0), (-xs, hw), (-xs, sw), (xs, sw), (xs, hw), (L / 2, 0),
                 (xs, -hw), (xs, -sw), (-xs, -sw), (-xs, -hw)]
        ori = 0
    else:
        if direction not in ("right", "down", "left", "up"):
            raise ConfigError(f"arrow direction must be left/right/up/down/both, got {direction!r}")
        verts = [(-L / 2, -sw), (xs, -sw), (xs, -hw), (L / 2, 0), (xs, hw), (xs, sw), (-L / 2, sw)]
        ori = {"right": 0, "down": 90, "left": 180, "up": 270}[direction]  # PsychoPy ori is clockwise
    return visual.ShapeStim(win, vertices=verts, pos=pos, ori=ori, fillColor=fill_color, lineColor=line_color,
                            lineWidth=line_width, opacity=opacity, colorSpace=cs)


@register_stimulus("text")
def text(win, cs, rng, text="+", pos=(0, 0), height=1.0, color="white", ori=0.0, font="Arial", opacity=1.0):
    return visual.TextStim(win, text=text, pos=pos, height=height, color=color, ori=ori, font=font,
                           opacity=opacity, colorSpace=cs)


# ---------------------------------------------------------------- visual search
def make_positions(layout, n, rng, center=(0, 0), grid_shape=None, spacing=2.0, radius=5.0,
                   area=(12.0, 8.0), min_dist=1.5, jitter=0.0):
    """Return an (n, 2) NumPy array of item positions. layout: 'grid', 'ring' or 'random'."""
    if layout == "grid":
        if grid_shape is None:
            cols = int(np.ceil(np.sqrt(n)))
            grid_shape = (int(np.ceil(n / cols)), cols)
        rows, cols = grid_shape
        if n > rows * cols:
            raise ConfigError(f"grid_shape {grid_shape} has only {rows * cols} cells for {n} items")
        xs = (np.arange(cols) - (cols - 1) / 2.0) * spacing
        ys = (np.arange(rows) - (rows - 1) / 2.0) * spacing
        gx, gy = np.meshgrid(xs, ys)
        cells = np.column_stack([gx.ravel(), gy.ravel()])
        pts = cells[rng.choice(len(cells), size=n, replace=False)]
    elif layout == "ring":
        ang = 2 * np.pi * np.arange(n) / n + rng.uniform(0, 2 * np.pi)
        pts = radius * np.column_stack([np.cos(ang), np.sin(ang)])
    elif layout == "random":
        pts = []
        for _ in range(20000):
            p = (rng.uniform(-0.5, 0.5, 2) * np.asarray(area))
            if all(np.hypot(*(p - q)) >= min_dist for q in pts):
                pts.append(p)
                if len(pts) == n:
                    break
        if len(pts) < n:
            raise ConfigError("Could not place all items: enlarge 'area' or reduce 'min_dist'/'n_items'")
        pts = np.array(pts)
    else:
        raise ConfigError("layout must be 'grid', 'ring' or 'random'")
    return pts + rng.uniform(-jitter, jitter, pts.shape) + np.asarray(center, float)


@register_stimulus("search_array")
def search_array(win, cs, rng, n_items=8, target_present=True, target=None, distractors=None, item_size=1.0,
                 layout="grid", center=(0, 0), grid_shape=None, spacing=2.0, radius=5.0,
                 area=(12.0, 8.0), min_dist=1.5, jitter=0.0):
    """Array of shapes with (optionally) one target. `target` and each distractor are stimulus specs, e.g.
    {"type": "triangle", "fill_color": "red"}. Distractor types are balanced and shuffled across items."""
    target = target or {"type": "triangle", "fill_color": "red"}
    distractors = distractors or [{"type": "circle", "fill_color": "red"}, {"type": "triangle", "fill_color": "green"}]
    n = int(n_items)
    if n < 1:
        raise ConfigError("search_array: n_items must be >= 1")
    pts = make_positions(layout, n, rng, center, grid_shape, spacing, radius, area, min_dist, jitter)
    t_idx = int(rng.integers(n)) if target_present else None
    n_dist = n - (1 if target_present else 0)
    d_idx = np.resize(np.arange(len(distractors)), n_dist)
    rng.shuffle(d_idx)
    items, k = [], 0
    for i, p in enumerate(pts):
        if i == t_idx:
            spec = target
        else:
            spec = distractors[int(d_idx[k])]
            k += 1
        items.append(build_stimulus(win, {"size": item_size, **spec, "pos": tuple(float(v) for v in p)}, cs, rng))
    info = {"n_items": n, "target_present": bool(target_present),
            "target_pos": [round(float(v), 3) for v in pts[t_idx]] if target_present else None}
    return StimGroup(items, info)
