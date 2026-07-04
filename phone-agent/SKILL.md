---
name: phone-agent
description: "Use when the user wants an AI voice agent to place an outbound phone call on their behalf: calling a company, navigating a phone menu (IVR), waiting on hold, asking a question, confirming or changing an order/appointment/account, or following up by phone. Also for cloning a voice to use on such calls. Powered by the Bland AI API and driven from the shell."
---

# Phone Agent (Bland AI)

## Overview

Place real outbound phone calls with an AI voice agent and pull the transcript back into the session. The agent dials, listens, talks, navigates IVR menus, holds, and ends the call per a task script you write. Driven entirely from the shell via `bland_call.sh` (Bland REST API).

## When to use

- User asks you to "call X", "have an AI call Y", "get on hold with Z for me".
- Routine phone tasks: utilities, insurance, airlines, clinics, reservations, status checks, simple follow-ups.
- Cloning a voice from an audio sample for use on calls.

When NOT to use:
- Anything requiring legally binding consent, payments, or moving money: have Albert do it himself.
- Calls needing account-holder identity verification you don't have (account number, SSN, DOB). The agent will dead-end at verification. Gather credentials first.
- Sensitive/personal conversations: use a real call.

## Prerequisites

- Bland account + credits (billed per minute). Dashboard: app.bland.ai → Settings → API Keys.
- API key stored at `~/.config/bland/api_key` (chmod 600, never in any repo) or `$BLAND_API_KEY`.
- Default voice is "Esteban" (id `60974bf8-151e-44e2-812e-4dc958aac5f3`, friendly Hispanic male). Albert's own clone is `fe8bd7bf-4bed-474e-9a4b-7faed121bc96` ("Albert"). Pass a different id as the 3rd arg to `call`, or set `$BLAND_DEFAULT_VOICE`.

## Safety rule (do not skip)

A live call is outward-facing and irreversible: it costs money and rings a real person. **Before dialing a real number, confirm with Albert the exact target number and the task script.** Read-only steps (`voices`, `status`, `watch`) need no confirmation. A test call to Albert's own cell is the safe way to tune voice + script.

## Quick reference

```bash
S=~/programs/ai-skills/phone-agent/bland_call.sh
$S voices                                  # list owned/cloned voices
$S clone "Albert" /path/sample.wav         # clone a voice (auto-converts to mp3)
$S call +18007435000 ./tasks/pge.txt       # place a call (task = file or inline string)
$S call +1XXXXXXXXXX "Inline task..." VOICE_ID
$S watch                                    # poll last call to completion, print transcript
$S status [call_id]                        # status + transcript on demand
```

Phone numbers must be E.164 (`+1` + 10 digits). The last `call_id` is saved to `~/.config/bland/last_call_id`, so `watch`/`status` need no argument.

## Writing the task script (this determines call quality)

The `task` is the agent's full instructions. Bad scripts cause rambling or hangups. A good script has:

1. Identity + goal in one line: who the agent is, why it's calling.
2. The exact ask, with the specific data it needs to give or get.
3. IVR / hold handling: "Press or say the option for billing. If put on hold, wait silently until a person answers."
4. Verification data it may be asked for (only what you have).
5. Stop condition: what counts as done, and to thank-and-hang-up after.

Keep it concrete and bounded. Example (`tasks/pge.txt`):

```
You are calling PG&E on behalf of the account holder about service at
14 Estates Ct, San Carlos, CA 94070. Goal: find out why power is off and
how to restore it. Likely a non-payment disconnection.
Navigate the menu to billing / service. If asked, the account number is
<ACCOUNT_NUMBER> and the name on the account is <NAME>.
Ask: (1) is the account disconnected for non-payment? (2) what is the
past-due balance and how is it paid? (3) once paid, what is needed to
reconnect and how soon? If put on hold, wait silently for a human.
When you have the answers, thank them and end the call.
```

## Verify before claiming done

After `watch`/`status`, read the actual transcript. Report what the agent learned from the transcript, not what you hoped it would do. If `answered_by` is voicemail or the call errored, say so and retry or escalate.

## Common mistakes

- Putting the API key in the JSON body. It is an HTTP header (`authorization: <key>`), not a body field.
- Vague one-line task ("ask about my account"). The agent improvises and fails. Write the full script.
- Dialing before confirming the number/script with Albert.
- Expecting the agent to pass identity verification without the account number. It can't.
- Forgetting credits/billing on the Bland account: calls silently fail to start without funds.
