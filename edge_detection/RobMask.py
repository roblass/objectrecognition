#!/usr/bin/env python2

#    RobMask.py - Module for performing edge detection with an arbitrary 3x3
#    mask. (TODO: add convolution for arbitrarily sized mask)
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

import sys, os, string, math
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

		# verify that the mask is valid (ie: 3x3)
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
					edge_file.putpixel((x,y), (0, int(mag), 0))
		return edge_file


# main function
if __name__ == '__main__':
	
	if len(sys.argv)<=2:
		print "Usage: python ", sys.argv[0], " mask_file filename(s)"
		sys.exit() 

	for filename in sys.argv[2:]:
		mask = RobMask(sys.argv[1], 100)

		#apply the specified mask to this image
		image = mask.apply(mask, Image.open(filename).convert('L'))

		# create output directory if it doesn't exist
		pwd = os.listdir(".")
		if "output_images" not in pwd:
			os.mkdir("output_images")

		# save the image
		image.save("output_images/"+os.path.splitext(filename)[0]+'.'+sys.argv[1].split('.')[-2]+".png")

