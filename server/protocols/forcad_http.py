from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import time

import requests

from server import app
from server.models import FlagStatus, SubmitResult
from server.flag_utils import deduplicate_flags


TIMEOUT = 10
MAX_BATCH_SIZE = 100
MAX_RATE_LIMIT_RETRIES = 5
DEFAULT_RETRY_AFTER = 1.0

REJECTED_MESSAGES = (
    'wrong flag',
    'flag is your own',
    'flag is too old',
    'your own',
    'too old',
    'invalid',
    'expired',
)


def classify_message(message):
    """Map a ForcAD per-flag msg to a farm status.

    The competition rules document the rejection messages. The legacy
    forcad_tcp adapter recognizes "accepted"/"congrat" as positive verdicts.
    Unknown verdicts stay QUEUED rather than being counted as accepted.
    """
    normalized = str(message or '').strip().lower()

    # Check negative verdicts first: e.g. "not accepted" must never become
    # ACCEPTED just because it contains the word "accepted".
    if any(phrase in normalized for phrase in REJECTED_MESSAGES):
        return FlagStatus.REJECTED

    if 'not accepted' in normalized or 'not congrat' in normalized:
        return FlagStatus.QUEUED

    if 'accepted' in normalized or 'congrat' in normalized:
        return FlagStatus.ACCEPTED

    return FlagStatus.QUEUED


def parse_retry_after(value):
    """Parse Retry-After as seconds or an HTTP date."""
    if value is None:
        return DEFAULT_RETRY_AFTER

    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        pass

    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_RETRY_AFTER


def _submit_batch(flags, config):
    url = config.get('SYSTEM_URL')
    token = config.get('SYSTEM_TOKEN')
    if not url:
        raise ValueError('SYSTEM_URL is not configured')
    if not token:
        raise ValueError('SYSTEM_TOKEN is empty; set FORCAD_TEAM_TOKEN locally')

    headers = {
        'X-Team-Token': token,
        'Content-Type': 'application/json',
    }
    payload = [item.flag for item in flags]

    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        response = requests.put(url, headers=headers, json=payload, timeout=TIMEOUT)

        if response.status_code == 429:
            if attempt >= MAX_RATE_LIMIT_RETRIES:
                raise RuntimeError(
                    'ForcAD Receiver returned HTTP 429 after {} retries'.format(
                        MAX_RATE_LIMIT_RETRIES
                    )
                )

            delay = parse_retry_after(response.headers.get('Retry-After'))
            app.logger.warning(
                'ForcAD rate limit reached; retrying in %.2f seconds', delay
            )
            time.sleep(delay)
            continue

        response.raise_for_status()
        body = response.json()

        if not isinstance(body, list):
            raise ValueError('ForcAD response must be a JSON array')
        if len(body) != len(flags):
            raise ValueError(
                'ForcAD returned {} results for {} submitted flags'.format(
                    len(body), len(flags)
                )
            )

        results = []
        for index, (flag_item, result_item) in enumerate(zip(flags, body)):
            if not isinstance(result_item, dict):
                raise ValueError('ForcAD result #{} is not an object'.format(index))
            if result_item.get('flag') != flag_item.flag:
                raise ValueError(
                    'ForcAD response order/content mismatch at result #{}'.format(index)
                )
            if 'msg' not in result_item:
                raise ValueError('ForcAD result #{} has no msg field'.format(index))

            message = str(result_item['msg']).strip()
            status = classify_message(message)
            results.append(SubmitResult(flag_item.flag, status, message))

        return results

    raise RuntimeError('ForcAD submission retry loop ended unexpectedly')


def submit_flags(flags, config):
    """Submit unique flags to ForcAD using PUT /flags in batches of <= 100."""
    unique_flags, duplicates_removed = deduplicate_flags(
        list(flags), lambda item: item.flag
    )
    if duplicates_removed:
        app.logger.warning(
            'Removed %s duplicate flags before ForcAD submission',
            duplicates_removed
        )

    for offset in range(0, len(unique_flags), MAX_BATCH_SIZE):
        batch = unique_flags[offset:offset + MAX_BATCH_SIZE]
        try:
            results = _submit_batch(batch, config)
        except Exception as error:
            app.logger.exception('Failed to submit a ForcAD flag batch')
            message = '{}: {}'.format(type(error).__name__, str(error))
            for item in batch:
                yield SubmitResult(item.flag, FlagStatus.QUEUED, message)

            # Do not continue sending later batches after a failed batch. They
            # remain queued and will be retried in a later farm-server cycle.
            for item in unique_flags[offset + MAX_BATCH_SIZE:]:
                yield SubmitResult(
                    item.flag,
                    FlagStatus.QUEUED,
                    'Not sent because the previous ForcAD batch failed'
                )
            return

        for result in results:
            if result.status == FlagStatus.QUEUED:
                app.logger.warning(
                    'Unknown ForcAD verdict for flag %s: %s',
                    result.flag,
                    result.checksystem_response
                )
            yield result
