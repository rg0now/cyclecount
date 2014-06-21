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

simple_one = False
group_one = False

datadict = {}

with open(plotdata, 'w') as hdata:
	title = root.attrib['name']
	for child in root:
		if (child.tag == 'single') and group:
			for child2 in child:
				if child2.tag == 'interval':
					try:
						xlabel
					except NameError:
						xlabel = child2.attrib['name']
					else:
						if xlabel != child2.attrib['name']:
							print "ERROR: Comparing apples to oranges"
							print xlabel + " instead of " + child2.attrib['name']
							exit(1)
					for child3 in child2:
						if child3.tag == 'result':
							if child3.attrib['type'] == 'median':
								try:
									ylabel
								except NameError:
									ylabel = child3.attrib['name']
								else:
									if ylabel != child3.attrib['name']:
										print "ERROR: Comparing apples to oranges"
										print ylabel + " instead of " + child3.attrib['name']
										exit(1)
								if child.attrib['name'] in datadict.keys():
									datadict[child.attrib['name']].update( { child2.attrib['value'] : child3.text } )
								else:
									datadict[child.attrib['name']] = {}
									datadict[child.attrib['name']].update( { child2.attrib['value'] : child3.text } )
						else:
							print "ERROR: Malformed XML\n"
							exit(1)
				else:
					group_one = True
					if child2.tag == 'result':
						if child2.attrib['type'] == 'median':
							try:
								ylabel
							except NameError:
								ylabel = child2.attrib['name']
							else:
								if ylabel != child2.attrib['name']:
									print "ERROR: Comparing apples to oranges"
									print ylabel + " instead of " + child2.attrib['name']
									exit(1)
							datadict[child.attrib['name']] = child2.text
					else:
						print "ERROR: Malformed XML\n"
						exit(1)
		else:
			if (child.tag == 'interval') and not group:
				try:
					xlabel
				except NameError:
					xlabel = child.attrib['name']
				else:
					if xlabel != child.attrib['name']:
						print "ERROR: Comparing apples to oranges"
						print xlabel + " instead of " + child.attrib['name']
						exit(1)
				for child2 in child:
					if child2.tag == 'result':
						if child2.attrib['type'] == 'median':
							try:
								ylabel
							except NameError:
								ylabel = child2.attrib['name']
							else:
								if ylabel != child2.attrib['name']:
									print "ERROR: Comparing apples to oranges"
									print ylabel + " instead of " + child2.attrib['name']
									exit(1)
							datadict[child.attrib['value']] = child2.text
					else:
						print "ERROR: Malformed XML\n"
						exit(1)					
			else:
				if (child.tag == 'result') and not group:
					if child.attrib['type'] == 'median':
						simple_one = True
						try:
							ylabel
						except NameError:
							ylabel = child.attrib['name']
						else:
							if ylabel != child.attrib['name']:
								print "ERROR: Comparing apples to oranges"
								print ylabel + " instead of " + child.attrib['name']
								exit(1)
						simple_one_text = child.text
				else:
					print "ERROR: Malformed XML\n"
					exit(1)

	newdict = {}
	key_num = 0
	val_curnum = 0
	val_maxnum = 0
	
	hdata.write('no')
	if not group:
		hdata.write("\t" + title)
	
	if simple_one:
		val_maxnum = 2
		key_num = 1
		hdata.write("\n")
		hdata.write("x " + simple_one_text + "\n")
		xlabel = ""
	elif group_one:
		val_maxnum = 0
		key_num = 1
		xlabel = ""
		hdata.write("\t" + title + "\n")
		if "nothing" in datadict:
			substractit = int(datadict["nothing"])
		else:
			substractit = 0
		for key1 in sorted(datadict.iterkeys()):
			if not key1 == "nothing":
				hdata.write(str(key1) + "\t" + str(int(datadict[key1])-substractit) + "\n")
				key_num += 1
	else:
		subtractit = {}
		for key1 in sorted(datadict.iterkeys()):
			if group:
				if not key1 == "nothing":
					val_curnum = 0
					key_num += 1
					hdata.write("\t" + key1)
					for key2 in sorted(datadict[key1].iterkeys(), key=int):
						if key2 not in newdict.keys():
							newdict[key2] = {}
						newdict[key2].update( { key1 : datadict[key1][key2] } )
						val_curnum += 1
						if val_curnum > val_maxnum:
							val_maxnum = val_curnum
				else:
					for key2 in sorted(datadict[key1].iterkeys(), key=int):
						subtractit[key2] = datadict[key1][key2]
			else:
				key_num = 1
				val_maxnum += 1
				newdict[key1] = datadict[key1]

		hdata.write("\n")

		for key1 in sorted(newdict.iterkeys(), key=int):
			hdata.write(str(key1))
			if group:
				for key2 in sorted(datadict.iterkeys()):
					if not key2 == "nothing":
						hdata.write("\t")
						if key2 not in newdict[key1].keys():
							hdata.write("-")
						else:
							if key1 in subtractit:
								hdata.write(str(int(newdict[key1][key2])-int(subtractit[key1])))
							else:
								hdata.write(str(newdict[key1][key2]))
			else:
				hdata.write("\t" + str(newdict[key1]))
			hdata.write("\n")
				
graph_width = 20 * val_maxnum * (key_num/2+1) + 200
graph_height = 500

with open(plotcmd, 'w') as hcmd:
	hcmd.write('set terminal pngcairo enhanced font "arial,10" fontscale 1.0 size ')
	hcmd.write(str(graph_width) + ', ' + str(graph_height) + "\n")
	hcmd.write("""set output 'plot.png'
set boxwidth 0.9 absolute
set style fill   solid 1.00 border lt -1
set key autotitle columnheader
set key invert reverse Left outside
set style histogram clustered gap 1 title  offset character 0, 0, 0
set datafile missing '-'
set yrange [0:*]
set style data histograms""" + "\n") 
	hcmd.write('set ylabel' + ' "' + ylabel + '"\n')
	if xlabel != "":
		hcmd.write('set xlabel' + ' "' + xlabel + '"\n')
	hcmd.write('set title' + ' "' + title + '"\n')
	if key_num < 2 or group_one:
		hcmd.write("set nokey\n")
		if group_one:
			hcmd.write("set xtics nomirror rotate by -90\n")
		hcmd.write("plot 'plot.dat' using 2:xtic(1)\n")
	else:
		hcmd.write("plot 'plot.dat' using 2:xtic(1), for [i=3:" + str(key_num+1) + "] '' using i\n")
		
	hcmd.write('set terminal postscript eps enhanced color font "arial,8"\n')
	hcmd.write("set output 'plot.eps'\n")
	hcmd.write("replot\n")
			
