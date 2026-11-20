import os


FORCAD_URL = os.environ.get('FORCAD_URL', 'http://10.183.2.10').rstrip('/')
FORCAD_TEAM_TOKEN = os.environ.get('FORCAD_TEAM_TOKEN', '')
FARM_API_TOKEN = os.environ.get('FARM_API_TOKEN', '')
FARM_SERVER_PASSWORD = os.environ.get('FARM_SERVER_PASSWORD', '')

if not FORCAD_TEAM_TOKEN:
    raise RuntimeError('Set FORCAD_TEAM_TOKEN before starting the farm server')
if not FARM_SERVER_PASSWORD:
    raise RuntimeError('Set FARM_SERVER_PASSWORD before starting the farm server')
if not FARM_API_TOKEN:
    raise RuntimeError('Set FARM_API_TOKEN before starting the farm server')

CONFIG = {
    # During the preparation stage, test only against the official NPC service.
    # After organizers publish the target list, replace this mapping with the
    # authorized opponents' service addresses. Do not put your own vulnbox here.
    'TEAMS': {
        'NPC': '10.149.88.2',
    },
    'FLAG_FORMAT': r'[A-Z0-9]{31}=',

    # ForcAD HTTP Receiver. The team token is read from the local environment
    # and must never be committed to this repository.
    'SYSTEM_PROTOCOL': 'forcad_http',
    'SYSTEM_URL': os.environ.get(
        'FORCAD_FLAGS_URL',
        FORCAD_URL + '/flags'
    ),
    'SYSTEM_TOKEN': FORCAD_TEAM_TOKEN,

    # The competition receiver allows up to 100 flags per request.
    # 100 flags every second is below the 200 flags/sec refill rate.
    'SUBMIT_FLAG_LIMIT': 100,
    'SUBMIT_PERIOD': 1,
    'FLAG_LIFETIME': 5 * 60,

    # Required local secrets; never commit their values.
    'SERVER_PASSWORD': FARM_SERVER_PASSWORD,
    'ENABLE_API_AUTH': True,
    'API_TOKEN': FARM_API_TOKEN,
}
