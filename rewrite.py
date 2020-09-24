import pyaudio
import wave
import os
import struct
import numpy as np
import time
import serial
import math
import statistics 
import pylab as pl
import matplotlib.pyplot as plt

defaultframes = 256

class textcolors:
    if not os.name == 'nt':
        blue = '\033[94m'
        green = '\033[92m'
        warning = '\033[93m'
        fail = '\033[91m'
        end = '\033[0m'
    else:
        blue = ''
        green = ''
        warning = ''
        fail = ''
        end = ''

def listToString(s):  
    
    # initialize an empty string 
    str1 = ""  
    
    # traverse in the string   
    for ele in s:  
        str1 += str(ele)   
    str1 += '\n'
    # return string   
    return str1  


recorded_frames = []
device_info = {}
useloopback = False
recordtime = 5

#Use module
p = pyaudio.PyAudio()

#Set default to first in list or ask Windows
try:
    default_device_index = p.get_default_input_device_info()
except IOError:
    default_device_index = -1

#Select Device
print (textcolors.blue + "Available devices:\n" + textcolors.end)
for i in range(0, p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print (textcolors.green + str(info["index"]) + textcolors.end + ": \t %s \n \t %s \n" % (info["name"], p.get_host_api_info_by_index(info["hostApi"])["name"]))

    if default_device_index == -1:
        default_device_index = info["index"]

#Handle no devices available
if default_device_index == -1:
    print (textcolors.fail + "No device available. Quitting." + textcolors.end)
    exit()


#Get input or default
device_id = int(input("Choose device [" + textcolors.blue + str(default_device_index) + textcolors.end + "]: ") or default_device_index)
print ("")

#Get device info
try:
    device_info = p.get_device_info_by_index(device_id)
except IOError:
    device_info = p.get_device_info_by_index(default_device_index)
    print (textcolors.warning + "Selection not available, using default." + textcolors.end)

#Choose between loopback or standard mode
is_input = device_info["maxInputChannels"] > 0
is_wasapi = (p.get_host_api_info_by_index(device_info["hostApi"])["name"]).find("WASAPI") != -1
if is_input:
    print (textcolors.blue + "Selection is input using standard mode.\n" + textcolors.end)
else:
    if is_wasapi:
        useloopback = True;
        print (textcolors.green + "Selection is output. Using loopback mode.\n" + textcolors.end)
    else:
        print (textcolors.fail + "Selection is input and does not support loopback mode. Quitting.\n" + textcolors.end)
        exit()

#recordtime = int(input("Record time in seconds [" + textcolors.blue + str(recordtime) + textcolors.end + "]: ") or recordtime)


serial_id = str(input("Name the serial port: ") or 'COM3')
#Open serial
arduino = serial.Serial(serial_id, 9600)
time.sleep(3) #connection
 
#Open stream
channelcount = device_info["maxInputChannels"] if (device_info["maxOutputChannels"] < device_info["maxInputChannels"]) else device_info["maxOutputChannels"]
print("channel count: " + str(channelcount))
stream = p.open(format = pyaudio.paInt16,
                channels = channelcount,
                rate = int(device_info["defaultSampleRate"]),
                input = True,
                frames_per_buffer = defaultframes,
                input_device_index = device_info["index"],
                as_loopback = useloopback)

#Start Recording
print (textcolors.blue + "Starting..." + textcolors.end)
#* recordtime
count = 0
sendVal = ""


while True:
    #get binary chunk
    data = stream.read(defaultframes)
    #format binary chunk and put it in an np array
    rfint = struct.unpack(str(len(data)) + 'B', data)
    npdata = np.array(rfint, dtype=np.byte)
    for x in range(0,npdata.size):
        if npdata[x] == -1 or npdata[x] == 1:
            npdata[x] = 0
   # print("npdata: " + str(npdata.size))
   # p = 20*np.log10(np.abs(np.fft.fft(npdata)))
    p = np.fft.fft(npdata)
    #print(p[:10])

    peak = -1
    for j in range(0, math.floor(npdata.size/2)):
        #get magnitude for comparision
        magnitude = math.sqrt(npdata[j].real**2 + npdata[j].imag**2)
        freq = j * device_info["defaultSampleRate"] / npdata.size;
        if freq > 49 and freq <= 100:
            if magnitude > peak:
                peak = magnitude
    
    if peak != 0:
        #print("peak: " + str(peak))
        sendVal = (str(int((peak)))) + '\n'
        arduino.write(sendVal.encode('utf-8'))
        


    #reset the np array
    npdata = np.array([])
    #time.sleep(.016)




arduino.close()

print (textcolors.blue + "End." + textcolors.end)
#Stop Recording

stream.stop_stream()
stream.close()

#Close module
p.terminate()

filename = input("Save as [" + textcolors.blue + "out.wav" + textcolors.end + "]: ") or "out.wav"

waveFile = wave.open(filename, 'wb')
waveFile.setnchannels(channelcount)
waveFile.setsampwidth(p.get_sample_size(pyaudio.paInt16))
waveFile.setframerate(int(device_info["defaultSampleRate"]))
waveFile.writeframes(b''.join(recorded_frames))
waveFile.close()