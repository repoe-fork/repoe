local params = { ... }
local file = (params[2] or "data") .. params[1]:gsub(".*/Data(/.*).lua$", "%1")

if file == "Data/Global" then
    return
end
print(file)

latestTreeVersion = '0_0'

function LoadModule(module, ...)
    return loadfile("pob/src/" .. module .. ".lua")(...)
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

require("bit")
require("pob.src.Data.Global")

local output = {}
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
local result
if file:find("Data/Uniques/Special") then
    require("pob.src.Modules.Data")
end
if file == "Data/SkillStatMap" then
    result = loadfile(params[1])(makeSkillMod, makeFlagMod, makeSkillDataMod) or output
else
    result = loadfile(params[1])(output, makeSkillMod, makeFlagMod, makeSkillDataMod) or output
end

local function removeFuncs(map)
    if type(map) == 'table' then
        for k, v in pairs(map) do
            if type(v) == 'table' then
                removeFuncs(v)
            elseif type(v) == 'function' then
                map[k] = nil
            end
        end
    end
end

removeFuncs(result)

local json = require("dkjson")
io.open(file .. ".json", "w"):write(json.encode(result))
