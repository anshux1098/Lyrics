# MinimalLyrics Auto-Fetch Synced Lyrics — Design

Date: 2026-08-12
Status: Approved
Scope: Rainmeter skin `MinimalLyrics` only (config at `C:\Users\ASUS\Documents\Rainmeter\Skins\MinimalLyrics\`; working copy at `C:\lyricsh\MinimalLyrics\`).

## Problem

The `MinimalLyrics` skin shows synced LRC lyrics only from a local file named
`Artist - Title.lrc` in `@Resources\Lyrics\`. When listening via Apple Music for
Windows:

1. The plugin data path works — WebNowPlaying v3.0.0 reads Apple Music directly
   through Windows SMTC (title, artist, position, duration, state all verified live).
2. No LRC files exist for any real track (only `Sample Artist - Sample Title.lrc`),
   so every track shows `— NO LYRICS —`.
3. Apple Music metadata is messy (e.g. artist = `Nabeel Shaukat Ali - Bewajah (Coke
   Studio Season 8) - Single`), so even user-supplied files must match the normalized
   name exactly.

## Solution

Auto-fetch synced lyrics from **LRCLIB** (https://lrclib.net — free, no API key) when
no local file exists, then cache to disk so each track is fetched once. Local LRC files
continue to take priority. The skin queries by the current Apple Music artist/title/duration.

## Architecture

The skin keeps its existing measures and 3-line display. Changes:

- **Measures (Lyrics.ini):**
  - Add `[MeasureDuration]` — `Plugin=WebNowPlaying`, `PlayerType=Duration` (format `mm:ss`).
  - Add `[MeasureFetch]` — built-in `RunCommand`:
    - `Program=curl.exe` (ships with Windows)
    - `Parameter=-s -A "MinimalLyrics/1.0" --max-time 8 "<url>"` (URL percent-encoded in Lua)
    - `State=WAIT`, `OutputType=STRING`
    - The URL is injected at fetch time by Lua:
      `SKIN:Bang('!SetOption', 'MeasureFetch', 'Parameter', url)` then
      `SKIN:Bang('!CommandMeasure', 'MeasureFetch', 'Run')`.
  - Keep `Plugin=WebNowPlaying` for Title/Artist/Position/State (verified working).
- **Lua (Lyrics.lua):** add a fetch state machine, URL building, LRCLIB search/candidate
  selection, JSON extraction, JSON string unescaping, file caching, and a plain-text
  display path. Keep the existing local-file load path and `findIndex` binary search.

## Fetch & Cache Logic

1. **Trigger:** on artist/title change (existing detection), after the local-file check
   fails (or file absent).
2. **Query:** build `https://lrclib.net/api/search?q=<percent-encoded "artist title">`
   from the *cleaned* Artist and Title (same values used for the filename). Add the track
   duration (seconds) to the ranking, not the query.
3. **Candidate selection:** from the returned JSON array, choose the first entry where:
   - `instrumental` is `false`, and
   - `syncedLyrics` is a non-empty string (preferred) OR `plainLyrics` is non-empty, and
   - `|candidate.duration - trackDuration| <= 2` (tolerance), if both are available.
4. **Cache:**
   - Synced LRC → `@Resources\Lyrics\Artist - Title.lrc` (reuses existing `loadLrc`).
   - Plain lyrics → `@Resources\Lyrics\Artist - Title.txt` (no timestamps).
   - Filenames use the cleaned Artist/Title so local files and cache share one namespace.
5. **No-retry:** record the fetch key (`artist|title`) in-session; if fetching failed or
   found nothing, do not retry until the track changes.
6. **Instrumental:** no cache file; show `— instrumental —`.
7. **Failure (network/parse):** show `— no lyrics —`; no crash (pcall around all of it).

## JSON Extraction (Lua, hand-rolled)

LRCLIB responses are small and well-formed; no JSON library is used.

- Split `/api/search` array on `},{` boundaries into candidate chunks.
- Extract fields per chunk with a lazy-match helper: `key":"<value>"`, and
  `"instrumental":<bool>`, `"duration":<num>`.
- Unescape values: `\n` → newline, `\"` → `"`, `\\` → `\`.
- If a chunk is malformed (unbalanced `{`/`}` or missing fields), skip it; if all chunks
  fail, treat as "no lyrics" for this track.

## URL Encoding (Lua)

Percent-encode reserved characters (`%`, space, `"`, `#`, `&`, `+`, `,`, `/`, `:`, `;`,
`<`, `=`, `>`, `?`, `@`, `[`, `]`, `^`, `` ` ``, `{`, `|`, `}`, `~`) in the query value.
Cleaned names are guaranteed free of `"`, `<`, `>`, `:`, `/`, `\`, `|`, `?`, `*` (removed
by the existing `clean()` and Substitute), so the encoded URL contains no shell-quoting
problems.

## Normalization (Substitute additions)

Add to `[MeasureArtist]` RegExpSubstitute, before the whitespace-collapse rules:

```
"(?i)\s*-\s*single\s*$":"", "(?i)\s*-\s*ep\s*$":"", "(?i)\s*-\s*album\s*$":""
```

Keeps existing rules (parentheticals, brackets, `feat./ft.`, `remix`, whitespace). This
makes both the query and the cache filename cleaner.

## Display Behavior

- **Synced:** existing 3-line prev/current/next rendering from cached `.lrc`.
- **Plain:** whole plain lyrics rendered as static text in the Current line
  (`ClipString=2`, W=350), Prev/Next empty.
- **Placeholders:** no lyrics → `— NO LYRICS —`; instrumental → `— INSTRUMENTAL —`;
  stopped/paused → existing placeholder behavior.
- **Blocking:** with `State=WAIT`, the skin update may pause up to ~8s once per new track
  while curl runs (`--max-time 8`). Bounded and acceptable.

## Error Handling

- curl timeout/non-zero exit → empty output → treated as not-found for the track.
- Malformed JSON / unexpected shapes → skipped candidate or not-found; never a crash.
- Track changes mid-fetch → result discarded (verify artist/title unchanged after the
  command completes before using/caching the response).

## Testing

1. Live: with Apple Music playing, activate the skin; confirm a `.lrc` (or `.txt`) cache
   file appears in `@Resources\Lyrics\` for the current track and the display updates.
2. Cache hit: play the same track again (or refresh the skin) → confirm **zero** network
   requests (verify via `curl` access log is not feasible; instead verify no new file
   writes and instant display, plus the fetch-key guard in Lua).
3. Plain-lyrics path: pick a track with only `plainLyrics`; confirm `.txt` cache and
   static current-line display.
4. Instrumental/not-found: confirm placeholders render and no repeated requests.
5. JSON/unescape correctness: run the Lua extraction helpers against a captured sample
   LRCLIB response.
6. Existing behavior intact: local `.lrc` files still win; prev/current/next still sync
   from local files; state==0 still shows placeholder.

## Out of Scope

- Other skins (older `Lyrics` skin unchanged).
- Switching plugins (WebNowPlaying verified working; MediaPlayer.dll / WindowsNowPlaying.dll
  remain available fallbacks but are not adopted here).
- Playback control buttons, cover art, scrolling lyric views.
- Retry/backoff beyond one attempt per track per session.
