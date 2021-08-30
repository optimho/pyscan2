'''
Simple Pyscan NFC / MiFare Classic Example
Copyright (c) 2019, Pycom Limited.

This example continuously sends a REQA for ISO14443A card type
If a card is discovered, it will read the UID
If DECODE_CARD = True, will attempt to authenticate with CARDkey
If authentication succeeds will attempt to read sectors from the card
'''

from array import array
from pycoproc_1 import Pycoproc
from MFRC630 import MFRC630
from LIS2HH12 import LIS2HH12
from LTR329ALS01 import LTR329ALS01
import time
import pycom
from network import LoRa
import socket
import ubinascii
from machine import SD 
import os

dataList=[]
value=[]
VALID_CARDS_SD =[]
intdata=[]

print('Lorawan example ')
print ('Use and ISO14443A type rfid card to swipe and send a message to the things network')
print ('Starting up.......')
print('')
print('')

# Initial data for cards
# add your card UID here
VALID_CARDS = [[0x43, 0x95, 0xDD, 0xF8],
               [0x43, 0x95, 0xDD, 0xF9],
               [0x46, 0x5A, 0xEB, 0x7D, 0x8A, 0x08, 0x04],
               [0x04, 0x34, 0x0B, 0xEA, 0xC2, 0x6F, 0x80],
               [0xEE, 0x87, 0x3F, 0x3F, 0x02]]

# This is the default key for an unencrypted MiFare card
CARDkey = [ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF ]
DECODE_CARD = False
newcard = [0xFF, 0xEF, 0xFF, 0xFF]   

def appendCard(fileName, card):
# /sd/cardDataStore.dat should be the default file name.
# This method adds a card to the card store  
    print ('Going to try write some data to the card')
    f = open('/sd/cardDataStore.dat', 'a')
    for items in VALID_CARDS:
        delimit=''
        #print(items)
        for values in card:
            f.write((delimit + str(values)))
            if delimit=="":
                delimit='#'
            #print(';', values)
    
        f.write('/n')
    f.close()
    VALID_CARDS_SD.append(card)
    #print ('List of cards ',VALID_CARDS_SD )

def connectSD():
    """Connect SD card"""
    try:
        sd=SD()
        #os.mount(sd, '/sd')
        print('Mount SD Card..')
    except OSError:
        print('There is a problem mounting the card - is there a card?')
    #print(os.listdir('/sd'))

def hasFile(fileName):
    """Check if a file exsists"""
    try:
        f = open(fileName,'r')
        f.close
        print ('File has been located..')
        return True
    except OSError:
        print('Cannot locate file...')
        return False


def writeToSD(fileName):
    """
    ##########################################        
    # Write data to file                     #
    ##########################################
    """
    print ('Going to try write some data to the card')
    f = open(fileName, 'w')
    for items in VALID_CARDS:
        delimit=''
        for values in items:
            f.write((delimit + str(values)))
            if delimit=="":
                delimit='#'
        f.write('/n')
    f.close()

def readFromSD(fileName):
    """
    #######################
    #Read data from a file#
    #######################
    """
    intdata=[]
    f = open(fileName,'r')
    print ('Going to try and read the data')
    data = f.read()
    f.close()
    dataList = data.split('/n')
    for items in dataList:
        if items !="":
            data=items.split('#')
            for theItems in data:
                try:
                    if theItems != []:
                        intdata.append((int(theItems)))
                except ValueError:
                    print('ValueError')
                    
            VALID_CARDS_SD.append(intdata)
            intdata=[]
    print('Successful read ..')

connectSD()
if hasFile('/sd/cardDataSt.dat')==False:
    writeToSD('/sd/cardDataStore.dat')
readFromSD('/sd/cardDataStore.dat')
#appendCard('/sd/cardDataStore.dat', newcard)
print (VALID_CARDS_SD)
#print (VALID_CARDS)

py = Pycoproc(Pycoproc.PYSCAN)
nfc = MFRC630(py)
lt = LTR329ALS01(py)
li = LIS2HH12(py)

# Initialise LoRa in LORAWAN mode.
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORAWAN, region=LoRa.AU915)

# create an OTAA authentication parameters, change them to the provided credentials
# API Key NNSXS.A6XD5D5KROX5JMM7FQVPVCYR7V5KDLUFU3OVCZI.MI4TADSSH7U2YMMO4QPJGIZIHPZCBKOPFLZIVOIXXWRW764MLILQ
app_eui = ubinascii.unhexlify('0000000000000FEF')
app_key = ubinascii.unhexlify('25ED83CF673AF5B7409FF63AA1B32EDB')
#uncomment to use LoRaWAN application provided dev_eui
dev_eui = ubinascii.unhexlify('70b3d549998aeda2')

# Uncomment for US915 / AU915 & Pygate
for i in range(0,8):
     lora.remove_channel(i)
for i in range(16,65):
     lora.remove_channel(i)
for i in range(66,72):
    lora.remove_channel(i)

# join a network using OTAA (Over the Air Activation)
#uncomment below to use LoRaWAN application provided dev_eui
if lora.nvram_restore():
    print ('has a saved version of lora OTAA')
else:
    print ('No saved lora connection')

#lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
lora.join(activation=LoRa.OTAA, auth=(dev_eui, app_eui, app_key), timeout=0)

# wait until the module has joined the network
while not lora.has_joined():
    time.sleep(10)
    print('Not yet joined...')
    if lora.has_joined():
        print ('Joined')
        lora.nvram_save()
        
# create a LoRa socket
s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# set the LoRaWAN data rate
s.setsockopt(socket.SOL_LORA, socket.SO_DR, 5)

# make the socket blocking
# (waits for the data to be sent and for the 2 receive windows to expire)
s.setblocking(True)

# send some data
s.send(bytes([0x01, 0x02, 0x03]))

# make the socket non-blocking
# (because if there's no data received it will block forever...)
s.setblocking(False)

# get any data received (if any...)
data = s.recv(64)
print(data)
def sendLoraOk():
    print('send lora OK')
    return

def sendLoraNok():
    print('send lora UnAuthorised Entry attempt')
    return

pybytes_enabled = False
if 'pybytes' in globals():
    if(pybytes.isconnected()):
        print('Pybytes is connected, sending signals to Pybytes')
        pybytes_enabled = True

RGB_BRIGHTNESS = 0x8

RGB_RED = (RGB_BRIGHTNESS << 16)
RGB_GREEN = (RGB_BRIGHTNESS << 8)
RGB_BLUE = (RGB_BRIGHTNESS)

counter = 0

def check_uid(uid, len):
    return VALID_CARDS_SD.count(uid[:len])

def send_sensor_data(name, timeout):
    if(pybytes_enabled):
        while(True):
            pybytes.send_signal(2, lt.light())
            pybytes.send_signal(3, li.acceleration())
            time.sleep(timeout)

# Make sure heartbeat is disabled before setting RGB LED
pycom.heartbeat(False)

# Initialise the MFRC630 with some settings
nfc.mfrc630_cmd_init()

print('Scanning for cards')
while True:
    # Send REQA for ISO14443A card type
    atqa = nfc.mfrc630_iso14443a_WUPA_REQA(nfc.MFRC630_ISO14443_CMD_REQA)
    if (atqa != 0):
        # A card has been detected, read UID
        print('A card has been detected, reading its UID ...')
        uid = bytearray(10)
        uid_len = nfc.mfrc630_iso14443a_select(uid)
        print('UID has length {}'.format(uid_len))
        if (uid_len > 0):
            # A valid UID has been detected, print details
            counter += 1
            print("%d\tUID [%d]: %s" % (counter, uid_len, nfc.format_block(uid, uid_len)))
            if DECODE_CARD:
                # Try to authenticate with CARD key
                nfc.mfrc630_cmd_load_key(CARDkey)
                for sector in range(0, 16):
                    if (nfc.mfrc630_MF_auth(uid, nfc.MFRC630_MF_AUTH_KEY_A, sector * 4)):
                        pycom.rgbled(RGB_GREEN)
                        # Authentication was sucessful, read card data
                        readbuf = bytearray(16)
                        for b in range(0, 4):
                            f_sect = sector * 4 + b
                            len = nfc.mfrc630_MF_read_block(f_sect, readbuf)
                            print("\t\tSector %s: Block: %s: %s" % (nfc.format_block([sector], 1), nfc.format_block([b], 1), nfc.format_block(readbuf, len)))
                    else:
                        print("Authentication denied for sector %s!" % nfc.format_block([sector], 1))
                        pycom.rgbled(RGB_RED)
                    

                # It is necessary to call mfrc630_MF_deauth after authentication
                # Although this is also handled by the reset / init cycle
                nfc.mfrc630_MF_deauth()
            else:
                #check if card uid is listed in VALID_CARDS
                if (check_uid(list(uid), uid_len)) > 0:
                    print('Card is listed, turn LED green')
                    pycom.rgbled(RGB_GREEN)
                    sendLoraOk()
                    #if(pybytes_enabled):
                    #    pybytes.send_signal(1, ('Card is listed', uid))
                        
                else:
                    print('Card is not listed, turn LED red')
                    pycom.rgbled(RGB_RED)
                    sendLoraNok()
                    #if(pybytes_enabled):
                    #    pybytes.send_signal(1, ('Unauthorized card detected', uid))
                        
    else:
        pycom.rgbled(RGB_BLUE)
    # We could go into power saving mode here... to be investigated
    nfc.mfrc630_cmd_reset()
    time.sleep(.5)
    # Re-Initialise the MFRC630 with settings as these got wiped during reset
    nfc.mfrc630_cmd_init()
