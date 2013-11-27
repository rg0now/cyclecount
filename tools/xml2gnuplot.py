#!/usr/bin/env python
"""
XML to gnuplot data and command file

Written by Andras Majdan
License: GNU General Public License Version 3
"""

import sys, os
import xml.etree.ElementTree

if len(sys.argv) != 4:
	print 'Usage: ' + sys.argv[0] + ' <source xml> <plot data> <plot cmd>'
	exit(1)

xmlfile = sys.argv[1]
plotdata = sys.argv[2]
plotcmd = sys.argv[3]

if not os.path.exists(xmlfile):
	print 'Cannot find XML file: ' + xmlfile
	exit(1)
	
tree = xml.etree.ElementTree.parse(xmlfile)
root = tree.getroot()

if root.tag == 'group':
	group = True
else:
	group = False
	
ywritten = False
num=0

with open(plotdata, 'w') as hdata, open(plotcmd, 'w') as hcmd:
	hcmd.write("set boxwidth 0.5\n")
	hcmd.write("set style fill solid\n")
	hcmd.write('set yrange [0:*]\n');
	hcmd.write('set title "' + root.attrib['name'] + '"\n')
	for child in root:
		if (child.tag == 'single') and group:
			for child2 in child:
				if child2.tag == 'interval':
					ivname = child2.attrib['name']
					for child3 in child2:
						if child3.tag == 'result':
							if child3.attrib['type'] == 'median':
								if not ywritten:
									hcmd.write('set ylabel "' + child3.attrib['name'] + '"\n')
									ywritten = True
								towrite = str(num) + ' "' + child.attrib['name'] + ' - ' + child2.attrib['value'] + ' ' + ivname + '" ' + child3.text + "\n"
								num += 1
								hdata.write(towrite)
						else:
							print "ERROR: Malformed XML\n"
							exit(1)
				else:
					if child2.tag == 'result':
						if child2.attrib['type'] == 'median':
							if not ywritten:
								hcmd.write('set ylabel "' + child2.attrib['name'] + '"\n')
								ywritten = True
							towrite = str(num) + ' "' + child.attrib['name'] + '" ' + child2.text + "\n"
							num += 1
							hdata.write(towrite)
					else:
						print "ERROR: Malformed XML\n"
						exit(1)
		else:
			if (child.tag == 'interval') and not group:
				ivname = child.attrib['name']
				for child2 in child:
					if child2.tag == 'result':
						if child2.attrib['type'] == 'median':
							if not ywritten:
								hcmd.write('set ylabel "' + child2.attrib['name'] + '"\n')
								hcmd.write('set xlabel "' + ivname + '"\n')
								ywritten = True
							towrite = str(num) + ' "' + child.attrib['value'] + '" ' + child2.text + "\n"
							num += 1
							hdata.write(towrite)
					else:
						print "ERROR: Malformed XML\n"
						exit(1)					
			else:
				if (child.tag == 'result') and not group:
					if child.attrib['type'] == 'median':
						if not ywritten:
							hcmd.write('set ylabel "' + child.attrib['name'] + '"\n')
							ywritten = True
						towrite = '0 0 ' + child.text + "\n"
						hdata.write(towrite)
				else:
					print "ERROR: Malformed XML\n"
					exit(1)
	hcmd.write("set terminal pngcairo size 800,600 enhanced font 'Verdana,10'\n")
	hcmd.write('set output "plot.png"\n');
	hcmd.write('plot "plot.dat" using 1:3:xtic(2) with boxes\n')
	hcmd.write("set terminal postscript eps enhanced color font 'Helvetica,10'\n")
	hcmd.write("set output 'plot.eps'\n")
	hcmd.write('plot "plot.dat" using 1:3:xtic(2) with boxes\n')
				
			
