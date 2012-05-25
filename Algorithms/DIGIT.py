# -*- coding: utf-8 -*-
from math import *

DIGIT = [] # initialize 16-bit DIGIT for bitwise manipulation
for i in range(0,16):
    DIGIT.append(int(pow(2,16) - pow(2,i) - 1))
    
DIGIT.reverse() # Comparison Bit Digit

# DIGIT:
# from
# 0b0111111111111111
# to
# 0b1111111111111110

REVERSE = 65535
# REVERSE = 0b1111111111111111

# RDIGIT:
# from
# 0b1000000000000000
# to
# 0b0000000000000001

RDIGIT = [REVERSE - i for i in DIGIT]