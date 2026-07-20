# -*- coding: utf-8 -*-
"""
Lightweight client for the public ICAMA pesticide registration query system.

Endpoint and field names are those used by the site's own search form
(https://www.icama.cn/BasicdataSystem/pesticideRegistration/queryselect.do).
The site renders results as a server-side HTML table (id="tab"); there is
no JSON API, so we parse the returned HTML with lxml.

NOTE: This is an unofficial integration against a third-party government
site. If ICAMA changes their page structure or field names, only this file
should need to be updated - the Odoo models call the functions below and
don't know about HTML/form details.
"""

import logging
import re
import time

import requests
from lxml import html as lxml_html

_logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.icama.cn/BasicdataSystem/pesticideRegistration/queryselect.do"
DETAIL_URL = "https://www.icama.cn/BasicdataSystem/pesticideRegistration/viewpd.do"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Headers for the initial "warm-up" GET, used only to obtain a JSESSIONID
# cookie - the site requires a valid session before it will answer the
# search POST (confirmed from a captured browser request).
GET_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Headers for the actual search POST.
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.icama.cn",
    "Referer": SEARCH_URL,
}

# All fields accepted by the site's search form. We always send the full
# set (blank for anything not used) since that's what the form itself does.
BASE_PAYLOAD = {
    "pageNo": 1,
    "pageSize": 100,
    "djzh": "",     # registration certificate no.
    "nymc": "",     # pesticide name
    "cjmc": "",     # manufacturer / registrant name
    "sf": "",
    "nylb": "",     # pesticide category
    "zhl": "",      # total content
    "jx": "",       # dosage form
    "zwmc": "",     # crop name
    "fzdx": "",     # target pest
    "syff": "",     # method of use
    "dx": "",       # toxicity
    "yxcf": "", "yxcf_en": "", "yxcfhl": "",
    "yxcf2": "", "yxcf2_en": "", "yxcf2hl": "",
    "yxcf3": "", "yxcf3_en": "", "yxcf3hl": "",
    "yxqs_start": "", "yxqs_end": "",
    "yxjz_start": "", "yxjz_end": "",
    "accOrfuzzy": 2,  # 1 = exact match, 2 = fuzzy/partial match
}

# Maps the Chinese column headers shown on the results table to the
# field names we store on pesticide.registration. Parsing by header text
# (rather than fixed column positions) makes this resilient to the site
# adding/reordering columns.
#
# NOTE: "有效成分" (active ingredient) below is a best-effort guess at
# the results table's column header, added alongside the new search
# parameter but not verified against a live response. Since parsing
# only pulls in headers that actually match a row in the fetched table,
# a wrong guess just means active_ingredient stays blank (harmless) -
# if that happens, check the actual header text in a search result page
# and update the key here.
HEADER_MAP = {
    "登记证号": "registration_no",
    "农药名称": "name",
    "农药类别": "category",
    "剂型": "dosage_form",
    "总含量": "total_content",
    "有效期至": "valid_until",
    "登记证持有人": "holder",
    "有效成分": "active_ingredient",
}

ONCLICK_ID_RE = re.compile(r"'([^']+)'")


class ICAMAClientError(Exception):
    pass


def new_session(timeout=20):
    """
    Create a requests.Session and visit the search page once so the
    server issues a JSESSIONID cookie. The search POST endpoint requires
    a valid session cookie to return real results.
    """
    session = requests.Session()
    try:
        session.get(SEARCH_URL, headers=GET_HEADERS, timeout=timeout)
    except requests.RequestException as exc:
        raise ICAMAClientError(
            "Failed to establish ICAMA session: %s" % exc
        ) from exc
    return session


def _parse_results_page(html_text):
    """Parse one results page. Returns list of dicts (see HEADER_MAP values)."""
    tree = lxml_html.fromstring(html_text)
    tables = tree.xpath('//table[@id="tab"]')
    if not tables:
        return []
    table = tables[0]
    rows = table.xpath(".//tr")
    if len(rows) < 2:
        return []

    header_cells = rows[0].xpath(".//td|.//th")
    headers = [c.text_content().strip() for c in header_cells]

    records = []
    for row in rows[1:]:
        cells = row.xpath("./td")
        if not cells:
            continue
        values = [c.text_content().strip() for c in cells]
        raw = dict(zip(headers, values))

        record = {}
        for cn_header, field in HEADER_MAP.items():
            if cn_header in raw:
                record[field] = raw[cn_header]

        # Grab the internal id used for the detail page (viewpd.do), if any
        detail_ref = None
        links = row.xpath(".//a[@onclick]")
        if links:
            match = ONCLICK_ID_RE.search(links[0].get("onclick", ""))
            if match:
                detail_ref = match.group(1)
        record["detail_ref"] = detail_ref

        # Skip fully-empty rows (e.g. "no data" placeholder rows)
        if any(record.get(f) for f in HEADER_MAP.values()):
            records.append(record)

    return records


def search(
    name="",
    category="",
    dosage_form="",
    registration_no="",
    holder="",
    active_ingredient="",
    fuzzy=True,
    page_size=200,
    max_pages=50,
    timeout=20,
    delay_between_pages=0.5,
    session=None,
):
    """
    Query ICAMA for pesticide registration records.

    :param name: pesticide name (农药名称)
    :param category: pesticide category (农药类别)
    :param dosage_form: dosage form (剂型)
    :param registration_no: registration certificate no. (登记证号)
    :param holder: registration holder / manufacturer name (登记证持有人)
    :param active_ingredient: active ingredient (有效成分). The site's
        form supports up to 3 active ingredients (yxcf/yxcf2/yxcf3);
        only the first slot is used here since a single-ingredient
        search covers the vast majority of lookups.
    :param fuzzy: partial/fuzzy match (True) vs exact match (False)
    :param page_size: rows requested per page
    :param max_pages: safety cap on number of pages fetched
    :param timeout: per-request timeout in seconds
    :param delay_between_pages: politeness delay between paginated requests
    :param session: optional requests.Session, already warmed up via
        new_session(). If not provided, a fresh session is created and
        used for just this call.
    :return: list of dicts with keys: registration_no, name, category,
             dosage_form, total_content, valid_until, holder,
             active_ingredient, detail_ref
    """
    http = session or new_session(timeout=timeout)

    payload = dict(BASE_PAYLOAD)
    payload["djzh"] = registration_no or ""
    payload["nymc"] = name or ""
    payload["nylb"] = category or ""
    payload["jx"] = dosage_form or ""
    payload["cjmc"] = holder or ""
    payload["yxcf"] = active_ingredient or ""
    payload["accOrfuzzy"] = 2 if fuzzy else 1
    payload["pageSize"] = page_size

    all_records = []
    page = 1
    while page <= max_pages:
        payload["pageNo"] = page
        try:
            response = http.post(
                SEARCH_URL,
                data=payload,
                headers=DEFAULT_HEADERS,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ICAMAClientError(
                "Failed to reach ICAMA (page %s): %s" % (page, exc)
            ) from exc

        page_records = _parse_results_page(response.text)
        if not page_records:
            break

        all_records.extend(page_records)

        if len(page_records) < page_size:
            # Last page reached
            break

        page += 1
        if delay_between_pages:
            time.sleep(delay_between_pages)

    return all_records


def fetch_detail(detail_ref, timeout=20, session=None):
    """
    Fetch the detail page for a single registration record.
    Returns the raw HTML text; parsing is left to the caller since the
    detail page layout varies more than the list view.
    """
    if not detail_ref:
        return None
    http = session or requests
    try:
        response = http.post(
            DETAIL_URL,
            params={"id": detail_ref, "r": time.time()},
            headers=DEFAULT_HEADERS,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ICAMAClientError(
            "Failed to fetch ICAMA detail for %s: %s" % (detail_ref, exc)
        ) from exc
    return response.text
