#!/usr/bin/env python
"""
Running cyclecount

Written by Andras Majdan
License: GNU General Public License Version 3
"""

import subprocess, os, sys, shutil
import xml.etree.cElementTree as ET
import xml.dom.minidom

# Functions

def is_kmod_inserted():
	try:
		output = subprocess.check_output('lsmod | grep MSRdrv', shell=True)
		print 'Kernel module was inserted'
		return True
	except subprocess.CalledProcessError:
		print 'Kernel module was not inserted'
		return False

def do_run(cmd, pnode):
	try:
		output = subprocess.check_output(cmd, shell=True)
		for line in output.splitlines():
			if line.startswith('result cycles median '):
				cnode = ET.SubElement(pnode, 'result')
				cnode.set('name', 'cycles')
				cnode.set('type', 'median')
				cnode.text = line.split()[-1]
			else:
				if line.startswith('result cycles '):
					cnode = ET.SubElement(pnode, 'result')
					cnode.set('id', line.split()[-2])
					cnode.set('name', 'cycles')
					cnode.set('type', 'normal')
					cnode.text = line.split()[-1]
				else:
					if line.startswith('test interval name '):
						pnode.set('name', line[19::])
		return 0
	except subprocess.CalledProcessError:
		print 'Called process error'
		return 1

def run_singletest(testname, pnode):
	sys.stdout.write("Running " + testname + " ")
	sys.stdout.flush()
	
	testpath = 'tmp/tests/' + testname;
	testcode = testpath + '/testcode'
	
	if not os.path.exists(testpath):
		print 'ERROR: Cannot run ' + testname
		return 1
	
	if os.path.exists(testcode):
		ret = do_run(testcode, pnode)
		if ret:
			print 'ERROR: Runtime error while running ' + testcode
			return 1
	else:
		for dire in os.listdir(testpath):
			sys.stdout.write(".")
			sys.stdout.flush()
			cnode = ET.SubElement(pnode, 'interval')
			cnode.set('value', dire)
			testcode = testpath + '/' + dire + '/testcode'
			ret = do_run(testcode, cnode)
			if ret:
				print 'ERROR: Runtime error while running ' + testcode
				return 1
				
	print("")
	return 0
	
def run_grouptest(testname, groupdirs, root):
	print 'Entering group ' + testname + '..'
	ret = 0
	for dire in groupdirs:
		cnode = ET.SubElement(root, 'single')
		cnode.set('name', dire.split('/')[-1])
		ret += run_singletest(testname + '/' + dire.split('/')[-1], cnode)
	return ret

		
def run_test(testname):
	err_code = 0
	testdir = 'tests/' + testname 
	testuserdata = testdir + '/test-userdata.hdef'
	if not os.path.exists(testuserdata):
		groupdirs = []
		for dire in os.listdir(testdir):
			dircand = testdir + '/' + dire
			if not os.path.isdir(dircand):
				print dircand + ' is not a directory'
				print 'ERROR: Could not run group test' + testname
				return 1
			groupdirs.append(dircand)
		if not groupdirs:
				print testdir + ' contains no directory'
				print 'ERROR: Could not run group test ' + testname
				return 1
		root = ET.Element('group')
		root.set('name', testname)
		err_code += run_grouptest(testname, groupdirs, root)
	else:
		root = ET.Element('single')
		root.set('name', testname)
		err_code += run_singletest(testname, root)
		
	xmlout = xml.dom.minidom.parseString(
		xml.etree.ElementTree.tostring(root)) 
		
	xmlfin = xmlout.toprettyxml()
	
	resultdir = 'results/' + testname
	if not os.path.exists(resultdir):
		os.makedirs(resultdir)
		
	with open(resultdir + '/result.xml', 'w') as hout:
		hout.write(xmlfin)
		
	subprocess.call(['tools/xml2gnuplot.py', resultdir + '/result.xml',
		resultdir + '/plot.dat', resultdir + '/plot.cmd'])

	ret = subprocess.call(['gnuplot', 'plot.cmd'], cwd=resultdir)
	if ret:
		print 'Warning: cannot run gnuplot'
	
	return err_code

# Program starts here

err_code = 0

if not is_kmod_inserted():
	print 'ERROR: Kernel module was not loaded'
	exit(1)
	
if len(sys.argv) <= 1:
	for dire in os.listdir('tests'):
		if os.path.isdir('tests/' + dire):
			err_code += run_test(dire)
else:
	for arg in sys.argv[1::]:
		if os.path.isdir('tests/' + arg):
			err_code += run_test(arg)
		else:
			print 'ERROR: Cannot find ' + arg
		
exit(err_code)
