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

The app provides a read-only diagnostic action before any send request. It activates original WeChat, reacquires geometry, and tries app-to-window filter switching, app-only cropping, window-only cropping and desktop-independent single-window capture. Only frame counters/status/dimensions and header-match booleans are written locally. Chat pixels/text are not saved. Successful capture-mode selection invalidates prior input calibration. Full-display fallback is not included. Current real diagnostic: three routes produced no callbacks, the independent-window route produced complete frames but no usable image; sending remains disabled. WeChat demonstration-hide preferences and same-app window ordering still require checking.

Related existing source recipes: writing-voice/SKILL.md; dendron/sync/wechat-sync/SKILL.md; dendron/sync/session-sync/scripts/session_sync.py; dendron/command-center/scripts/session_index.py. Session indexing covers local Claude Code/Codex transcripts, not all web ChatGPT or Claude Desktop history. Inherited author paths must be adapted before deployment.
