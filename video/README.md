# Video assets

Drop booth video files here. They're served at `/video/<filename>`.

## Malicious Skill attractor

The big-screen view (`/screen`) plays a looping **Malicious Skill** video as an
attractor during quiet spells. Place the file here:

```
video/malicious-skill.mp4
```

- It's served at `/video/malicious-skill.mp4` (the default the screen looks for).
- To use a different filename, open the screen with `?src=/video/<your-file>.mp4`.
- If the file is missing, `/screen` shows a "video not found" placeholder instead
  of breaking.

### Screen controls / modes

- `/screen` — leaderboard; press **V** or click **▶ Malicious Skill video** to
  show the attractor, **Esc** to close. Use **Unmute** for audio (browsers start
  muted so autoplay works).
- `/screen?video=1` — start directly on the video (single-screen "now playing").
- `/screen?video=auto` — auto-cycle: ~45s video, ~30s leaderboard, repeat
  (hands-off attractor loop for quiet spells).

Staff hook: *"That's a malicious agent skill getting caught — want to try it?"*
→ walk them to **Tame the Agent (#6)** or **Watch the MCP Wire (#7)**.

> Large media should ideally live in Git LFS or a CDN, not the repo — keep an eye
> on file size before committing the mp4.
