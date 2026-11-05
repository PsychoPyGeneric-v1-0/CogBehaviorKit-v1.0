# Tutorial 2: from a published paper to code (Posner, 1980)

Paper: Posner, M. I. (1980). *Orienting of attention.* Quarterly Journal of Experimental Psychology, 32(1), 3-25.
Runnable result: `experiments/posner_1980_tutorial/config.py`

> **Important.** The design logic below (cue types, mostly-valid cues, catch trials, key-press detection) is the
> well-known structure of this paradigm. The **numeric parameters in the example config (durations, SOA, sizes,
> trial counts, cue form) are illustrative placeholders, not values I verified in the paper.** Do step 1 below
> with the actual Methods section before collecting data.

## Step 1: build a protocol worksheet from the Methods section
For every row, copy the value *and the page/figure where you found it*; mark anything missing as "not reported".

| Question | Where it goes in the config |
|---|---|
| Screen background, luminance, viewing distance, display size | `screen.bg_color`, `distance_cm`, `width_cm` |
| Fixation stimulus: shape, size | `stimuli.fixation` |
| Placeholder boxes: size, eccentricity | `stimuli.box_left/right` (`pos`, `size`) |
| Cue type (central arrow vs peripheral brightening), duration | `stimuli.cue_*` + `events[cue].duration` |
| Cue-target SOA | `events[gap].duration` (= SOA - cue duration) |
| Target form, size, duration | `stimuli.target`, `events[target].duration` |
| Task and response (detect? key?) | `keys.responses`, `events[target].response` |
| Trial types and proportions (valid/invalid/neutral/catch) | `design.conditions` with `n` counts |
| Number of trials, blocks, practice | `n_repeats`, `n_blocks`, `practice.n_trials` |
| Foreperiod before the cue (fixed/variable) | `events[fixation].duration` (`[min, max]` = jittered) |
| Analysis (RT by trial type, error handling) | `design.summary_by`, then your own analysis |

## Step 2: translate the design
- **Trial types** become an explicit condition list with relative frequencies. Here valid : invalid : neutral : catch
  = 16 : 4 : 4 : 2 per side-pair, giving ~80% validity among cued trials (the paradigm's classic ratio).
- **The cue** is expressed with *visibility flags*: `cue_left.visible` / `cue_right.visible` are set per trial in
  `derive` (both visible = neutral).
- **Catch trials** set `target.visible = False`. Correct = withholding the response, so
  `scoring.no_response_label = "none"` and `answer = "none"`.
- **Timing** is in seconds in the config; the engine converts it to whole frames. At 60 Hz, a 50 ms cue = 3 frames.

## Step 3: validate before running
1. `--check display` - confirm size/frame rate; `--check timing` - confirm 50 ms really lasts 3 frames.
2. `--check preview` - compare stimuli with the paper's figures.
3. `--test` - run 6 trials; open `data/test/*.csv` and check that `cue.visible` flags, positions and `answer` are right.
4. Pilot a colleague; verify RTs are plausible (detection RT ~200-400 ms) and invalid > valid.

## Step 4: run and analyse
```
python run_experiment.py posner_1980_tutorial --participant 01 --seed 1
```
The end-of-run summary gives accuracy and mean RT per `trial_type`. The expected qualitative pattern is
faster RT for valid than invalid cues (the validity effect); check this against what the paper reports rather
than assuming magnitudes. Keep a note of every deviation from the paper (e.g. different screen, key press).
