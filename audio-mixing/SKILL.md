---
name: audio-mixing
description: Mix existing tracks or refine audio balance, EQ, dynamics, stereo placement, and loudness using FFmpeg.
---
# Audio mixing

Use FFmpeg/ffprobe; Python standard library optional. No extra packages, plugins, or models. Preserve sources; use float WAV intermediates.

1. Inspect duration, channels, and sample rate with `ffprobe`; measure LUFS/true peak using `ebur128=peak=true`. Align tracks; match rates/layouts.
2. Balance `volume` and `pan` first. Leave roughly 6 dB headroom; avoid independent stem normalization.
3. EQ in context: high-pass unwanted rumble without removing fundamentals; cut masking/resonances before boosting. Start with 1-3 dB moves. Check 200-500 Hz mud, 2-5 kHz harshness, 5-9 kHz sibilance; never cut blindly. Use `highpass`, `equalizer`.
4. Compress uneven dynamics only (`acompressor`; start near 2:1, preserve transients). Automate gain or duck music under speech (`sidechaincompress`). Fade edits; preserve tails.
5. Sum explicit gains with `amix=inputs=N:normalize=0`; choose duration deliberately. Check bus peaks; lower gains if overloaded.
6. Honor delivery specs; otherwise start at -16 LUFS-I, <= -1 dBTP for full programs. Judge short SFX by peaks/context. Apply two-pass `loudnorm` to the final mix: reuse measured I/LRA/TP/threshold and target offset with identical targets. Prefer linear mode; check dynamic fallback. Set output sample rate explicitly.
7. Compare at matched loudness; check transitions, quiet/loud passages, and mono. Disclose unavailable listening; meters cannot confirm sound quality.
8. Export requested format (default: 48 kHz/24-bit WAV). Remeasure the decoded delivery file for loudness, true peak, duration, and channels. Deliver commands and measurements.
