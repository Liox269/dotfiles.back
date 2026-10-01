local home   = os.getenv("HOME")
local hypr   = home .. "/.config/hypr"
package.path = package.path .. ";" .. home .. "/.config/caelestia/?.lua"

local function maybe_create(file, content)
    local f = io.open(file)
    if f then f:close() return end
    f = io.open(file, "w")
    if f then
        if content then f:write(content) end
        f:close()
    end
end

local function maybe_copy(src, dst)
    local out = io.open(dst)
    if out then out:close() return end
    local input = io.open(src, "r")
    if not input then return end
    out = io.open(dst, "w")
    if out then
        out:write(input:read("*a"))
        out:close()
    end
    input:close()
end

maybe_copy(hypr .. "/scheme/default.lua", hypr .. "/scheme/current.lua")
maybe_create(home .. "/.config/caelestia/hypr-vars.lua", "return {}\n")
local overrides = require("hypr-vars")

local gaming_file = home .. "/.config/caelestia/hypr-gaming.lua"
local f = io.open(gaming_file)
if f then
    f:close()
    package.path = package.path .. ";" .. home .. "/.config/caelestia/?.lua"
    local ok, gaming = pcall(require, "hypr-gaming")
    if ok and type(gaming) == "table" then
        for k, v in pairs(gaming) do overrides[k] = v end
    end
end

if type(overrides) == "table" then
    local vars = require("variables")
    for k, v in pairs(overrides) do vars[k] = v end
end

hl.monitor({ output = "HDMI-A-1", mode = "1920x1080@60", position = "0x0", scale = 1, transform = 0 })
hl.monitor({ output = "DP-2", mode = "1920x1080@144", position = "1920x0", scale = 1 })

require("hyprland.env")
require("hyprland.general")
require("hyprland.input")
require("hyprland.misc")
require("hyprland.animations")
require("hyprland.decoration")
require("hyprland.group")
require("hyprland.execs")
require("hyprland.rules")
require("hyprland.gestures")
require("hyprland.keybinds")

maybe_create(home .. "/.config/caelestia/hypr-user.lua")
require("hypr-user")
