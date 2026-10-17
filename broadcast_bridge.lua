-- UDP Broadcast Bridge for MinimalLyrics
-- Writes current lyric state to a JSON file that the Python sidecar reads.
-- Add this to your existing Lyrics.lua

local BROADCAST_PATH = 'C:\\\\Users\\\\ASUS\\\\AppData\\\\Local\\\\Temp\\\\lyricsh_broadcast.json'
local lastBroadcast = ''

local function broadcastState(artist, title, prev, current, nextLine, state, position, duration)
  -- Build JSON manually (Lua has no built-in JSON)
  local function esc(s)
    if not s then return '' end
    s = tostring(s)
    s = s:gsub('\\', '\\\\')
    s = s:gsub('"', '\\"')
    s = s:gsub('\n', '\\n')
    s = s:gsub('\r', '\\r')
    s = s:gsub('\t', '\\t')
    return s
  end

  local json = string.format(
    '{"artist":"%s","title":"%s","prev":"%s","current":"%s","next":"%s","state":%d,"position":%s,"duration":%s}',
    esc(artist), esc(title), esc(prev), esc(current), esc(nextLine),
    state,
    tostring(position or 0),
    tostring(duration or 0)
  )

  -- Only write if changed (avoid disk spam)
  if json == lastBroadcast then return end
  lastBroadcast = json

  local f = io.open(BROADCAST_PATH, 'w')
  if f then
    f:write(json)
    f:close()
  end
end

-- Hook into your existing setLyrics function.
-- Find this in Lyrics.lua:
--
--   local function setLyrics(prev, current, nextLine)
--     ... existing code ...
--   end
--
-- And add this line right before the closing 'end':
--
--   broadcastState(lastArtist, lastTitle, prev, current, nextLine, state, position, duration)
--
-- You'll need to pass state/position/duration into setLyrics or
-- access them from the Update() scope. The simplest approach:
-- make them file-local variables set in Update() before setLyrics is called.
