"""Contract between the official go-e key table and the integration.

Source of truth: `contract/api_keys.json`, generated from the official key table (see
`contract/generate_api_keys.py` for the commit it comes from). The tests check three things:

1. Every documented key is either mapped to a `Tag` or listed in `contract/classification.json`
   (unsupported keys are documented there with a group, decision "open").
2. Every key the code uses that the official table does not list is explained in the same file.
3. Read/write flag and category of every mapped key match the documentation. Known differences are
   listed in `contract/deviations.json`; their tests carry the marker `needs_decision` (they fail on
   purpose, but are not blocking until someone has decided whether the difference is intended or the
   documentation has a gap). A NEW difference has no marker and is blocking.
"""
import json
import re
from pathlib import Path

import pytest

from custom_components.goecharger_api2 import const as entity_const
from custom_components.goecharger_api2.pygoecharger_ha import const as bridge_const
from custom_components.goecharger_api2.pygoecharger_ha.keys import CAT, Tag

CONTRACT = Path(__file__).parent / "contract"
DOC = json.loads((CONTRACT / "api_keys.json").read_text())["keys"]
CLASSIFICATION = json.loads((CONTRACT / "classification.json").read_text())
DEVIATIONS = json.loads((CONTRACT / "deviations.json").read_text())["deviations"]

TAGS = {tag.key: tag for tag in Tag}
CARD_KEY = re.compile(r"c\d[nei]")
CATEGORY = {"Config": CAT.CONFIG, "Status": CAT.STATUS, "Constant": CAT.CONSTANT, "Other": CAT.OTHER}


def _filter_keys():
    keys = set()
    for name in dir(bridge_const):
        value = getattr(bridge_const, name)
        if name.startswith("FILTER_") and isinstance(value, str):
            keys |= {k for k in re.split(r"[,\s]+", re.sub(r"\{.*?\}", "", value)) if k}
    return keys


def _entity_keys():
    return {d.key for name in dir(entity_const) if isinstance(getattr(entity_const, name), list)
            for d in getattr(entity_const, name) if hasattr(d, "key")}


FILTER_KEYS = _filter_keys()
CODE_KEYS = set(TAGS) | FILTER_KEYS | _entity_keys()


def _known(aspect):
    return {d["key"] for d in DEVIATIONS if d["aspect"] == aspect}


def _cases(aspect):
    known = _known(aspect)
    return [pytest.param(key, id=key, marks=[pytest.mark.needs_decision] if key in known else [])
            for key in sorted(set(DOC) & set(TAGS))]


# ----------------------------------------------------------------------------- documented keys

def test_every_documented_key_is_supported_or_classified():
    classified = set(CLASSIFICATION["handled_outside_tag"]) | set(CLASSIFICATION["not_supported"])
    unclassified = sorted(set(DOC) - set(TAGS) - classified)
    assert unclassified == [], "new documented keys: map them to a Tag or add them to classification.json"


def test_classification_has_no_stale_entries():
    listed = set(CLASSIFICATION["handled_outside_tag"]) | set(CLASSIFICATION["not_supported"])
    stale = sorted(k for k in listed if k not in DOC or k in TAGS)
    assert stale == [], "supported or no longer documented: remove them from classification.json"


def test_card_keys_are_really_requested_through_the_card_filters():
    requested = {k for name in ("FILTER_CARDS_ID_FWV60", "FILTER_CARDS_ENGY_FWV60", "FILTER_CARDS_NAME_FWV60")
                 for k in getattr(bridge_const, name).split(",")}
    missing = sorted(k for k in CLASSIFICATION["handled_outside_tag"] if k not in requested)
    assert missing == []


# ----------------------------------------------------------------------------- keys used but not documented

def test_every_undocumented_key_used_by_the_code_is_explained():
    explained = set(CLASSIFICATION["undocumented_in_code"]) | set(CLASSIFICATION["handled_outside_tag"])
    unexplained = sorted(k for k in CODE_KEYS - set(DOC) if k not in explained)
    assert unexplained == [], "not in the official table: add them to classification.json with a reason"


def test_undocumented_classification_has_no_stale_entries():
    stale = sorted(k for k in CLASSIFICATION["undocumented_in_code"] if k in DOC or k not in CODE_KEYS)
    assert stale == [], "documented now, or no longer used: remove them from classification.json"


# ----------------------------------------------------------------------------- flags of mapped keys

@pytest.mark.parametrize("key", _cases("writeable"))
def test_write_flag_matches_documentation(key):
    documented = DOC[key]["rw"] in ("R/W", "W")
    assert TAGS[key].writeable is documented, f"documented {DOC[key]['rw']!r}, keys.py writeable={TAGS[key].writeable}"


@pytest.mark.parametrize("key", _cases("category"))
def test_category_matches_documentation(key):
    assert TAGS[key].cat == CATEGORY[DOC[key]["category"]], \
        f"documented {DOC[key]['category']!r}, keys.py {TAGS[key].cat.name}"


def test_deviation_list_has_no_stale_entries():
    stale = sorted(f"{d['key']}:{d['aspect']}" for d in DEVIATIONS if d["key"] not in TAGS or d["key"] not in DOC)
    assert stale == []
