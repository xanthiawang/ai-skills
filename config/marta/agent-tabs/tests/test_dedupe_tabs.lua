package.path = "./?.lua;../?.lua;" .. package.path

local dedupe = require("dedupe_tabs")

local function same_values(actual, expected)
    if #actual ~= #expected then
        return false
    end
    for i = 1, #actual do
        if actual[i] ~= expected[i] then
            return false
        end
    end
    return true
end

local function assert_indices(tabs, expected, label)
    local plan = dedupe.plan_closures(tabs)
    local indices = {}
    for i, tab in ipairs(plan) do
        indices[i] = tab.index
    end
    assert(same_values(indices, expected), label)
end

assert_indices({
    { index = 0, path = "/tmp/project", is_active = false },
    { index = 1, path = "/tmp/other", is_active = false },
    { index = 2, path = "/tmp/project", is_active = true },
    { index = 3, path = "/tmp/project", is_active = false },
}, { 0, 3 }, "keeps active tab when duplicate group contains active tab")

assert_indices({
    { index = 0, path = "/tmp/project", is_active = false },
    { index = 1, path = "/tmp/other", is_active = false },
    { index = 2, path = "/tmp/project", is_active = false },
    { index = 3, path = "/tmp/other", is_active = true },
}, { 2, 1 }, "keeps first duplicate unless active tab belongs to that path")

assert_indices({
    { index = 0, path = "/tmp/project/", is_active = false },
    { index = 1, path = "/tmp/project", is_active = false },
    { index = 2, path = "/", is_active = false },
}, { 1 }, "normalizes trailing slashes except filesystem root")

print("ok")
