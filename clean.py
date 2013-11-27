#!/usr/bin/env python
"""
Cleaning cyclecount

Written by Andras Majdan
License: GNU General Public License Version 3
"""

import subprocess, os, sys

# Functions

def is_kmod_inserted():
	try:
		output = subprocess.check_output('lsmod | grep MSRdrv', shell=True)
		return True
	except subprocess.CalledProcessError:
		return False
		
def remove_kmod():
	print 'Trying to remove MSRdrv..'
	ret = subprocess.call(['sudo', './uninstall.sh'], cwd='kerneldrv')
	if ret:
		print 'ERROR: Failed to remove kernel module'
		return 1
	else:
		print 'Kernel module has been removed'
		return 0
	

def is_kmod_exists():
	if os.path.exists('kerneldrv/MSRdrv.ko'):
		return True
	else:
		return False
		
def clean_kmod():
	ret = subprocess.call(['make', '-C', 'kerneldrv', 'clean'])
	if ret:
		print 'ERROR: Failed to clean kernel module'
		return 1
	else:
		print 'Kernel module is clean'
		return 0


def clean_singletest(testdir, testname):
	print 'Cleaning ' + testname + '..'
	
	cleanfile = testdir + '/CLEAN'
	if os.path.exists(cleanfile):
		print 'Starting test defined clean tasks..'
		with open(cleanfile, 'r') as handle:
			for line in handle:
				if not line.startswith('#'):
					if len(line) > 0:
						line = line.rstrip()
						ret = subprocess.call(line.split(), cwd=testdir)
						if ret:
							print 'ERROR: a test defined task failed'
							exit(1)
	
	return 0
	
def clean_grouptest(testdir, testname, groupdirs):
	print 'Cleaning group ' + testname + '..'
	ret = 0
	for dire in groupdirs:
		ret += clean_singletest(dire, testname + '/' + dire.split('/')[-1])
	return ret

def clean_test(testname):
	err_code = 0
	testdir = 'tests/' + testname 
	testuserdata = testdir + '/test-userdata.hdef'
	if not os.path.exists(testuserdata):
		groupdirs = []
		for dire in os.listdir(testdir):
			dircand = testdir + '/' + dire
			if not os.path.isdir(dircand):
				print dircand + ' is not a directory'
				print 'ERROR: Could not clean group test' + testname
				return 1
			groupdirs.append(dircand)
		if not groupdirs:
				print testdir + ' contains no directory'
				print 'ERROR: Could not clean group test ' + testname
				return 1
		err_code += clean_grouptest(testdir, testname, groupdirs)
	else:
		err_code += clean_singletest(testdir, testname)
	
	return err_code

# Program starts here

err_code = 0

if is_kmod_exists():
	err_code += clean_kmod()
	
if is_kmod_inserted():
	err_code += remove_kmod()
	
subprocess.call(['rm', '-rf', 'tmp'])
subprocess.call(['rm', '-rf', 'results'])

if len(sys.argv) <= 1:
	for dire in os.listdir('tests'):
		if os.path.isdir('tests/' + dire):
			err_code += clean_test(dire)
else:
	for arg in sys.argv[1::]:
		err_code += clean_test(arg)
		
exit(err_code)
