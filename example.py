#!/usr/bin/env python3
"""Look up a few part numbers. Needs part_translations.json (see README.md)."""
from brick_translator import Translator

translator = Translator.load()
print(translator.info)

# Rebrickable part upn0342 as a BrickLink part number
print(translator.translate_part("upn0342", "Rebrickable", "BrickLink"))
# BrickLink 3001 on BrickOwl
print(translator.translate_part("3001", "BrickLink", "BrickOwl"))
# every known ID of Rebrickable part 3001
print(translator.part_ids("3001"))
# Rebrickable color 0 (black) on BrickLink
print(translator.translate_color(0, "Rebrickable", "BrickLink"))
