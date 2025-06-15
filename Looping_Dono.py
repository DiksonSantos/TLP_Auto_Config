#!/usr/bin/env python3
# coding: utf-8

import subprocess
import time


while True:
	time.sleep(4)
	subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh' ,shell=True)


# Um Ciclo só
#subprocess.call('python3 /home/dikson/Linux_Helper/TLP_Power_Management/SUDO_CPU_2key.sh' ,shell=True)
