ForcAD setup for the competition
==================================

This fork uses the ForcAD API described in the organizer-provided `ch-api.md`.

## Local environment variables

Set these in the shell where the farm server is started. Do not put tokens or
passwords into `server/config.py`, a commit, an issue, or a pull request.

If the organizer-provided `team_data.txt` is in the current directory, load
the team token without printing it:

```sh
export FORCAD_URL='http://10.183.2.10'
export FORCAD_TEAM_TOKEN="$(sed -n 's/^team_token=//p' ./team_data.txt | head -n 1)"
export FARM_SERVER_PASSWORD='<choose a strong farm web password>'
# Optional: enables X-Token authentication for Farm Client API requests.
export FARM_API_TOKEN='<choose a separate long random token>'
```

You can override the full receiver endpoint with `FORCAD_FLAGS_URL`; it must
point to the `/flags` route. Otherwise the config uses
`$FORCAD_URL/flags`.

## Receiver protocol

The `forcad_http` protocol sends:

- HTTP `PUT` to `/flags` (the handout specifies PUT, not POST);
- `X-Team-Token` from `FORCAD_TEAM_TOKEN`;
- a JSON array of flag strings, with at most 100 flags per request.

The server checks every returned `msg`, validates that the response contains
one result per submitted flag in the documented order, and does not treat
HTTP 200 alone as acceptance. The competition rules document the rejection
messages `Wrong flag`, `Flag is your own`, and `Flag is too old`. Positive
messages are recognized using the legacy ForcAD adapter's `accepted` and
`congrat` phrases. Any unknown verdict remains `QUEUED` for retry.

On HTTP 429, the protocol waits for `Retry-After` (seconds or HTTP date) and
retries a bounded number of times. The farm defaults to 100 flags per
one-second cycle, below the documented 200 flags/second refill rate. This is
a conservative submission rate, not a way to bypass the receiver quota.

## Team list and competition stages

The committed default `TEAMS` list contains only the NPC test service
`10.149.88.2`, as listed in the API handout. The separate
`10.149.86.2` value in team data is labelled as your own vulnbox address and
is not put in the target list.

The handout provides the public attack-data endpoint:

```sh
curl -fsS "$FORCAD_URL/api/v1/client/attack_data/"
```

The farm config expects `TEAMS` as a Python mapping of display names to
service addresses. The handout does not include a sample attack-data JSON
schema, so this repository does not guess how to convert that response.
Before the scored phase, populate `TEAMS` from organizer-provided attack-data
and use only targets permitted for the active stage. During preparation,
keep only NPC. Run the farm client from an allowed participant computer,
not from the team vulnbox or external VPS/cloud resources.

## Run the server

Install dependencies and start the farm server as described in
`docs/ru/farm_server.md`. The web-interface password is the value of
`FARM_SERVER_PASSWORD`. If `FARM_API_TOKEN` is set, pass that separate value
to Farm Client using its `--token` option.
