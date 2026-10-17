local lrc = {}
local lrcLoaded = false
local lastArtist = ''
local lastTitle = ''
local noLyrics = '\226\128\148 no lyrics \226\128\148'

local function stripBom(s)
  if s:sub(1, 3) == '\239\187\191' then
    return s:sub(4)
  end
  return s
end

local function sanitize(s)
  s = tostring(s or '')
  s = s:gsub('[<>:"/\\|?*]', '_')
  s = s:gsub('%c', '')
  return s
end

local function parseTimeToSeconds(str)
  str = tostring(str or '')
  local total = 0
  local h, m, s = str:match('^(%d+):(%d+):([%d%.]+)$')
  if h then
    total = total + tonumber(h) * 3600
    str = m .. ':' .. s
  end
  local m2, s2 = str:match('^(%d+):([%d%.]+)$')
  if m2 then
    return total + tonumber(m2) * 60 + tonumber(s2)
  end
  return tonumber(str) or 0
end

local function loadLrc(path)
  lrc = {}
  lrcLoaded = false
  local f = io.open(path, 'rb')
  if not f then return end
  local content = stripBom(f:read('*a'))
  f:close()
  content = content:gsub('\r\n', '\n')
  for line in content:gmatch('[^\n]+') do
    local tags = {}
    for t in line:gmatch('%[%d+:%d+[%.%d]*%]') do
      local tt = t:match('(%d+:%d+[%.%d]*)')
      table.insert(tags, parseTimeToSeconds(tt))
    end
    if #tags > 0 then
      local text = line:gsub('%[[^%]]*%]', '')
      text = text:gsub('^%s+', ''):gsub('%s+$', '')
      if text ~= '' then
        for _, ts in ipairs(tags) do
          table.insert(lrc, { time = ts, text = text })
        end
      end
    end
  end
  table.sort(lrc, function(a, b) return a.time < b.time end)
  lrcLoaded = (#lrc > 0)
end

local function lyricsFilePath()
  local artist = sanitize(lastArtist)
  local title = sanitize(lastTitle)
  if artist == '' and title == '' then return nil end
  return SKIN:GetVariable('@') .. 'lyrics\\' .. artist .. ' - ' .. title .. '.lrc'
end

local function setLyrics(prev, current, nextLine)
  SKIN:Bang('!SetOption', 'MeterPrev', 'Text', prev or '')
  SKIN:Bang('!SetOption', 'MeterCurrent', 'Text', current or '')
  SKIN:Bang('!SetOption', 'MeterNext', 'Text', nextLine or '')
end

local function setPlaceholder()
  setLyrics('', noLyrics, '')
end

local function findIndex(pos)
  if #lrc == 0 then return nil end
  if pos < lrc[1].time then return 1 end
  local lo, hi = 1, #lrc
  local idx = 1
  while lo <= hi do
    local mid = math.floor((lo + hi) / 2)
    if lrc[mid].time <= pos then
      idx = mid
      lo = mid + 1
    else
      hi = mid - 1
    end
  end
  return idx
end

function Initialize()
  setPlaceholder()
end

function Update()
  local artistM = SKIN:GetMeasure('MeasureArtist')
  local titleM = SKIN:GetMeasure('MeasureTitle')
  local posM = SKIN:GetMeasure('MeasurePosition')
  local stateM = SKIN:GetMeasure('MeasureState')
  if not (artistM and titleM and posM and stateM) then return end

  local artist = artistM:GetStringValue() or ''
  local title = titleM:GetStringValue() or ''

  if artist ~= lastArtist or title ~= lastTitle then
    lastArtist = artist
    lastTitle = title
    local path = lyricsFilePath()
    if path then
      loadLrc(path)
    else
      lrc = {}
      lrcLoaded = false
    end
  end

  local state = tonumber(stateM:GetValue()) or 0
  if not lrcLoaded or state == 0 then
    setPlaceholder()
    return
  end

  local pos = parseTimeToSeconds(posM:GetStringValue())
  local idx = findIndex(pos)
  if not idx then
    setPlaceholder()
    return
  end

  local prev = (idx > 1) and lrc[idx - 1].text or ''
  local current = lrc[idx].text
  local nextLine = (idx < #lrc) and lrc[idx + 1].text or ''
  setLyrics(prev, current, nextLine)
end
