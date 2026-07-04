package.loaded["dedupe_tabs"] = nil

local plugin_root = ".."
local captured_action = nil

marta = {
    expose = function()
        _G.plugin = function(_) end
        _G.action = function(declaration)
            captured_action = declaration
        end
    end
}

globalContext = {
    application = {
        pluginFolder = plugin_root
    }
}

dofile("../init.lua")

local tabs_by_position = {
    active = {
        { model = { folder = { path = { rawValue = "/tmp/project" } } } },
        { model = { folder = { path = { rawValue = "/tmp/project" } } } }
    },
    inactive = {
        { model = { folder = { path = { rawValue = "/tmp/other" } } } },
        { model = { folder = { path = { rawValue = "/tmp/other" } } } }
    }
}

local closed = {}
local active_position = { name = "active" }
local inactive_position = { name = "inactive" }
local tab_manager = {}

function tab_manager:getPosition(pane)
    return pane.position
end

function tab_manager:getActiveTabIndex(position)
    return 0
end

function tab_manager:getCount(position)
    return #tabs_by_position[position.name]
end

function tab_manager:getTab(position, index)
    return tabs_by_position[position.name][index + 1]
end

function tab_manager:close(pane)
    table.insert(closed, pane)
end

local notification = nil
local context = {
    window = {
        tabs = tab_manager
    },
    activePane = {
        position = active_position,
        view = {
            showNotification = function(_, label)
                notification = label
            end
        }
    },
    inactivePane = {
        position = inactive_position
    }
}

assert(captured_action ~= nil, "action should be registered")
captured_action.apply(context)

assert(#closed == 2, "one duplicate tab in each pane should close")
assert(notification == "Closed 2 duplicate tabs", "status notification should report both closures")

print("ok")
