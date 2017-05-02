#!/usr/bin/env python

import argparse

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", type=str,
                        help="name of input file")

    args = parser.parse_args()

    removeroots(args)

def removeroots(args):
	print args.o
	fail = open(args.o,'r').read()


	sentences = fail.split("\n\n")
	sentencesout =  []
	for s in sentences:
		root = 0
		changed = False
		lines = s.split("\n")
		linesout = []
		for l in lines:
			symbols = l.split("\t")
			if len(symbols) > 8:
				if symbols[7] == "root" or symbols[7] == "ROOT":
					if root == 0:
						root = symbols[0]
					else:
						print "double root", root, symbols[0]
						symbols[6] = root
						symbols[7] = "nmod"
						#print "\t".join(symbols)
						changed = True
			linesout.append("\t".join(symbols))
		sentencesout.append("\n".join(linesout))
		if changed:
			print "\n".join(linesout).split("\n")[0]
			pass

	totalout =  "\n\n".join(sentencesout)
	failout = open(args.o+"_no2root", 'w')
	failout.write(totalout)
	failout.close()
main()
