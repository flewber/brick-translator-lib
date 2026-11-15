#!/usr/bin/env python3
"""Old interface, kept so existing scripts keep running. Deprecated.

New code: `from brick_translator import Translator` (see README.md).

Differences from the original module:
- A missing or damaged data file raises TranslationDataError on first
  use. It is no longer reported as "no translation found".
- An unknown site name raises UnknownSchemeError (a ValueError).
- Translating a part into its own scheme works.
- Brickset IDs are found (the original looked them up under a wrong
  name and never stored any).
An unknown part still returns False, as before.
"""
import warnings

from brick_translator import default_translator
from brick_translator.translator import LEGACY_PREFIXES, REBRICKABLE

REBRICKABLE_PFX = "RB_"
BRICKLINK_PFX = "BL_"
BRICKOWL_PFX = "BO_"
BRICKSET_PFX = "BS_"
LEGO_PFX = "LG_"

REBRICKABLE_SUPPORTED_TRANSLATIONS = [
    ("Rebrickable", REBRICKABLE_PFX),
    ("BrickLink", BRICKLINK_PFX),
    ("BrickOwl", BRICKOWL_PFX),
    ("BrickSet", BRICKSET_PFX),
    ("LEGO", LEGO_PFX),
]


def _deprecated(name):
    warnings.warn(f"translate_lib.{name} is deprecated; use brick_translator.Translator",
                  DeprecationWarning, stacklevel=3)


def tranlate_from_to(input_part_id, input_site, output_site):
    """List of IDs in output_site's scheme, or False if there are none."""
    _deprecated("tranlate_from_to")
    return default_translator().translate_part(input_part_id, input_site, output_site) or False


def _all_other_ids(key, scheme):
    """Every other known ID of the part, prefixed, or False if unknown."""
    translator = default_translator()
    rb_ids = translator.translate_part(key, scheme, REBRICKABLE)
    if not rb_ids:
        return False
    own = (scheme, str(key))
    out = []
    for rb_id in rb_ids:
        ids = {REBRICKABLE: [rb_id], **translator.part_ids(rb_id)}
        for prefix, other_scheme in LEGACY_PREFIXES.items():
            for other in ids.get(other_scheme, ()):
                if (other_scheme, other) != own and prefix + other not in out:
                    out.append(prefix + other)
    return out


def tranlate_from_rebrickable(key):
    _deprecated("tranlate_from_rebrickable")
    return _all_other_ids(key, "Rebrickable")


def tranlate_from_bricklink(key):
    _deprecated("tranlate_from_bricklink")
    return _all_other_ids(key, "BrickLink")


def tranlate_from_brickowl(key):
    _deprecated("tranlate_from_brickowl")
    return _all_other_ids(key, "BrickOwl")


def tranlate_from_brickset(key):
    _deprecated("tranlate_from_brickset")
    return _all_other_ids(key, "Brickset")


def tranlate_from_lego(key):
    _deprecated("tranlate_from_lego")
    return _all_other_ids(key, "LEGO")
