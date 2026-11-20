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
export FARM_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

Both `FARM_SERVER_PASSWORD` and `FARM_API_TOKEN` are required; the server
refuses to start without them. Share the generated `FARM_API_TOKEN` only with
the team's Farm Clients. It is separate from the ForcAD team token.

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

## Start the farm server

From the repository root, in the same shell where the variables above are set:

```sh
cd server
python3 -m pip install -r requirements.txt
./start_server.sh
```

The web interface uses `FARM_SERVER_PASSWORD`.

A Farm Client connects to the farm server using its URL and the separate farm
API token:

```sh
python3 client/start_sploit.py ./your_sploit.py \
  --server-url http://127.0.0.1:5000 \
  --token "$FARM_API_TOKEN"
```

Use the real farm-server address instead of `127.0.0.1` on participant
computers. Keep the Receiver team token only on the farm-server host; clients
send flags to the farm server and do not need the ForcAD token.
