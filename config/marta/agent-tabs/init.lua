marta.expose()

local plugin_folder = tostring(globalContext.application.pluginFolder)
package.path = plugin_folder .. "/?.lua;" .. package.path

local dedupe = require("dedupe_tabs")

plugin {
    id = "org.kejunying.agenttabs",
    name = "Agent Tabs",
    apiVersion = "2.2",
    author = "Zixin Wang"
}

local function folder_path_for(pane)
    local folder = pane.model.folder
    if folder == nil then
        return nil
    end
    return folder.path.rawValue
end

local function collect_tabs(tab_manager, position)
    local active_index = tab_manager:getActiveTabIndex(position)
    local count = tab_manager:getCount(position)
    local tabs = {}

    for index = 0, count - 1 do
        local pane = tab_manager:getTab(position, index)
        table.insert(tabs, {
            index = index,
            path = folder_path_for(pane),
            is_active = index == active_index,
            pane = pane
        })
    end

    return tabs
end

local function close_planned_tabs(tab_manager, planned)
    table.sort(planned, function(left, right)
        return left.index > right.index
    end)

    for _, tab in ipairs(planned) do
        tab_manager:close(tab.pane)
    end

    return #planned
end

local function dedupe_position(tab_manager, position)
    local planned = dedupe.plan_closures(collect_tabs(tab_manager, position))
    return close_planned_tabs(tab_manager, planned)
end

local function tab_positions_for_context(context)
    local tab_manager = context.window.tabs
    local positions = {}

    local function add_position(pane)
        if pane == nil then
            return
        end

        local position = tab_manager:getPosition(pane)
        if position == nil then
            return
        end

        for _, existing in ipairs(positions) do
            if existing == position then
                return
            end
        end

        table.insert(positions, position)
    end

    add_position(context.activePane)
    add_position(context.inactivePane)

    return positions
end

action {
    id = "dedupe",
    name = "Deduplicate Tabs",
    apply = function(context)
        local tab_manager = context.window.tabs
        local closed = 0

        for _, position in ipairs(tab_positions_for_context(context)) do
            closed = closed + dedupe_position(tab_manager, position)
        end

        local label = "No duplicate tabs"
        if closed == 1 then
            label = "Closed 1 duplicate tab"
        elseif closed > 1 then
            label = "Closed " .. tostring(closed) .. " duplicate tabs"
        end

        context.activePane.view:showNotification(label, "agent-tabs-dedupe")
    end
}
