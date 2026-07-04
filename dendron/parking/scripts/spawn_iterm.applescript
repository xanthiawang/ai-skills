on run argv
    if (count of argv) < 3 then
        error "Usage: spawn_iterm.applescript <cwd> <tab_title> <resume_cmd>"
    end if
    set sessionCwd to item 1 of argv
    set tabTitle to item 2 of argv
    set resumeCmd to item 3 of argv
    tell application "iTerm"
        activate
        if (count of windows) is 0 then
            create window with default profile
        else
            tell current window
                create tab with default profile
            end tell
        end if
        tell current window
            tell current session
                set name to tabTitle
                write text "cd " & quoted form of sessionCwd & " && " & resumeCmd
            end tell
        end tell
    end tell
end run
