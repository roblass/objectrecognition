#!/usr/bin/env python2

#    recognize.py - finds roads that are so-called "ill-structured"
#
#    The algorithms used in this program are based on the algorithms described
#    in the paper "Grouping Dominant Orientations for Ill-Structured Road
#    Following" written by Christopher Rasmussen at the University of
#    Delaware.  The paper appeared in Proc. Computer Vision and Pattern
#    Recognition, 2004. 
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

import sys, math, os,random
from PIL import Image, ImageFilter
from math import fabs

# variables that we need throughout the program
gamma, k = 0,0

# computes the part of g_hat that is common to both even and odd
def gCommonCalculation(x, y, theta, sigma):
	a = x * math.cos(theta) + y * math.sin(theta)
	b = -x * math.sin(theta) + y * math.cos(theta)
	first_term = -(1.0/8.0*(sigma**2.0))
	second_term = 4.0*(a**2.0) + (b**2.0)
	return math.exp(first_term * second_term)

# performs odd specific g_hat calculations
def gHatOdd(x, y, theta, sigma,gamma):
	a = x * math.cos(theta) + y * math.sin(theta)
	return math.sin(2.0*math.pi*a/gamma)*gCommonCalculation(x,y,theta,sigma)

# performs even specific g_hat calculations
def gHatEven(x, y, theta, sigma,gamma):
	a = x * math.cos(theta) + y * math.sin(theta)
	return math.cos(2.0*math.pi*a/gamma)*gCommonCalculation(x,y,theta,sigma)

# kernel is assumed to be kxk
def normalize(kernel,k):
	smallest = kernel[0][0]
	biggest = kernel[0][0]
	for x in range(k):
		for y in range(k):
			if kernel[x][y] < smallest:
				smallest = kernel[x][y]
			if kernel[x][y] > biggest:
				biggest = kernel[x][y]
	for x in range(k):
		for y in range(k):
			kernel[x][y] = (kernel[x][y] - smallest) / (biggest - smallest)
	return kernel

# produces even and odd kernels for the given orientation
def generateKernels(theta,sigma,k,gamma):
	odd,even = [],[]
	total_odd, total_even = 0,0

	# generate kernel hat
	for x_hat in range(k):
		odd.append([])
		even.append([])
		for y_hat in range(k):
			x = (x_hat) - (k/2)
			y = (y_hat) - (k/2)
			odd[x_hat].append(gHatOdd(x,y,theta,sigma,gamma))
			even[x_hat].append(gHatEven(x,y,theta,sigma,gamma))
			total_odd = odd[x_hat][y_hat]
			total_even = even[x_hat][y_hat]
	mu_odd = total_odd / (k**2)
	mu_even = total_even / (k**2)

	# subtract the mean
	for x in range(k):
		for y in range(x):
			odd[x][y] = odd[x][y] - mu_odd
	

	# normalize the resulting kernels
	odd = normalize(odd,k)
	even = normalize(even,k)
	return even, odd

# runs all three parts of the algorithm
def detect(file):
	# open input file
	in_file = Image.open(file).convert('L')
	
	# create an output file for showing voting results
	out_file = Image.new('RGBA', in_file.size)

	#############################
	# generate Gabor kernels 	#
	#############################

	# first compute some of the variables that are constant throughout
	width, height = out_file.size

	# the paper calls this variable "lambda", but that is a reserved word in
	# python, and gamma looks like and upside down L, so i decided to use it
	gamma = 2.0**(math.floor((math.log(width,2.0)))-5.0)

	orientations = 72

	# k should be odd, since it makes calculations easier
	k = int((10.0*gamma)/(math.pi*4))
	if k%2==0:
		k = k + 1
	sigma = (k/9.0)

	# loop through all the pixels that make sense
	even_kernels = {}
	odd_kernels = {}
	# create kernels for n different orientations
	for theta in map(lambda a: math.radians(a*(180/orientations)),range(orientations)):
		even, odd = generateKernels(theta,sigma,k,gamma)
		even_kernels[theta] = even
		odd_kernels[theta] = odd

	###############################################
	# COMPUTE DOMINANT ORIENTATION FOR EACH PIXEL #
	###############################################

	# fill a kxk "matrix" with -1s
	subsample = 15
	angle_vote = []
	response = []

	for x in range(width):
		angle_vote.append([])
		response.append([])
		for y in range(height):
			angle_vote[x].append(-1)
			response[x].append(0)



	# loop through pixels in image
	for y_hat in filter(lambda x: x%subsample==0, range(k/2, height-k/2)):
		print "computing dominant orientation: ", (y_hat-k/2)/subsample+1, "of", (height-k)/subsample
		for x_hat in range(k/2, width-k/2):
			best = 0
			best_angle = -1
			# try every angle
			for theta in map(lambda a: math.radians(a*(180/orientations)),range(orientations)):

				total = 0
				# loop through elements in filter
				odd = odd_kernels[theta]
				even = even_kernels[theta]
				for x in range(k):
					for y in range(k):
						total += odd[x][y] * \
							in_file.getpixel(((x_hat-(k/2))+x,(y_hat-(k/2))+y))
						total += even[x][y] * \
							in_file.getpixel(((x_hat-(k/2))+x,(y_hat-(k/2))+y))
				if total>best:
					response[x_hat][y_hat] = total
					best = total
					best_angle = theta
			angle_vote[x_hat][y_hat] = best_angle


	#####################################
	# VOTE FOR THE DOMINANT ORIENTATION #
	#####################################
	
	#create the voting matrix
	votes = []
	for x in range(width):
		votes.append([])
		for y in range(height):
			votes[x].append(0)
			

	for x in range(width):
		print "voting, column", x+1, "of",  width
		# only get the y's that voted in the previous step
		for y in filter(lambda _y: angle_vote[x][_y]!=-1, range(height)):
			#vote on pixels in a specific row
			for top_y in range(min(y, int(0.75*height))):
				# obtuse
				if angle_vote[x][y]>(math.pi/2):
					start = (y-top_y) * math.tan((angle_vote[x][y]-math.pi/2)-(math.pi)/(orientations*2))
					stop = (y-top_y) * math.tan((angle_vote[x][y]-math.pi/2)+(math.pi)/(orientations*2))
					for vote_x in filter(lambda x: x<width and x>0, range(int(start)+x, int(stop)+x)):
						votes[vote_x][top_y] += 1
				else:
				#acute
					start = (y-top_y) * math.tan((math.pi/2-angle_vote[x][y])-(math.pi)/(orientations*2))
					stop = (y-top_y) * math.tan((math.pi/2-angle_vote[x][y])+(math.pi)/(orientations*2))
					for vote_x in filter(lambda x: x<width and x>0, range(int(start)-x, int(stop)+x)):
						votes[vote_x][top_y] += 1

	#determine the "winning" point
	print "determining winner, and saving output"
	max_clique = []
	max_votes = -1
	for x in range(width):
		for y in range(height):
			if votes[x][y] > max_votes:
				max_votes = votes[x][y]
				max_clique = [(x,y)]
			if votes[x][y] == max_votes:
				max_clique.append((x,y))
	print len(max_clique), "in clique, with a max of ", max_votes

	max_spot = (0,0)
	best_y = 0
	for spot in max_clique:
		max_spot = (max_spot[0]+spot[0], max_spot[1]+spot[1])
		if spot[1] > best_y:
			best_y = spot[1]
	print max_clique
	max_spot = (max_spot[0]/len(max_clique), best_y)
	print best_y

			

	# output a voting image
	voting_image = Image.open(file).convert('L')
	winner_image = Image.open(file)
	for x in range(width):
		for y in range(height):
			# show the range of votes
			voting_image.putpixel((x,y),64.0*(1.0*votes[x][y]/max_votes))
			# show the winning pixe l
			if fabs(x-max_spot[0])<5 and fabs(y-max_spot[1])<5:
				winner_image.putpixel((x,y),(255,0,0))
				
			


	# save this spot to out_file
	pwd = os.listdir(".")
	if "output" not in pwd:
		os.mkdir("output")

	print "saving output/" + file.split(".")[0] + ".votes.png"
	print "saving output/" + file.split(".")[0] + ".winner.png"
	voting_image.save("output/" + file.split(".")[0] + ".votes.png")
	winner_image.save("output/" + file.split(".")[0] + ".winner.png")
	

# print usage
if len(sys.argv)==1:
	print "Usage: python [-t threshold]", sys.argv[0], " filename(s)"
	sys.exit() # not really needed, but it is psychologically beneficial

# find the road in each file given as input
for file in sys.argv[1:]:
	detect(file)
