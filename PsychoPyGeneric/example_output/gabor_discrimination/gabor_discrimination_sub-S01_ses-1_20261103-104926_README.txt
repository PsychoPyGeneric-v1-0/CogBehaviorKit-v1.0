====================================================================================================
WHAT IS IN THE DATA FILE?
====================================================================================================
Experiment : gabor_discrimination
Participant: S01   Session: 1   Run type: real
Data file  : gabor_discrimination_sub-S01_ses-1_20261103-104926.csv
Written    : 2026-11-03 10:49:26  (updated while the experiment runs)

Gabor discrimination at several contrast levels. The Gabor is shown briefly, then the participant
answers on a response screen (RT is counted from that screen).

HOW TO OPEN THE CSV
  * One ROW = one TRIAL. One COLUMN = one measure (explained below). Empty cell = not applicable.
  * Excel: use Data > From Text/CSV and choose 'comma' as delimiter. Double-clicking can put everything
    in one column on computers set to French or other European settings (they expect ';').
  * If you open and re-save the CSV in Excel it may be rewritten with ';' separators and decimal commas.
    Keep the original file untouched and save your own copy as .xlsx.
  * 'rt' and 'onset_time' are in SECONDS; the planned_/measured_ timing columns are in MILLISECONDS. Positions/sizes are in the screen units of the experiment ('deg').

RESPONSE KEYS  (key pressed -> meaning saved in the 'response' column)
  key 'left'  ->  'left'
  key 'right'  ->  'right'

GENERAL COLUMNS
  experiment              Name of the experiment.
  participant             Participant ID you typed at the start.
  session                 Session number you typed at the start.
  test_mode               1 = test run (started with --test), 0 = real run.
  block                   Block number (1, 2, ...). Practice trials have block 0.
  trial                   Trial counter over the whole run, starting at 1. Practice trials are
                          counted too.
  practice                1 = practice trial, 0 = real trial. REMOVE the practice trials (practice =
                          1) before analysing.
  seed                    Random seed of the run. Running again with the same seed gives the same
                          trial order.

EXPERIMENT VARIABLES  (the conditions of each trial, and what was shown)
  gabor.contrast          Contrast of the Gabor (0 = invisible, 1 = maximum).
  tilt                    Discrimination: -1 = tilted left, +1 = tilted right.
  side                    Side of the screen where the Gabor (and cue) appeared.
  gabor.pos               [x, y] position of the Gabor in degrees from the centre (negative x =
                          left).
  cue.pos                 [x, y] position of the ring cue (same as the Gabor).
  gabor.ori               Orientation of the Gabor in degrees, clockwise from vertical.
  answer                  The correct response of this trial.

RESPONSE COLUMNS
  response_key            The keyboard key the participant pressed first. Empty = no key pressed.
  response                What that key MEANS in this experiment (see the key list above). If no key
                          was pressed, this is the 'no response' label if one is defined, otherwise
                          empty.
  rt                      Reaction time in SECONDS (0.45 = 450 ms), measured from the first screen
                          refresh of the response event. Empty = no key pressed.
  correct                 1 = correct, 0 = wrong. Empty = the experiment has no correct answer to
                          compare with.
  timed_out               1 = no key was pressed before the response time ran out, 0 = a key was
                          pressed.

TIMING COLUMNS  (one pair per event of the trial; times in whole MILLISECONDS)
  planned_<event>_ms  = the duration the program planned, rounded to whole screen frames.
  measured_<event>_ms = the duration it really lasted. It should match 'planned_' within about one frame
                        (16.7 ms at 60 Hz). A big difference = timing problem.
  (Milliseconds, not seconds, so that Excel can never turn 1.5 into a date such as '1 May'.)
  Events of a trial, in order:
    1. fixation     shows: fixation
    2. cue          shows: fixation, cue
    3. gap          shows: fixation
    4. target       shows: fixation, gabor
    5. respond      shows: fixation  [response event: waits for a key; RT starts here; its measured time = until the key press]
    6. iti          shows: blank screen
  planned_fixation_ms     planned duration of the event 'fixation', in milliseconds.
  measured_fixation_ms    measured duration of the event 'fixation', in milliseconds.
  planned_cue_ms          planned duration of the event 'cue', in milliseconds.
  measured_cue_ms         measured duration of the event 'cue', in milliseconds.
  planned_gap_ms          planned duration of the event 'gap', in milliseconds.
  measured_gap_ms         measured duration of the event 'gap', in milliseconds.
  planned_target_ms       planned duration of the event 'target', in milliseconds.
  measured_target_ms      measured duration of the event 'target', in milliseconds.
  planned_respond_ms      planned duration of the event 'respond', in milliseconds.
  measured_respond_ms     measured duration of the event 'respond', in milliseconds.
  planned_iti_ms          planned duration of the event 'iti', in milliseconds.
  measured_iti_ms         measured duration of the event 'iti', in milliseconds.

OTHER COLUMNS
  dropped_frames          Number of screen refreshes that came late during this trial. A value
                          around 1 per trial is common (probably a late first frame while the
                          trial's stimuli are prepared). What matters is that the 'measured_'
                          durations of your important events match the 'planned_' ones. Many dropped
                          frames in the middle of trials would mean a timing problem.
  onset_time              Time (seconds since the experiment started) when the first screen of this
                          trial appeared.

QUICK ANALYSIS RECIPE
  1. Keep only real trials:                  practice = 0
  2. For reaction times keep only:           correct = 1  and  timed_out = 0
  3. Average 'rt' (seconds) for each level of your condition columns; compare accuracy ('correct')
     separately, to check that faster responses are not simply less accurate.
  4. Check 'planned_' vs 'measured_' timing and 'dropped_frames' to make sure the timing was good.
