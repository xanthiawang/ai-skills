# Human-confirmed local WeChat replies

Source-only deployment declaration. Personal voice samples, request previews,
credentials, database keys, compiled apps and send journals remain private local state.

Workflow: real history → private voice-conditioned draft → exact owner preview →
local Mac review of recipient identifiers and complete text → fixed native input →
unique new self-sent database row with server ID. The model has prepare/status
capabilities only. It cannot approve a Mac dialog or call the sender.

Initial beta accepts a single-line reply of 1..200 characters. The user must
manually open and verify the selected conversation. OCR checks the title; it
does not prove a recipient's internal ID. Duplicate/visually similar known
titles are rejected. Original WeChat process must have the expected database
root open. Moving/resizing the window or input area requires recalibration.
The focused accessible editor must expose a byte-for-byte matching text value;
unavailable accessibility values stop before Enter. OCR is only an additional
region check. Readback uses a fresh cursor captured when approval is claimed.

Accessibility and Screen Recording need explicit OS/user authorization.
Before other recipients can be sent to, an actual human-confirmed File Transfer
message `微信助手代发测试` must pass UI and database readback. Pending-before-typing
and one-use requests prevent blind retries after uncertainty. It is not a recipient
read receipt. No generated or synthetic chat dataset is used for verification.

Native components adapt the attributed MIT toolkit at
https://gist.github.com/acmerfight/0a01249ef72970d07a2603dbb629e80f,
revision `c98dbb10cf23c30e83d5d744905101b0880887a0`. `Capture.swift` retains its
ScreenCaptureKit/Vision capture implementation; `Send.swift` adapts its sender.
Full notice: `THIRD_PARTY_LICENSE`. Upstream generated-data tests are not included.

2026-10-14 artifact routing: source stays in the managed repository's
`config/wechat-assistant/reply-bridge/`; queue state, private calibration and
native app belong under `~/.local/share/wechat-assistant/`. Public redistribution
must use a reviewed allowlist and must exclude personal voice samples/profiles.

## Scoped capture diagnostics (2026-10-14)

The app provides a read-only diagnostic action before any send request. It opens the verified original process using NSWorkspace, yields activation and waits for verified foreground state. It reacquires geometry and tries app-to-window filter switching, app-only cropping, window-only cropping and desktop-independent single-window capture. The visible-region alternative constrains sourceRect before capture to the window rectangle; foreground, geometry and z-order overlap checks reject obscured frames before OCR. This is visible-region capture, not guaranteed isolated-window capture. Only frame counters/status/dimensions, bounded failure reasons and header-match booleans are written locally. Chat pixels/text are not saved. Successful capture-mode selection invalidates prior input calibration. Full-display output is not included.

Current real diagnostic on macOS 26.3.2: original-process opening resolved the activation denial; four isolated routes returned complete frames but the File Transfer title was not verified. Manual inspection showed only the input-method indicator with white chat contents, so nonblank pixels are not evidence of usable chat capture. Visible-region capture stopped on an overlapping layer-1000 window. The owner confirmed the demonstration-hide setting is absent in this WeChat version; do not keep asking for it. Screenpipe is healthy, but recent WeChat-labeled OCR was garbled and included unrelated window text, so it does not verify the recipient. The owner's built-in Command-4 screenshots work; the source now includes a read-only shortcut action that verifies the original account/process and foreground state before triggering Command-4. It never presses Return or completes a selection. Automated overlay observation/capture remains unverified. A supplied screenshot from another chat cannot authorize the File Transfer test or calibrate a clipped window. No test message or genuine send readback was observed; sending remains disabled.

2026-10-14: compiled replacements were installed only into the existing private runtime. Each prior signed app was copied into its private reply-bridge-archive directory before replacement. The same existing Screen Recording and Accessibility permissions were refreshed through System Settings; no broader permission was added. Generated images, private diagnostics and application backups are not committed.

Related existing source recipes: writing-voice/SKILL.md; dendron/sync/wechat-sync/SKILL.md; dendron/sync/session-sync/scripts/session_sync.py; dendron/command-center/scripts/session_index.py. Session indexing covers local Claude Code/Codex transcripts, not all web ChatGPT or Claude Desktop history. Inherited author paths must be adapted before deployment.
