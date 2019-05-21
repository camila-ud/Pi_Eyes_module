#!/usr/bin/python
# coding: utf8
# Controller to execute fbx2.c process
# Framebuffer-copy-to-two-SPI-screens
# P20 C.Arias

from getpass import getpass
import subprocess
import os

def open_OLED():
	global process
	#if we want get password
	#-----------------------------------
	#try:
		#password = getpass("Insert sudo password: ")
	#except Exception as error:
		#print('error', password,error)
	#else:
		#sudo -S in order to take input from stdin
		#process = Popen("sudo -S ./fbx2".split(),stdin=PIPE,stderr=PIPE)
		#process.communicate(password.encode())
	#----------------------------------------		
	process = subprocess.Popen(["sudo","./fbx2"])		
	pass
		
def close_OLED():
	global process
	os.system("sudo killall fbx2")
	print("OLED est fermé")
	
	
	


