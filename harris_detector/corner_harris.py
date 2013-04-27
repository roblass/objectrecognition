#!/usr/bin/python2.3

#    corner_harris.py - implementation of the harris corner detection
#    algorithm
#
#    The method I use to compute the eigenvalues in this program is explained
#    here:
#       http://www.selu.edu/Academics/Depts/Math/students/george3/george.htm


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

import sys
import os
from PIL import Image
from RobMask import RobMask
from math import sqrt, fabs

threshold = 2000000000


def computeMatrix(image, x, y, x_grad, y_grad, C):
    """returns variable 'C' """
    # upper left
    C[0][0] = C[0][0] + x_grad.getpixel((x, y))**2
    C[0][1] = C[0][1] + x_grad.getpixel((x, y))*y_grad.getpixel((x, y))
    C[1][0] = C[1][0] + x_grad.getpixel((x, y))*y_grad.getpixel((x, y))
    C[1][1] = C[1][1] + y_grad.getpixel((x, y))**2

    return C


def computeGradients(image):
    """returns (x,y) where x and y are gradients in their respective
    directions"""

    # use prewitt to compute gradients
    m = RobMask("prewitt.coe", 0)
    x_grad, y_grad = m.getXPD(image), m.getYPD(image)

    good_pixels = []
    # for every point, window size = 3
    print "computing response"
    for x in range(1, image.size[0]-1):
        for y in range(1, image.size[1]-1):
            # compute C
            C = [[0, 0], [0, 0]]

            # first row
            C = computeMatrix(image, x-1, y-1, x_grad, y_grad, C)
            C = computeMatrix(image, x, y-1, x_grad, y_grad, C)
            C = computeMatrix(image, x+1, y-1, x_grad, y_grad, C)

            # second row
            C = computeMatrix(image, x-1, y, x_grad, y_grad, C)
            C = computeMatrix(image, x, y, x_grad, y_grad, C)
            C = computeMatrix(image, x+1, y, x_grad, y_grad, C)

            #third row
            C = computeMatrix(image, x-1, y+1, x_grad, y_grad, C)
            C = computeMatrix(image, x, y+1, x_grad, y_grad, C)
            C = computeMatrix(image, x+1, y+1, x_grad, y_grad, C)

            # compute lambda for this matrix.
            t = C[0][0]
            a = C[0][1]
            b = C[1][0]
            c = C[1][1]

            # make sure we have a rational root
            if t*t - 2*c*t + c*c - 4*a*b > 0:
                # see reference at the top for explanation of this
                l_1 = (t + c - sqrt(t*t - 2*c*t + c*c - 4*a*b))/2
                l_2 = (t + c + sqrt(t*t - 2*c*t + c*c - 4*a*b))/2

                k = 0.06
                R = l_1 * l_2 - k * (l_1 + l_2)**2
                if R > threshold:
                    if l_1 < l_2:
                        l_2 = l_1
                    good_pixels.append((R, x, y))

    return good_pixels


def computeGradient(image, u, v):
    """computes gradient.  acceptable values for u and v are 0 and 1."""

    # new image to hold gradient
    gradient = Image.new('L', image.size)

    #compute gradient using standard formula
    for x in range(image.size[0]-1):
        for y in range(image.size[1]-1):
            gradient.putpixel((x, y), (image.getpixel((x+u, y+v)) -
                              image.getpixel((x, y)))**2)


def harrisDetector(filename):
    """Runs a Harris edge detector on the specified file and returns a list of
    points it thinks are corners"""

    image = Image.open(filename).convert('L')

    response = computeGradients(image)

    # remove adjacent pixels

    # write corners to image
    output = Image.new('RGBA', image.size)
    for pixels in response:
        output.putpixel((pixels[1], pixels[2]), (255, 0, 0))

    #make output dir if it doesn't exist
    pwd = os.listdir(".")
    if "output_images" not in pwd:
        os.mkdir("output_images")

    # save
    output.save("output_images/"+os.path.splitext(filename)[0]+"_harris.png")

# print usage
if len(sys.argv) < 2:
    print "Usage: python ", sys.argv[0], " filename(s)"

# run on each input file
for argv in sys.argv[1:]:
    harrisDetector(argv)
