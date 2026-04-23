# Playtesting Mir's End

Every playthrough is automatically recorded and can be exported as a
JSON file for review. This doc covers:

- How to run a session
- How to export it
- What the JSON looks like
- How to share it for discussion
- How to debug someone else's session

## Running a session

```bash
cd game && python3 -m http.server 8080
```

Then open `http://localhost:8080/play.html` in a browser. Click
**New Game**, hit **Escape** to skip the intro if you want, and play.

The session starts recording the moment New Game fires. Every time
the story panel updates — your command echo, the interpreter's
response, an autosave notice — the session is persisted to
`localStorage.mirsend_session`.

If the page crashes or you close the tab, the last-persisted
snapshot survives. The next time the page loads, the session is
still there; starting a **New Game** replaces it.

## Exporting a session

Three ways to trigger an export, all equivalent:

1. Click the **Export** button in the right sidebar (next to
   Save / Load / Continue).
2. Keyboard shortcut **Ctrl+E** (Windows/Linux) or **Cmd+E** (macOS).
3. In the browser devtools console:
   ```js
   window.MirsEnd.downloadSession()   // triggers the download
   window.MirsEnd.exportSession()      // returns the object
   ```

The download is a JSON file named
`mirsend-session-<ISO-timestamp>.json`. You can rename it anything.

## The JSON format

```json
{
  "version": 1,
  "startedAt": "2026-04-20T12:30:00.000Z",
  "exportedAt": "2026-04-20T12:45:22.000Z",
  "turnCount": 62,
  "commandHistory": [
    "open emergency locker",
    "take flashlight",
    "switch on flashlight",
    "pull lever",
    "n",
    "..."
  ],
  "transcript": "[Interpreter connected.]\nYou wake to a shout...\n> open emergency locker\nYou open the emergency locker, revealing a flashlight.\n[Your score has just gone up by one point.]\n...",
  "finalState": {
    "currentRoom": "Command Module",
    "o2": 44,
    "morale": 57,
    "inventory": ["multimeter", "Yevgenia's flight notebook", "flashlight"],
    "gameStarted": true
  }
}
```

- `commandHistory` — every command the player typed, in order
- `transcript` — the full `#story-output` text, chronological (includes
  system messages, autosave notices, scoring messages)
- `finalState` — snapshot of `window.MirsEnd.getState()` at export time
- Timestamps are ISO-8601 UTC

## Sharing a session for discussion

Paste the JSON into chat, or attach the file. For shorter discussions,
just paste `commandHistory` and the relevant slice of `transcript`.

## Debugging someone else's session

The `commandHistory` is reproducible: feed it back into the game in
order and you'll reach the same final state (within ±1 oxygen turn,
since oxygen is a real-time-ish counter).

Playwright example:
```ts
for (const cmd of session.commandHistory) {
  await sendCommand(page, cmd);
}
```

If a session exposes a bug, write the reproducing commands into a
regression test at `tests/e2e/<bug-id>.spec.ts`.

## Notes

- Sessions are stored client-side only. Nothing ever leaves the
  browser unless you export and share it yourself.
- Exporting does not clear the session; the recording keeps going.
- Starting a new game overwrites the stored session. If you want to
  keep an old session, export it before clicking New Game.
