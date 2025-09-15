#!/usr/bin/env python3
# coding: utf-8

import subprocess
import time
#from slides import gerenciar_slideshow_cinnamon

while True:
	time.sleep(2)
	subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh' ,shell=True)
	#time.sleep(1)
	#subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/slides.py' ,shell=True)
	#gerenciar_slideshow_cinnamon()


# Chamada Unica:
#subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh' ,shell=True)
#subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/slides.py' ,shell=True)
