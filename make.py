#!/usr/bin/env python
"""
Making cyclecount

Written by Andras Majdan
License: GNU General Public License Version 3
"""

import sys, subprocess, tempfile, os, sys, shutil

# Functions

def is_kmod_inserted():
	try:
		output = subprocess.check_output('lsmod | grep MSRdrv', shell=True)
		print 'Kernel module was inserted'
		return True
	except subprocess.CalledProcessError:
		print 'Kernel module was not inserted'
		return False
		
def is_kmod_exists():
	if os.path.exists('kerneldrv/MSRdrv.ko'):
		return True
	else:
		return False
		
def build_kmod():
	ret = subprocess.call(['make', '-C', 'kerneldrv'])
	if ret:
		print 'ERROR: Failed to build kernel module'
		exit(1)
	else:
		print 'Kernel module has been built'
	
def insert_kmod():
	print 'Trying to insert MSRdrv.ko..'
	ret = subprocess.call(['sudo', './install.sh'], cwd='kerneldrv')
	if ret:
		print 'ERROR: Failed to insert kernel module'
		exit(1)
	else:
		print 'Kernel module has been inserted'

def get_macros_from_header(testuserdata):
	ret = {}
	defs = {}
	ivs = {}
	with open(testuserdata, 'r') as handle:
		for line in handle:
			if line.startswith('#define '):
				words = line.split()
				if len(words) > 1:
					if len(words) > 2:
						defs[words[1]] = ' '.join(words[2::])
					else:
						defs[words[1]] = ''
				else:
					print 'Invalid macro: ' + line
			if line.startswith('#interval '):
				line = line.rstrip()
				words = line.split()
				if len(words) > 4:
					if words[2].isdigit() and words[3].isdigit():
						ivs[words[1]] = {
							'start': int(words[2]),
							'end' : int(words[3]),
							'name': ' '.join(words[4::]) }
					else:
						print 'Invalid macro: ' + line
				else:
					print 'Invalid macro: ' + line
	
	ret['define'] = defs
	ret['interval'] = ivs
		
	return ret

def copy_and_parse_header(src, dst, testname, loop_count, 
	ivid=None, i=None, ivname=None):
	
	global_defs = ""
	with open(dst, 'w') as hout, open(src, 'r') as hin:
		for line in hin:
			if line.startswith('#interval'):
				if ivid:
					hout.write('#define ' + ivid + ' ' + str(i) + "\n")
					hout.write('#define INTERVAL_VALUE ' + str(i) + "\n")
					hout.write('#define INTERVAL_NAME ' + ivname + "\n")
				else:
					print 'ERROR: unexpected #interval'
					exit(1)
			else:
				if line.startswith('#define '):
					tokens = line.rstrip('\n').split(' ')
					if len(tokens) > 2:
						global_defs += ' -D' + tokens[1] + '=' + tokens[2]
					else:
						global_defs += ' -D' + tokens[1]
				hout.write(line)
				
		names = testname.split('/')
		if len(names) > 1:
			hout.write('#define TEST_GROUP "' + names[0] + '"\n');
			hout.write('#define TEST_NAME "' + names[1] + '"\n');
		else:
			hout.write('#define TEST_NAME "' + testname + '"\n');
		return global_defs
		
def do_cmd(cmd):
	sys.stdout.write(".")
	sys.stdout.flush()
	try:
		output = subprocess.check_output(cmd, shell=True)
		return True
	except subprocess.CalledProcessError:
		print 'Compilation error'
		return False

def make_singletests(testname, testdir, testuserdata, tmpdir, 
		incdirs, srcfiles, libfiles, ofiles,
		loop_count, ivid, ivstart, ivend, ivname):
	cmd = 'g++ -g -O2 -D__STDC_LIMIT_MACROS -lpthread -I "' + testdir + '" -I "kerneldrv" -I "bench" "bench/PMCTestA.cpp" "bench/PMCTestB.cpp" "bench/quickselect.c"' 
	
	if incdirs:
		for dire in incdirs:
			cmd += ' -I "' + dire + '"'
	
	if libfiles:
		for libe in libfiles:
			if '/' in libe:
				sres = libe.rsplit('/', 1);
				cmd += ' -L' + sres[0] + ' -l' + sres[1] 
			else:	
				cmd += ' -l' + libe
	
	if ofiles:
		for ofilee in ofiles:
			cmd += ' "' + ofilee + '"'
	
	if srcfiles:
		for srcfilee in srcfiles:
			cmd += ' "' + srcfilee + '"'
	
	ret = 0
	
	sys.stdout.write("Building ")
	sys.stdout.flush()
	
	if ivid:
		for i in range(ivstart, ivend+1):
			tmpdiri = tmpdir + '/' + str(i)
			if not os.path.exists(tmpdiri):
				os.makedirs(tmpdiri)
			
			testuserdatai = tmpdiri + '/test-userdata.h'
			global_defs = copy_and_parse_header(testuserdata, testuserdatai, testname,
				loop_count, ivid, i, ivname)
			ncmd = cmd + global_defs + ' -D' + ivid + '=' + str(i) + ' -I "' + tmpdiri + '" -o "' + tmpdiri + '/testcode"'
			ret += do_cmd(ncmd)
	else:
		testuserdatai = tmpdir + '/test-userdata.h'
		global_defs = copy_and_parse_header(testuserdata, testuserdatai, testname, 
			loop_count)
		ncmd = cmd + global_defs + ' -I "' + tmpdir + '" -o "' + tmpdir + '/testcode"'
		ret += do_cmd(ncmd)
		
	print("")
	return ret
	

def build_singletest(testdir, testname):
	print 'Building ' + testname + '..'
	
	runfile = testdir + '/RUN'
	if os.path.exists(runfile):
		print 'Starting test defined tasks..'
		with open(runfile, 'r') as handle:
			for line in handle:
				if line.strip():
					if not line.startswith('#'):
						line = line.rstrip()
						ret = subprocess.call(line.split())
						if ret:
							print 'ERROR: a test defined task failed'
							exit(1)
	
	incdirs = []
	incfile = testdir + '/INCLUDE'
	if os.path.exists(incfile):
		print 'Including test defined includes..'
		with open(incfile, 'r') as handle:
			for line in handle:
				if line.strip():
					if not line.startswith('#'):
						incdirs.append(line.rstrip())
						
	srcfiles = []
	srcfile = testdir + '/SOURCE'
	if os.path.exists(srcfile):
		print 'Appending test defined sources..'
		with open(srcfile, 'r') as handle:
			for line in handle:
				if line.strip():
					if not line.startswith('#'):
						srcfiles.append(line.rstrip())
						
	libfiles = []
	ofiles = []
	linkfile = testdir + '/LINK'
	if os.path.exists(linkfile):
		print 'Appending test defined libraries..'
		with open(linkfile, 'r') as handle:
			for line in handle:
				if line.strip():
					if not line.startswith('#'):
						line = line.rstrip()
						if line.endswith('.o'):
							ofiles.append(line)
						else:
							libfiles.append(line)
	
	tmpdir = 'tmp/' + testdir
	if not os.path.exists(tmpdir):
		os.makedirs(tmpdir)
	testuserdata = testdir + '/test-userdata.hdef'
	macros = get_macros_from_header(testuserdata)
	intval = macros['interval']
	defval = macros['define']

	ivid = None
	ivstart = None
	ivend = None
	ivname = None

	if len(intval) > 1:
		print 'Only 1 interval macro is accepted per test'
		print 'ERROR: Could not build single test ' + testname
		return 1
	else:
		for key, val in intval.items():
			ivid = key
			ivstart = val['start']
			ivend = val['end']
			ivname = val['name']
			
	loop_count = 1
	if 'LOOP_COUNT' in defval:
		tmp = defval['LOOP_COUNT']
		if tmp.isdigit():
			loop_count = int(tmp)
		else:
			print 'Invalid LOOP_COUNT, default will be used (1)'
	
	ret = make_singletests(testname, testdir, testuserdata,
		tmpdir, incdirs, srcfiles, libfiles, ofiles,
		loop_count, ivid, ivstart, ivend, ivname)
	
	return ret
	
def build_grouptest(testdir, testname, groupdirs):
	print 'Building group ' + testname + '..'
	ret = 0
	for dire in groupdirs:
		ret += build_singletest(dire, testname + '/' + dire.split('/')[-1])
	return ret

		
def build_test(testname):
	err_code = 0
	testdir = 'tests/' + testname 
	testuserdata = testdir + '/test-userdata.hdef'
	if not os.path.exists(testuserdata):
		groupdirs = []
		for dire in os.listdir(testdir):
			dircand = testdir + '/' + dire
			if not os.path.isdir(dircand):
				print dircand + ' is not a directory'
				print 'ERROR: Could not build group test' + testname
				return 1
			groupdirs.append(dircand)
		if not groupdirs:
				print testdir + ' contains no directory'
				print 'ERROR: Could not build group test ' + testname
				return 1
		err_code += build_grouptest(testdir, testname, groupdirs)
	else:
		err_code += build_singletest(testdir, testname)
	
	return err_code

# Program starts here

err_code = 0

if not is_kmod_inserted():
	if not is_kmod_exists():
		build_kmod()
	insert_kmod()

if len(sys.argv) <= 1:
	for dire in os.listdir('tests'):
		if os.path.isdir('tests/' + dire):
			err_code += build_test(dire)
else:
	for arg in sys.argv[1::]:
		if os.path.isdir('tests/' + arg):
			err_code += build_test(arg)
		else:
			print 'ERROR: Cannot find ' + arg
		
exit(err_code)
