local params = { ... }
local path = params[1]:gsub("(.*)/src/Data/.*.lua$", "%1")
local file = params[1]:gsub(".*/src/Data/(.*).lua$", "%1")

print(path, file)

latestTreeVersion = '0_0'
launch = {}

function LoadModule(module, ...)
    return loadfile(path .. "/src/Data/" .. module .. ".lua")(...)
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
local function clean(map, visited, keys)
    if type(map) == 'table' then
        for k, v in pairs(map) do
            if type(k) == "string" then
                keys[k] = k
            end
            local seen = visited[v]
            visited[v] = true
            if seen then
                map[k] = nil
            elseif type(v) == 'function' then
                map[k] = nil
            elseif type(v) == 'table' then
                clean(v, visited, keys)
            end
        end
    end
    return map
end

local json = require("dkjson")
if file == "Global" then
    require(path .. ".src.Modules.Data")
    clean(data, {}, {})
    io.open((params[2] or "data/") .. "DataModule.min.json", "w"):write(json.encode(data))
    io.open((params[2] or "data/") .. "DataModule.json", "w"):write(json.encode(data, { indent = true }))
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
clean(result, {}, keys)
local keyorder = {}
for k, _ in pairs(keys) do table.insert(keyorder, k) end
table.sort(keyorder)

io.open((params[2] or "data/") .. file .. ".min.json", "w"):write(json.encode(result, { keyorder = keyorder }))
io.open((params[2] or "data/") .. file .. ".json", "w"):write(json.encode(result, { indent = true, keyorder = keyorder }))
