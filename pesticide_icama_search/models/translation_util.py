# -*- coding: utf-8 -*-
"""
Small, dependency-light helpers for zh <-> en translation.

Layers, cheapest/most reliable first:

1. A static dictionary covering ICAMA's fixed regulatory vocabulary
   (pesticide category / dosage form - a closed set of ~25 official
   terms). Zero network calls, instant, and more accurate than machine
   translation for regulatory codes.
2. Lara Translate's API, one call for a whole BATCH of strings at once
   (all the names/holders on a results page, not one call per string)
   - used when Access Key ID/Secret are configured in Settings. Lara's
   REST API requires request signing that only their official SDK
   implements (it isn't a plain documented HTTP endpoint like Google/
   DeepL/OpenAI), so this uses the official `lara-sdk` package rather
   than hand-rolled HTTP calls - install it with `pip install
   lara-sdk` in the same Python environment Odoo runs in.
3. Google's public (unauthenticated, no key needed) translate endpoint,
   one string at a time, as a no-configuration fallback if no Lara
   credentials are set, the lara-sdk package isn't installed, or a
   batch call fails.

Either way, the caller (pesticide.translation.cache) persists every
result, so a given string is only ever sent to a translator once.
"""

import logging
import re
import time

import requests

_logger = logging.getLogger(__name__)

CJK_RE = re.compile(r"[\u4e00-\u9fff]")

GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"

try:
    from lara_sdk import Credentials as LaraCredentials
    from lara_sdk import Translator as LaraTranslator
    from lara_sdk import LaraApiError, LaraError

    LARA_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when the package isn't installed
    LaraCredentials = None
    LaraTranslator = None
    LaraApiError = Exception
    LaraError = Exception
    LARA_SDK_AVAILABLE = False

LARA_SDK_INSTALL_MESSAGE = (
    "The 'lara-sdk' Python package isn't installed on this Odoo server. "
    "Install it with: pip install lara-sdk (run it in the same Python "
    "environment Odoo uses), then restart Odoo."
)
# Lara's docs don't publish a hard cap on texts per call the way DeepL
# does - kept conservative and consistent with the other providers so
# one bad response never wastes a huge batch.
LARA_BATCH_SIZE = 50


def contains_chinese(text):
    return bool(text) and bool(CJK_RE.search(text))


def detect_lang(text):
    """Very cheap heuristic: any CJK character present -> Chinese."""
    return "zh" if contains_chinese(text) else "en"


# Fixed ICAMA vocabulary - 农药类别 (category) and 剂型 (dosage form).
# These are official regulatory terms, not free text, so a static
# mapping is both faster and more reliable than machine translation.
# Extend this as new terms are encountered (e.g. from a failed lookup
# logged as a warning).
_ZH_EN = {
    # Categories (农药类别)
    "除草剂": "Herbicide",
    "杀虫剂": "Insecticide",
    "杀菌剂": "Fungicide",
    "杀鼠剂": "Rodenticide",
    "杀螨剂": "Acaricide",
    "杀线虫剂": "Nematicide",
    "植物生长调节剂": "Plant Growth Regulator",
    "软体动物杀灭剂": "Molluscicide",
    "杀软体动物剂": "Molluscicide",
    "熏蒸剂": "Fumigant",
    # Dosage forms (剂型)
    "悬浮剂": "Suspension Concentrate (SC)",
    "乳油": "Emulsifiable Concentrate (EC)",
    "可湿性粉剂": "Wettable Powder (WP)",
    "颗粒剂": "Granule (GR)",
    "水剂": "Aqueous Solution (SL)",
    "水分散粒剂": "Water Dispersible Granule (WG)",
    "可溶液剂": "Soluble Concentrate (SL)",
    "可溶粉剂": "Soluble Powder (SP)",
    "油悬浮剂": "Oil-based Suspension Concentrate (OD)",
    "水乳剂": "Emulsion, Oil in Water (EW)",
    "微乳剂": "Microemulsion (ME)",
    "悬乳剂": "Suspo-emulsion (SE)",
    "超低容量液剂": "Ultra-low Volume Liquid (UL)",
    "烟剂": "Smoke Generator (FU)",
    "片剂": "Tablet (TB)",
    "粉剂": "Dustable Powder (DP)",
    "种子处理干粉剂": "Powder for Dry Seed Treatment (DS)",
    "种子处理液剂": "Solution for Seed Treatment (LS)",
}
_EN_ZH = {v: k for k, v in _ZH_EN.items()}
# Allow matching English input without the trailing "(XX)" code and
# case-insensitively, since a user typing a search term won't type the
# abbreviation exactly (e.g. "wettable powder" instead of
# "Wettable Powder (WP)").
_EN_ZH_LOOSE = {
    re.sub(r"\s*\([^)]*\)\s*$", "", v).strip().lower(): k for v, k in _EN_ZH.items()
}


def static_lookup(text, source_lang, target_lang):
    """Instant, offline lookup against the known regulatory vocabulary.
    Returns None (not a failure - just "not in the static list") if the
    text isn't one of the fixed terms above."""
    if not text:
        return None
    if source_lang == "zh" and target_lang == "en":
        return _ZH_EN.get(text)
    if source_lang == "en" and target_lang == "zh":
        return _EN_ZH.get(text) or _EN_ZH_LOOSE.get(text.strip().lower())
    return None


def google_translate_single(text, source_lang, target_lang, timeout=8):
    """
    Single HTTP call to Google's public translate endpoint - the same
    unauthenticated one browser extensions use. No API key, no SDK.
    Used as the fallback when no Lara credentials are configured, the
    lara-sdk package isn't installed, or a Lara batch call fails.
    """
    if not text:
        return None
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": text,
    }
    try:
        resp = requests.get(GOOGLE_TRANSLATE_URL, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return "".join(chunk[0] for chunk in data[0] if chunk and chunk[0])
    except Exception as exc:  # noqa: BLE001
        _logger.warning("Google translation failed for %r: %s", text, exc)
        return None


def lara_translate_batch(
    texts,
    source_lang,
    target_lang,
    access_key_id,
    access_key_secret,
    timeout=30,
    errors=None,
    max_retries=2,
):
    """
    Translate a whole list of strings in ONE Lara Translate API call,
    instead of one call per string. Returns a list of translations in
    the same order as `texts`, or None if the call fails (caller
    should fall back to Google in that case). If `errors` (a list) is
    passed, the human-readable failure reason - including Lara's own
    error message, not just a generic exception string - is appended
    to it so the caller can surface it (e.g. in strict/"Require Lara"
    mode) instead of only ever logging a warning.

    HTTP 429/5xx-flavored Lara API errors are retried with a short
    backoff; auth failures, missing dependency, and malformed
    responses fail immediately since retrying won't help.
    """
    texts = list(texts)
    if not texts or not access_key_id or not access_key_secret:
        return None

    if not LARA_SDK_AVAILABLE:
        _logger.warning(LARA_SDK_INSTALL_MESSAGE)
        if errors is not None:
            errors.append(LARA_SDK_INSTALL_MESSAGE)
        return None

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            credentials = LaraCredentials(access_key_id, access_key_secret)
            client = LaraTranslator(credentials)
            result = client.translate(texts, source=source_lang, target=target_lang)
            translation = result.translation
            if isinstance(translation, list) and len(translation) == len(texts):
                return [(t or "").strip() for t in translation]
            if isinstance(translation, str) and len(texts) == 1:
                return [translation.strip()]
            last_error = (
                "Lara returned an unexpected response shape for %d "
                "texts: %r" % (len(texts), translation)
            )
            break  # a parse/shape failure won't be fixed by retrying
        except LaraApiError as exc:
            status = getattr(exc, "status_code", None)
            etype = getattr(exc, "type", "") or ""
            msg = getattr(exc, "message", None) or str(exc)
            last_error = "Lara API error [%s%s]: %s" % (
                status,
                (" %s" % etype) if etype else "",
                msg,
            )
            if status in (429, 500, 502, 503, 504) and attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except LaraError as exc:  # noqa: BLE001 - SDK-level (connection, etc.)
            last_error = "Lara SDK error: %s" % exc
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            break
        except Exception as exc:  # noqa: BLE001
            last_error = "Unexpected error calling Lara: %s" % exc
            break

    _logger.warning(
        "Lara translation failed for a batch of %d texts: %s",
        len(texts),
        last_error,
    )
    if errors is not None:
        errors.append(last_error)
    return None


def test_lara_connection(access_key_id, access_key_secret, timeout=15):
    """
    Send one trivial translation request and return (ok, message) with
    a human-readable diagnosis. Used by the Settings "Test Connection"
    button so a failure shows the ACTUAL reason (missing package, bad
    credentials, quota...) instead of only ever silently falling back
    to Google and leaving you guessing.
    """
    if not access_key_id or not access_key_secret:
        return False, "Both Access Key ID and Access Key Secret are required."
    if not LARA_SDK_AVAILABLE:
        return False, LARA_SDK_INSTALL_MESSAGE

    errors = []
    result = lara_translate_batch(
        ["你好"],
        "zh",
        "en",
        access_key_id,
        access_key_secret,
        timeout=timeout,
        errors=errors,
        max_retries=0,
    )
    if result:
        return True, "Success - Lara replied: %r" % result[0]
    return False, (
        errors[-1] if errors else "Lara translation failed for an unknown reason."
    )
