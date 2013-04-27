#!/sw/bin/python

#    RobMask.py - Module for performing convolution
#    Copyright (C) 2005  Rob Lass
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 2.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import string
import math
from math import fabs
from PIL import Image


class RobMask:
    xmask = []
    ymask = []
    threshold = 100

    def __init__(self, filename, threshold):
        "Takes the name of a file specifying coefficients"

        self.threshold = threshold

        # read the file, and store coefficients in mask
        f = open(filename, 'r')
        line = f.readline()
        while line != '':
            numbers = string.split(line)
            for i in range(len(numbers)):
                numbers[i] = int(numbers[i])
            self.xmask.append(string.split(line))
            line = f.readline()
        f.close()

        # verify that the mask is valid
        if len(self.xmask) != 3:
            raise "Invalid coefficient input file ", filename
        for row in self.xmask:
            if len(row) != 3:
                raise "Invalid coefficient input file ", filename

        # make the y-mask the inverse of the x-mask
        for i in range(len(self.xmask)):
            row = []
            for j in range(len(self.xmask)):
                row.append(self.xmask[j][i])
            self.ymask.append(row)

    def getXPD(self, source):
        """compute p.d. with respect to x"""
        gradient = Image.new('L', source.size)

        print "computing x p.d."

        for x in range(1, source.size[0]-1):
            for y in range(1, source.size[1]-1):
                Mx = int(self.xmask[0][2]) * source.getpixel((x+1, y-1))
                Mx = Mx + int(self.xmask[1][2]) * source.getpixel((x+1, y))
                Mx = Mx + int(self.xmask[2][2]) * source.getpixel((x+1, y+1))
                Mx = Mx + int(self.xmask[0][0]) * source.getpixel((x-1, y-1))
                Mx = Mx + int(self.xmask[1][0]) * source.getpixel((x-1, y))
                Mx = Mx + int(self.xmask[2][0]) * source.getpixel((x-1, y+1))

                gradient.putpixel((x, y), fabs(Mx))

        return gradient

    def getYPD(self, source):
        """compute p.d. with respect to y"""
        gradient = Image.new('L', source.size)

        print "computing y p.d."

        for x in range(1, source.size[0]-1):
            for y in range(1, source.size[1]-1):
                My = int(self.ymask[2][0]) * source.getpixel((x-1, y+1))
                My = My + int(self.ymask[2][1]) * source.getpixel((x, y+1))
                My = My + int(self.ymask[2][2]) * source.getpixel((x+1, y+1))
                My = My + int(self.ymask[0][0]) * source.getpixel((x-1, y-1))
                My = My + int(self.ymask[0][1]) * source.getpixel((x, y-1))
                My = My + int(self.ymask[0][2]) * source.getpixel((x+1, y-1))

                gradient.putpixel((x, y), fabs(My))

        return gradient

    def apply(self, mask, source):
        "Applies the given mask to the source image, and returns edge image"

        edge_file = Image.new('RGBA', source.size)

        #convolution
        for x in range(1, source.size[0]-1):
            for y in range(1, source.size[1]-1):
                 # compute p.d. with respect to x
                Mx = int(self.xmask[0][2]) * source.getpixel((x+1, y-1))
                Mx = Mx + int(self.xmask[1][2]) * source.getpixel((x+1, y))
                Mx = Mx + int(self.xmask[2][2]) * source.getpixel((x+1, y+1))
                Mx = Mx + int(self.xmask[0][0]) * source.getpixel((x-1, y-1))
                Mx = Mx + int(self.xmask[1][0]) * source.getpixel((x-1, y))
                Mx = Mx + int(self.xmask[2][0]) * source.getpixel((x-1, y+1))

                # compute p.d. with respect to y
                My = int(self.ymask[2][0]) * source.getpixel((x-1, y+1))
                My = My + int(self.ymask[2][1]) * source.getpixel((x, y+1))
                My = My + int(self.ymask[2][2]) * source.getpixel((x+1, y+1))
                My = My + int(self.ymask[0][0]) * source.getpixel((x-1, y-1))
                My = My + int(self.ymask[0][1]) * source.getpixel((x, y-1))
                My = My + int(self.ymask[0][2]) * source.getpixel((x+1, y-1))

                mag = math.sqrt(Mx*Mx + My*My)

                if mag > self.threshold:
                    edge_file.putpixel((x, y), (0, int(mag), 0))
        return edge_file
