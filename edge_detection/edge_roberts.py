#!/usr/bin/env python2

#    edge_roberts.py - performs roberts edge detection on specified files
#
#    Copyright (C) 2005  Rob Lass
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys
import math
import os
from PIL import Image, ImageFilter

# global variables
threshold = 100


def detect(file):
    # open input file
    in_file = Image.open(file).convert('L')
    in_file.filter(ImageFilter.SMOOTH)
    in_file.filter(ImageFilter.SHARPEN)

    # create object for edge image file
    edge_file = Image.new('RGBA', in_file.size)

    # create object for overlay image file
    overlay_file = Image.open(file).convert('L').convert('RGBA')

    # loop through all pixels, perform convolution
    for x in range(in_file.size[0]-1):
        for y in range(in_file.size[1]-1):
            # compute partial derivative wrt x
            Mx = 0
            if x < in_file.size[0]-1 and y < in_file.size[0]-1:
                Mx = in_file.getpixel((x, y)) - in_file.getpixel((x+1, y+1))
            else:
                Mx = in_file.getpixel((x, y))

            # compute partial derivative wrt y
            My = 0
            if x < in_file.size[0]-1 and y < in_file.size[0]-1:
                My = in_file.getpixel((x, y+1)) - in_file.getpixel((x+1, y))
            elif x >= in_file.size[0]-1:
                My = in_file.getpixel((x, y+1))
            elif y >= in_file.size[0]-1:
                My = in_file.getpixel((x+1, y))

            # compute the magnitude at this point
            mag = math.sqrt(Mx*Mx + My*My)

            if mag > threshold:
                overlay_file.putpixel((x, y), (int(mag), 0, 0))
                edge_file.putpixel((x, y), (0, int(mag), 0))

    # create dir if it doesn't exist, and save file
    pwd = os.listdir(".")
    if "output_images" not in pwd:
        os.mkdir("output_images")
    edge_file.save("output_images/"+os.path.splitext(file)[0]+"_roberts.png")


# print usage
if len(sys.argv) == 1:
    print "Usage: python [-t threshold]", sys.argv[0], " filename(s)"
    sys.exit()

for file in sys.argv[1:]:
    detect(file)
