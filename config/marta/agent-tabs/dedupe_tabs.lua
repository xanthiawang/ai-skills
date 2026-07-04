local M = {}

local function normalize_path(path)
    if path == nil or path == "" or path == "/" then
        return path
    end
    return (path:gsub("/+$", ""))
end

function M.plan_closures(tabs)
    local groups = {}
    local order = {}

    for _, tab in ipairs(tabs) do
        local key = normalize_path(tab.path)
        if key ~= nil and key ~= "" then
            if groups[key] == nil then
                groups[key] = {}
                table.insert(order, key)
            end
            table.insert(groups[key], tab)
        end
    end

    local to_close = {}
    for _, key in ipairs(order) do
        local group = groups[key]
        if #group > 1 then
            local keep = group[1]
            for _, tab in ipairs(group) do
                if tab.is_active then
                    keep = tab
                    break
                end
            end
            for _, tab in ipairs(group) do
                if tab ~= keep then
                    table.insert(to_close, tab)
                end
            end
        end
    end

    return to_close
end

return M
