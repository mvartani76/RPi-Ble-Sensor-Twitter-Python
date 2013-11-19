#!/usr/bin/env python
import sys
from twython import Twython
import os
import time
import pexpect
import RPi.GPIO as GPIO

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t

# This algorithm borrowed from 
# http://processors.wiki.ti.com/index.php/SensorTag_User_Guide#Gatt_Server
# which most likely took it from the datasheet.  I've not checked it, other
# than noted that the temperature values I got seemed reasonable.
#
def calcTmpTarget(objT, ambT, gpvar7, localtime):
    m_tmpAmb = ambT/128.0
    Vobj2 = objT * 0.00000015625
    Tdie2 = m_tmpAmb + 273.15
    S0 = 6.4E-14            # Calibration factor
    a1 = 1.75E-3
    a2 = -1.678E-5
    b0 = -2.94E-5
    b1 = -5.7E-7
    b2 = 4.63E-9
    c2 = 13.4
    Tref = 298.15
    S = S0*(1+a1*(Tdie2 - Tref)+a2*pow((Tdie2 - Tref),2))
    Vos = b0 + b1*(Tdie2 - Tref) + b2*pow((Tdie2 - Tref),2)
    fObj = (Vobj2 - Vos) + c2*pow((Vobj2 - Vos),2)
    tObj = pow(pow(Tdie2,4) + (fObj/S),.25)
    tObj = (tObj - 273.15)
    print "%.2f C" % tObj
    if (gpvar7 == 1):
    	api.update_status(status='Temp is '+str(round(tObj,2))+' C at time: '+str(localtime))

CONSUMER_KEY = 'V953Z63QVRV29g5k8AEvig'
CONSUMER_SECRET = 'pMdEj4upojdJPUW6X4GgiifYEYcFuXUW4IBXcQWFz0'
ACCESS_KEY = '2197297674-xTXUt8e6g0x7bkJhOqcwvT5cB3XbQwDvAc8g78N'
ACCESS_SECRET = 'Ba5RcDq2BMsYt89Bo4iESlj9o9sfX1WdWSvjiDj9S5bSr'

api = Twython(CONSUMER_KEY,CONSUMER_SECRET,ACCESS_KEY,ACCESS_SECRET) 

GPIO.setmode(GPIO.BOARD)

# set up GPIOs 7 as input
GPIO.setup(7,GPIO.IN)

bluetooth_adr = sys.argv[1]
tool = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
tool.expect('\[LE\]>')
print "Preparing to connect. You might need to press the side button..."
tool.sendline('connect')
# test for success of connect
#tool.expect('\[CON\].*>')
tool.sendline('char-write-cmd 0x29 01')
tool.expect('\[LE\]>')
while True:
    time.sleep(1)
    tool.sendline('char-read-hnd 0x25')
    tool.expect('descriptor: .*') 
    rval = tool.after.split()
    objT = floatfromhex(rval[2] + rval[1])
    ambT = floatfromhex(rval[4] + rval[3])
    #print rval
    gpvar7 = GPIO.input(7)
    localtime = time.asctime( time.localtime(time.time()))
    calcTmpTarget(objT, ambT, gpvar7, localtime)


GPIO.cleanup()	
