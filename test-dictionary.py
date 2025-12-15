#!/usr/bin/env python3
from translate_lib import *

# translate the rebrickable part number 01501 into a Bricklink part number
print(tranlate_from_to('upn0342',"Rebrickable","BrickLink"))

print(tranlate_from_rebrickable('01501'))
print(tranlate_from_bricklink('41708stk01'))
print(tranlate_from_brickowl('1111785'))
print(tranlate_from_brickset('3001'))
print(tranlate_from_lego('1501'))
