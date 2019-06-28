#!/usr/bin/python
# coding: utf8
# Controller to execute fbx2.c process
# Framebuffer-copy-to-two-SPI-screens
# P20 C.Arias

import subprocess
import os
class Controller:
	def __init__(self):
		self.process = 0
		print("D")
		
	def open_OLED(self):
	
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
		self.process = subprocess.Popen(["sudo","./fbx2"])
		return 		
	
		
	def close_OLED(self):
		os.system("sudo killall fbx2")
		print("OLED est fermé")
		return 
	
	
	


