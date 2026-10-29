---
name: procedural-audio
description: Compose and render original music and sound effects offline in Python with the local Surge XT, sfizz, VSCO 2 CE and VCSL setup (`local_music`, pedalboard, numpy). Use for any request to generate, synthesize or program audio (配乐/转场音乐/片头/音效生成/合成音效), such as transition stingers, jingles, loops, risers, whooshes, impacts, UI blips or ambiences, even if the user doesn't name the tools. Use sfx-sources instead when they want to download existing clips.
allowed-tools: Bash(python3 .claude/skills/procedural-audio/scripts/*)
---
# Procedural music & SFX

Everything renders offline with the system `python3` (3.14); there is no audio device, GUI or network. Paths here are relative to the project root (`~/Downloads`).

## What's installed
- `local_music`: `find_sounds(query, kind)`, `surge(preset)`, `sfizz(sfz)`, `render_notes(plugin, [(midi, start_s, len_s, vel)], out_wav)`.
- Surge XT: 3,008 presets in `~/Library/Application Support/Surge XT`, grouped by category folders: Basses, Leads, Pads, Keys, Plucks, FX, Drums, Percussion, Synths, Polysynths, Atmospheres, Chords, Bells, Mallets, Strings, Brass, Winds, Sequences, Rhythms and more.
- SFZ in `~/Music/Sample Libraries`:
  - VSCO 2 CE: orchestral strings, winds, brass, harp, glockenspiel, timpani, piano, organ.
  - VCSL: pianos, harpsichords, world plucks, mallets, cymbals, gongs, mark trees, toy and found percussion, drums.
- Effects and tools: pedalboard (Reverb, Delay, Compressor, Limiter, filters, Chorus, Phaser, Distortion, PitchShift, Convolution), plus numpy, scipy, soundfile, pyloudnorm and matplotlib.

## Kit
`scripts/audio_kit.py` wraps the repetitive parts. Use the CLI to pick sounds:
```
K=.claude/skills/procedural-audio/scripts/audio_kit.py
python3 $K find "kick" [--kind surge|sfz]   # prints load() specs: "Drums/T8 Kick 1", "VSCO-2-CE-1.1.0/Harp.sfz"
python3 $K probe "Pads/Film" 57 69          # attack, decay, spectral peaks (MIDI) early vs late
python3 $K sfzmap "Mark Trees.sfz"          # which key/velocity plays which sample
python3 $K check out.wav --bpm 140 --png /tmp/x.png   # peak, LUFS, loudness per beat, spectrogram
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
- **Notes at t=0:** Surge renders silence for notes at exactly t=0. `ak.render` adds a 0.5 s lead-in and crops it. If you call `lm.render_notes` directly, offset the notes yourself.
- **`lm.render_notes` side effects:** it always writes a WAV and quietly attenuates when the peak goes over 0.95. Don't rely on its levels across stems.
- **Preset names repeat across categories,** and `find_sounds` matches substrings of the full path. Always load by `"Category/Name"`; `find` prints them. For example, Basic DCO Polysynth lives under Synths.
- **VCSL unpitched instruments map articulations to keys.** For example, Suspended Cymbal 1 has 60–63 bowed, 64–67 crescendo rolls, 68 hits with velocity layers, and 69 bell; Mark Trees has 60 ascending, 61 descending and 62 fast ascending. A "cymbal" note can therefore turn out to be a roll.
- **Reversing:** reverse one-shots with `ak.reverse` so silence is trimmed on both ends. Otherwise the swell peaks early.
- **Measuring loudness:** raw RMS is dominated by sub-heavy kicks. Compare sections with K-weighted loudness (`check`, `ak.kweighted_db`).
- **Limiting:** don't slam a limiter after summing. It flattens exactly the hit you want to stand out.
- **Run-to-run variation:** some Surge presets contain randomness, so re-renders can differ by about 1–2 dB.
- **Built-in patterns:** Sequences, Rhythms and Arps presets run their own internal patterns. Write the notes yourself when timing must lock to a BPM.
- **Target levels:** around −16 to −14 LUFS with peaks at −1 dBFS works well for video beds and stingers.
