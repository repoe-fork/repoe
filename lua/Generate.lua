local params = { ... }
local path = params[1]:gsub("(.*)/src/Data/.*.lua$", "%1")
local file = params[1]:gsub(".*/src/Data/(.*).lua$", "%1")

print(path, file)

latestTreeVersion = '0_0'
launch = {}

function LoadModule(module, ...)
    local loaded, error = loadfile(path .. "/src/" .. module .. (module:find(".lua") and "" or ".lua"))
    if error or not loaded then
        print("error loading module", error)
    else
        return loaded(...)
    end
end

function triangular(n)
    return n * (n + 1) / 2
end

function copyTable(tbl, noRecurse)
    local out = {}
    for k, v in pairs(tbl) do
        if not noRecurse and type(v) == "table" then
            out[k] = copyTable(v)
        else
            out[k] = v
        end
    end
    return out
end

function isValueInTable(tbl, val)
    for k, v in pairs(tbl) do
        if val == v then
            return k
        end
    end
end

function isValueInArray(tbl, val)
    for i, v in ipairs(tbl) do
        if val == v then
            return i
        end
    end
end

function sanitiseText(text)
    if not text then return nil end
    -- Something something unicode support something grumble
    -- Only do these replacements if a char from 128-255 or '<' is found first
    return text:find("[\128-\255<]") and text
        :gsub("%b<>", "")
        :gsub("\226\128\144", "-") -- U+2010 HYPHEN
        :gsub("\226\128\145", "-") -- U+2011 NON-BREAKING HYPHEN
        :gsub("\226\128\146", "-") -- U+2012 FIGURE DASH
        :gsub("\226\128\147", "-") -- U+2013 EN DASH
        :gsub("\226\128\148", "-") -- U+2014 EM DASH
        :gsub("\226\128\149", "-") -- U+2015 HORIZONTAL BAR
        :gsub("\226\136\146", "-") -- U+2212 MINUS SIGN
        :gsub("\195\164", "a")     -- U+00E4 LATIN SMALL LETTER A WITH DIAERESIS
        :gsub("\195\182", "o")     -- U+00F6 LATIN SMALL LETTER O WITH DIAERESIS
        -- single-byte: Windows-1252 and similar
        :gsub("\150", "-")         -- U+2013 EN DASH
        :gsub("\151", "-")         -- U+2014 EM DASH
        :gsub("\228", "a")         -- U+00E4 LATIN SMALL LETTER A WITH DIAERESIS
        :gsub("\246", "o")         -- U+00F6 LATIN SMALL LETTER O WITH DIAERESIS
        -- unsupported
        :gsub("[\128-\255]", "?")
        or text
end

function tableConcat(t1, t2)
    local t3 = {}
    for i = 1, #t1 do
        t3[#t3 + 1] = t1[i]
    end
    for i = 1, #t2 do
        t3[#t3 + 1] = t2[i]
    end
    return t3
end

require(path .. ".src.GameVersions")
require(path .. ".src.Data.Global")

local function makeSkillMod(modName, modType, modVal, flags, keywordFlags, ...)
    return {
        name = modName,
        type = modType,
        value = modVal,
        flags = flags or 0,
        keywordFlags = keywordFlags or 0,
        ...
    }
end
local function makeFlagMod(modName, ...)
    return makeSkillMod(modName, "FLAG", true, 0, 0, ...)
end
local function makeSkillDataMod(dataKey, dataValue, ...)
    return makeSkillMod("SkillData", "LIST", { key = dataKey, value = dataValue }, 0, 0, ...)
end
local function clean(map, visited, keys, jpath)
    if type(map) == 'table' then
        for k, v in pairs(map) do
            keys[k] = k
            if type(k) == "table" or type(k) == "function" then
                map[k] = nil
            elseif type(v) == 'function' then
                map[k] = nil
            elseif type(v) == 'table' then
                local seen = visited[v]
                visited[v] = jpath and jpath .. "/" .. k or true
                if seen == true then
                    map[k] = nil
                elseif seen and jpath:find(seen) then
                    -- recursive reference
                    map[k] = { ["$ref"] = seen }
                else
                    clean(v, visited, keys, jpath and jpath .. "/" .. k)
                end
            end
        end
    end
    return map
end

local json = require("dkjson")
if file == "Global" then
    return
end

local output = {}
local result
if file:find("Uniques/Special") then
    require(path .. ".src.Modules.Data")
end
if file == "SkillStatMap" then
    result = loadfile(params[1])(makeSkillMod, makeFlagMod, makeSkillDataMod) or output
else
    result = loadfile(params[1])(output, makeSkillMod, makeFlagMod, makeSkillDataMod) or output
end

local keys = {}
clean(result, {}, keys, "#")
local keyorder = {}
for k, _ in pairs(keys) do table.insert(keyorder, k) end
table.sort(keyorder, function(l, r)
    if type(l) == type(r) then
        return l < r
    else
        return type(l) > type(r)
    end
end)

io.open((params[2] or "data/") .. file .. ".min.json", "w"):write(json.encode(result, { keyorder = keyorder }))
io.open((params[2] or "data/") .. file .. ".json", "w"):write(json.encode(result, { indent = true, keyorder = keyorder }))
