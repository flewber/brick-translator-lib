#!/usr/bin/env python3
import json

# Part number prefix definitions
REBRICKABLE_PFX = "RB_"
BRICKLINK_PFX = "BL_"
BRICKOWL_PFX = "BO_"
BRICKSET_PFX = "BS_"
LEGO_PFX = "LG_"

REBRICKABLE_SUPPORTED_TRANSLATIONS = [
    ("Rebrickable", REBRICKABLE_PFX),
    ("BrickLink",   BRICKLINK_PFX),
    ("BrickOwl",    BRICKOWL_PFX),
    ("BrickSet",    BRICKSET_PFX),
    ("LEGO",        LEGO_PFX),
]

translation_filename = "part_translations.json"  # File name

try:
    with open(translation_filename, 'r') as f:
        translation_dict = json.load(f)
except:
    print("%s not found. Need to create using get-translations.py" % translation_filename)

def tranlate_from_to(key,input_site,output_site):
    input_translation = False
    output_translation = False
    for translation in REBRICKABLE_SUPPORTED_TRANSLATIONS:
        if(translation[0] == input_site):
            input_translation = translation
        elif(translation[0] == output_site):
            output_translation = translation
    if(not (input_translation and output_translation)):
        print("invalid site name")
        return False
    key_with_prefix = input_translation[1] + key
    try:
        other_part_nums = translation_dict[key_with_prefix]
        ret_list = []
        for part_num in other_part_nums:
            if(part_num[:len(output_translation[1])] == output_translation[1]):
                ret_list.append(part_num[len(output_translation[1]):])
        return ret_list
    except:
        return False
    
def tranlate_from_rebrickable(key):
    with_prefix = REBRICKABLE_PFX + key
    try:
        return translation_dict[with_prefix]
    except:
        return False

def tranlate_from_bricklink(key):
    with_prefix = BRICKLINK_PFX + key
    try:
        return translation_dict[with_prefix]
    except:
        return False

def tranlate_from_brickowl(key):
    with_prefix = BRICKOWL_PFX + key
    try:
        return translation_dict[with_prefix]
    except:
        return False

def tranlate_from_brickset(key):
    with_prefix = BRICKSET_PFX + key
    try:
        return translation_dict[with_prefix]
    except:
        return False

def tranlate_from_lego(key):
    with_prefix = LEGO_PFX + key
    try:
        return translation_dict[with_prefix]
    except:
        return False