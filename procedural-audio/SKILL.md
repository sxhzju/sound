---
name: procedural-audio
description: Compose and render original music and sound effects offline in Python. Use for audio generation, synthesis, stingers, loops, risers, whooshes, impacts, UI blips and ambiences. Includes a renderer and setup instructions for downloading Surge XT, sfizz and SFZ libraries. Use sfx-sources when the user wants to download existing clips.
allowed-tools: Bash(python .claude/skills/procedural-audio/scripts/*) Bash(python3 .claude/skills/procedural-audio/scripts/*)
---
# Procedural music & SFX

Rendering runs offline after the user installs the required tools. Do not assume any plugins, Python packages, presets or sample libraries are already installed.

## Setup before first use

Read [references/setup.md](references/setup.md) when setting up a new machine or resolving missing dependencies. It links to official downloads for Surge XT, sfizz, VSCO 2 CE and VCSL, explains Python installation, and documents the `SOUND_*` path settings. Install only the resources needed for the task.

The renderer is bundled as `scripts/audio_backend.py`; no external `local_music` module is needed. Pure Python synthesis and analysis work without instrument plugins or sample libraries. Surge presets require Surge XT VST3; SFZ instruments require sfizz VST3 and downloaded samples. `requirements.txt` lists the Python dependencies.

Examples assume installation at `.claude/skills/procedural-audio/` relative to the user's project root. Activate the virtual environment from the setup guide, then use its `python` for all commands and render scripts.

Run `doctor` to inspect configured paths, then `find` and `probe` to verify the resources needed for this task. Use actual results from the user's installation; preset names and sample mappings below are examples, not a guaranteed installed inventory.

## Kit
`scripts/audio_kit.py` wraps the repetitive parts. Use the CLI to pick sounds:
```
K=.claude/skills/procedural-audio/scripts/audio_kit.py
python "$K" doctor                            # show configured paths and missing optional resources
python "$K" find "kick" [--kind surge|sfz]   # prints load() specs: "Drums/T8 Kick 1", "VSCO-2-CE-1.1.0/Harp.sfz"
python "$K" probe "Pads/Film" 57 69          # attack, decay, spectral peaks (MIDI) early vs late
python "$K" sfzmap "Mark Trees.sfz"          # which key/velocity plays which sample
python "$K" check out.wav --bpm 140 --png /tmp/x.png   # peak, LUFS, loudness per beat, spectrogram
```
Then import it in your render script:
```python
import sys; sys.path.insert(0, ".claude/skills/procedural-audio/scripts")
import audio_kit as ak

HIT = 1.5
mix = ak.timeline(HIT + 2.0)
cym = ak.load("Suspended Cymbal 1.sfz")                       # key 68 = hit (sfzmap)
rev = ak.reverse(ak.render(cym, [(68, 0, 1.0, 110)]))[:, -int(1.2 * ak.SR):]
ak.place(mix, ak.fade(rev, fade_in=0.4), HIT - rev.shape[1] / ak.SR, -8)
ak.place(mix, ak.noise_sweep(HIT, 300, 8000), 0, -10)          # riser
ak.place(mix, ak.render(ak.load("Drums/T8 Kick 1"), [(45, 0, 0.2, 127)]), HIT, -3)
ak.place(mix, ak.render(cym, [(68, 0, 1.0, 127)]), HIT, -4)
ak.place(mix, ak.sub_drop(), HIT, -3)
ak.write("impact.wav", ak.master(ak.fade(mix, fade_out=0.6)))
```
- `render()` returns a peak-normalised `(2, n)` array, so levels are set only by the `place(..., gain_db)` call.
- `noise_sweep(dur, f0, f1)` rises when f1 > f0 and falls (a whoosh) when f1 < f0.
- `sub_drop()` makes a falling sine boom.
- `master()` drives the limiter by a fixed 2 dB, then peaks at −1 dBFS.

## Workflow
0. On a new machine, follow the setup guide and verify the needed engine with `probe` before composing.
1. Plan on a grid: tempo, key, bar-by-bar roles and the sync point (the hit). Write times as beats (`B = 60 / BPM`), not loose seconds.
2. Pick sounds with `find`, then `probe` every pitched one you plan to use (see below). Read `sfzmap` for any VCSL percussion.
3. Render one stem per part and `place` it on a timeline. Send related parts through a shared pedalboard bus: dry-ish drums, reverb/delay on music.
4. Shape the dynamics on purpose. For a transition: keep the groove a few dB under, crescendo into the hit, leave a short gap (around an 8th note) right before it, and make the hit the loudest moment, followed by a tail.
5. Verify, because you cannot listen. Run `check` and confirm the per-beat loudness follows the plan (build up, dip at the gap, peak at the hit). Then `Read` the spectrogram PNG.
6. Deliver a 48 kHz / 24-bit WAV plus the generating script, so it can be re-rendered or tweaked. Tell the user where the sync point is (for example "hit at 3.43 s"). Keep stems and probe files in scratch space.

## Probing: read the peaks before trusting a preset
Healthy pitched sounds show the played note plus its harmonics (+12, +19, +24), stable from early to late. Watch for:
- **Drift:** peaks move between early and late (Pads/Galaxy Pad). Avoid these for chords.
- **Chord or interval presets:** strong unrelated pitches, for example Chords/6 Osc Stab plays a whole chord from one key, and Pads/Film stacks a fifth (+7). Voice your chords with that in mind.
- **Octave offsets:**
  - VSCO Glockenspiel sounds +12.
  - Plucks/Techno Stab is around −24.
  - Basses/Rounded, Useful and Warm Square sound −12.
  - Drum presets track pitch: Drums/T8 Kick 1 note 45 sounds A1 (55 Hz).

  Transpose to compensate, and check the SFZ key range (`sfzmap`) before writing notes outside it.

## Gotchas
- **Notes at t=0:** Surge renders silence for notes at exactly t=0. `ak.render` adds a 0.5 s lead-in and crops it. If you call `audio_backend.render_notes` directly, offset the notes yourself.
- **`audio_backend.render_notes` side effects:** it always writes a WAV and quietly attenuates when the peak goes over 0.95. Don't rely on its levels across stems.
- **Preset names repeat across categories,** and `find_sounds` matches substrings of the full path. Always load by `"Category/Name"`; `find` prints them. For example, Basic DCO Polysynth lives under Synths.
- **VCSL unpitched instruments map articulations to keys.** For example, Suspended Cymbal 1 has 60–63 bowed, 64–67 crescendo rolls, 68 hits with velocity layers, and 69 bell; Mark Trees has 60 ascending, 61 descending and 62 fast ascending. A "cymbal" note can therefore turn out to be a roll.
- **Reversing:** reverse one-shots with `ak.reverse` so silence is trimmed on both ends. Otherwise the swell peaks early.
- **Measuring loudness:** raw RMS is dominated by sub-heavy kicks. Compare sections with K-weighted loudness (`check`, `ak.kweighted_db`).
- **Limiting:** don't slam a limiter after summing. It flattens exactly the hit you want to stand out.
- **Run-to-run variation:** some Surge presets contain randomness, so re-renders can differ by about 1–2 dB.
- **Built-in patterns:** Sequences, Rhythms and Arps presets run their own internal patterns. Write the notes yourself when timing must lock to a BPM.
- **Target levels:** around −16 to −14 LUFS with peaks at −1 dBFS works well for video beds and stingers.
