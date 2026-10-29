---
name: sfx-sources
description: Find and download free sound effects from Pixabay, Freesound, Mixkit, and Kenney.
allowed-tools: Bash(python3 .claude/skills/sfx-sources/scripts/*)
---
You can't hear these clips, so lean on what people who did hear them left behind. Pixabay and Freesound rank results by those signals; Mixkit and Kenney give you only file names.

Order: Pixabay (huge catalog, ranked by ♥, no credit) → Freesound (real-world foley, ranked by ↓, uploader's description) → Mixkit (curated wav, names only) → Kenney (UI/game packs).
Exception: UI sounds (clicks, toggles, blips) start at Kenney. A purpose-made UI click beats a well-rated real-world one (a flashlight switch), and taking a whole run from one pack keeps them sounding like a set.

```
S=.claude/skills/sfx-sources/scripts/sfx.py
python3 $S pixabay "<q>"                   # English query; ♥likes ↓downloads
python3 $S freesound "<q>"                 # ↓downloads ★rating(votes) license description
python3 $S mixkit <tag>                    # one English word
python3 $S kenney [pack]                   # no pack: list packs
python3 $S get <dir> <key>...              # parallel download
```
`--urls` on a search adds preview links for the user to audition.

Reading the signals:
- Prefer the most-♥ / most-↓ clip that fits the cue, and quote the numbers when proposing it. A high count beats a high average: ★4.4(380) is stronger evidence than ★4.9(6).
- The Freesound description is the closest thing to listening: "built-in mic" or "made with my mouth" means lo-fi; a named recorder (Zoom, Sound Devices) and a clear source ("cork from a wine bottle") mean you know what you'll get. Reject clips whose description shows a different source than the cue, however popular.
- Freesound licenses: CC0 is free; BY needs a credit (`get` prints it); avoid BY-NC for anything commercial (`--license cc0|by` filters).
- Popularity says nothing about fit: a ♥3k "thud" can be a 3 s cinematic rumble. Check the duration, and measure with ffmpeg (tail length, where the energy sits) before trusting a top hit.
- Names alone (Mixkit, Kenney) are a weaker signal, so for those offer two or three candidates with `--urls` and let the user pick.

- Freesound times out: `python3 .claude/skills/sfx-sources/scripts/clash_freesound.py --fix`; if that fails, read references/local-setup.md.
- Freesound caps ~80 KB/s per connection: put all keys in one `get`.
- Pixabay is behind Cloudflare; the script auto-uses a curl_cffi venv in ~/.cache/sfx-sources/venv (built on first call). If it starts returning 403, Cloudflare tightened — fall back to WebFetch on the search page for titles.
