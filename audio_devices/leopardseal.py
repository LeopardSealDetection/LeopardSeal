#!/usr/bin/env python3

import sys
sys.path.insert(1, './code')
import pi_serial
import datetime
import time
import glob
import sys
import threading
import simpleaudio as sa
import signal
import numpy as np

# Check command line arguments
if (len(sys.argv) < 2):
    print('Usage: python3 leopardseal.py "St. Louis"\n' +
          '       ./leopardseal.py "San Diego"\n' +
          '       ./leopardseal.py results/san_diego')
    sys.exit()

folder = 'results/' + sys.argv[1].replace('.', '').replace(' ', '_').lower() + '/'

# Also accept direct path
if '/' in sys.argv[1]:
    folder = sys.argv[1]
    if folder[-1] != '/':
        folder = folder + '/'

DATAFILE_NAME = folder + 'data.csv'
ser_com = pi_serial.SmsMonitor()
QUIT = False
last_command = ''
# ct stores current time
CT = datetime.datetime.now() #Format: 2020-07-15 14:30:26.159446
EXP_SCHEDULE = [] #Used for storing the schedule to run experiments

RESPONSE_TIMEOUT = 24 #Length to wait for a response in seconds

# Check call status
def getCallStatus():

    # Send serial command
    ser_com.send('cstat;0')

    # Print Response
    response = checkReceivedMessages()
    num = -1
    if response[0] == 'callstat':
        num = int(response[1])
        if num == 0:
            print('Ready')
        elif num == 1:
            print('Call failed')
        elif num == 2:
            print('Unknown')
        elif num == 3:
            print('Ringing')
        elif num == 4:
            pass
            # print('Call in progress')
        else:
            num = -1
            print('Call Status Error')
    else:
        print('Call Status Error')

    return num

#Request the Network Status from the hardware
def getNetworkStatus():

    # Send serial command
    ser_com.send('nstat;0')

    #Print Response
    response = checkReceivedMessages()
    num = -1
    if response[0] == 'netstat':
        num = int(response[1])
        if num == 0:
            print('Not registered')
        elif num == 1:
            print('Registered, home network')
        elif num == 2:
            print('Searching for network')
        elif num == 3:
            print('Issue connecting to network')
        elif num == 4:
            print('Registered, Roaming')
        else:
            num = -1
            print('Network Error')
    else:
        print('Network Error')

    return num

# Try to make a call
def callNumber(phone_num):

    # Send serial command
    print('calln;' + phone_num)
    ser_com.send('calln;' + phone_num)

    # Print response
    response = checkReceivedMessages()
    num = -3
    if response[0] == 'call_ack':
        num = int(response[1])
        if num == -1:
            print('call not answered')
        elif num == -2:
            print('no service')
        elif num == 1:
            print('Call connected to BTS')
        else:
            num = -3
            print('Call Error ' + response[1])
            print(response)
    else:
        print('Call Error ' + response[1])
        print(response)

    return num

# Play audio tone
def playTone():
    filename = 'code/audio_player/1000hz_0.1.wav'
    wave_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = wave_obj.play()
    play_obj.wait_done()  # Wait until sound has finished playing

# Record sample
def recordSample():

    # Send serial command
    ser_com.send('records;0')

    # Play tone
    # for i in range(0,2):
    time.sleep(2)
    playTone()

    # Print Response
    response = checkReceivedMessages()
    num = -3
    # print(response)
    if response[0] == 'records':
        num = float(response[1])
        if num == -1:
            print('couldn\'t get RTT value')
        elif num == -2:
            print('Not on call')
        elif num >= 0:
            print('%i ms' % float(response[1].strip()))
        else:
            num = -3
            print('Record Error')
    else:
        print('Record Error')

    # Return result
    return num

# Analog read
def analogSample():

    # Send serial command
    ser_com.send('rawsampleread;0')

    # Print response
    response = checkReceivedMessages()
    if response[0] == 'rawstat' and response[1] == '1':
        print('Received')
        return 0
    else:
        print('Error')
        return -1

# Stop analog read
def stopAnalog():

    # Send serial command
    ser_com.send('stopraw;0')

    # Print response
    response = checkReceivedMessages()
    if response[0] == 'rawstat' and response[1] == '0':
        print('Received')
        return 0
    else:
        print('Error')
        return -1

# End a call
def endCall():

    # Send serial command
    ser_com.send('endc;0')

    # Print response
    response = checkReceivedMessages()
    num = -1
    if response[0] == 'end_ack':
        num = int(response[1])
        if num == 1:
            print('call ended')
        elif num == 0:
            print('call ended')
        else:
            num = -1
            print('End Call Error')
    else:
        print('End Call Error')

    return num

# Run a set of experiments. Tell the hardware to start a call and get samples. Record the data and end the call when done
def runExperiments(sample_count, phone_num, sr_status):

    rtt_data_list = []              # List of RTT data
    CT = datetime.datetime.now()    # Get current date and time
    i = 0                           # Loop counter

    # Loop until target samples are taken
    while i < sample_count:

        CT = datetime.datetime.now()    # Get current date and time

        # Add delay between calls
        time.sleep(8)

        # Place Call, retry if necessary
        while True:
            callNumber(phone_num)
            time.sleep(16)
            if getCallStatus() == 4:
                break

        # Verify call is in progress, retry loop if not
        if getCallStatus() != 4:
            print('Call ended before samples were taken')
            continue

        print('\nCollecting samples')

        # Delay measurements for several seconds while playing tones
        for k in range(0,2):
            time.sleep(8)
            playTone()

        # Aggregate delays to calculate average
        aggregate_delays = []

        # Take several measurements, then average to get a sample
        skip = False
        zero_count = 0
        j = 0
        NUM_SAMPLES = 8
        while j < NUM_SAMPLES:

            # End call if we receive ten consecutive failed measurements
            if zero_count == 10:
                skip = True
                endCall()
                break

            # Record sample
            sample = recordSample()

            # Valid sample
            if sample > 0:
                aggregate_delays.append(sample)

            # Call was dropped
            elif sample == -2:
                print('Call ended before enough samples were taken')
                skip = True
                break

            # RTT test failed, retry
            elif sample == -1:
                continue

            elif sample == 0:
                zero_count += 1
                continue

            # Error occurred
            else:
                print('Error occurred during test')
                return -1

            # Increment couunter
            j += 1

        if not skip:
            # Calculate average and add to results
            aggregate_delays = np.array(aggregate_delays)
            aggregate_delays = aggregate_delays[abs(aggregate_delays - np.mean(aggregate_delays)) < 2. * np.std(aggregate_delays)]
            rtt_data_list.append(np.mean(aggregate_delays))
            # Save Data when Done
            # saveData([np.mean(aggregate_delays)], sr_status, CT)
            saveData(aggregate_delays, sr_status, CT)
            print('Final measurement: %i ms\n' % np.mean(aggregate_delays))

            # Increment counter after successful sample
            i += 1

            #End Call
            endCall()

    #Print RTT value list
    for i in rtt_data_list:
        print('%f ms' % i)

    return 1

#This function is to handle all of the messages to be sent to the hardware
#To send a message using the library use the command: ser_com.send(message_string)
def sendMessage(message_id, data="no_data"):
    global last_command

    #Need to craft the message string
    message_string = ""

    # Handle empty case
    if(message_id == ''):
        return

    # Get Network Status
    elif(message_id == 'n'):
        getNetworkStatus()
        # last_command = message_id

    # Get Network Status
    elif(message_id == 'x'):
        getCallStatus()
        # last_command = message_id

    # Place call to default number
    elif(message_id == 'c'):
        # Get number, send call command, get response
        ret = callNumber('3528702102')
        last_command = message_id
        time.sleep(16)
        while getCallStatus() != 4:
            callNumber('3528702102')
            time.sleep(16)

    # Place call, number data should be stored in 'data' input variable
    elif(message_id[0] == 'c' and len(message_id) > 2):
        # Get number, send call command, get response
        callNumber(message_id.split(';')[1])
        last_command = message_id

    # Place call, number data should be stored in 'data' input variable
    elif(message_id[0] == 'c' and len(message_id) == 2):
        number = ''
        if message_id[1] == '1':
            number = '3528702102'
        elif message_id[1] == '2':
            number = '3523289812'
        else:
            print("Error: No command matches that ID")
            return
        # Get number, send call command, get response
        callNumber(number)
        last_command = message_id

    # Scedule a test
    elif(message_id[0] == 's' and len(message_id) > 2 and len(message_id.split(';')) == 8):
        # Send status command, get response
        message_id = message_id.split(';')
        EXP_SCHEDULE.append([datetime.datetime(2022, int(message_id[1]), int(message_id[2]), hour=int(message_id[3]), minute=int(message_id[4])), int(message_id[5]), message_id[6], message_id[7]])
        print(EXP_SCHEDULE)
        last_command = message_id

    # End Call
    elif(message_id == 'e'):
        # Send end call command, get response
        endCall()
        # last_command = message_id

    # Get RTT Sample
    elif(message_id[0] == 'r' and len(message_id) > 2 and len(message_id.split(';')) == 4):
        command = message_id.split(';')
        runExperiments(int(command[1]), command[2], command[3])
        last_command = message_id

    # View schedule
    elif(message_id == 'v'):
        if EXP_SCHEDULE:
            for item in EXP_SCHEDULE:
                print(item)
        else:
            print('empty')
        # last_command = message_id

    # Raw analog sample
    elif(message_id == 'a'):
        # Send command, get response
        analogSample()
        # last_command = message_id

    # Stop analog sampling
    elif(message_id == 't'):
        # Send command, get response
        stopAnalog()
        # last_command = message_id

    # Manual test
    elif(message_id == 'm'):
        # Send command, get response
        recordSample()
        # last_command = message_id

    # Play tone
    elif(message_id == 'p'):
        # Send command, get response
        playTone()
        # last_command = message_id

    # Run last command
    elif(message_id == 'l'):
        sendMessage(last_command)

    # Help
    elif(message_id == 'h'):
        print('\nGet network status | n\n' +
            'Get call status | x\n' +
            'Place call | c;phone_number\n' +
            'Place call to default number | c\n' +
            # 'Get call status | s\n' +
            'End call | e\n' +
            'Run experiment | r;sample_count;phone_number;sr_status\n' +
            'Schedule experiment | s;mon;day;h;m;sample_count;phone_num;sr_status\n' +
            'Start raw analog read | a\n' +
            'Stop analog read | t\n' +
            'Run instant test | m\n' +
            'Play tone | p\n' +
            'Run last command | l\n' +
            'Quit | q\n')
        last_command = message_id

    # Quit
    elif(message_id == 'q'):
        resetBoard()
        ser_com.quit()
        global QUIT
        QUIT = True

    elif(message_id == 'Q'):
        endCall()
        resetBoard()
        ser_com.quit()
        QUIT = True


    # If none of the above, print error
    else:
        print("Error: No command matches that ID")


    #After sending the message, call checkReceivedMessages() to get the response then handle accordingly
    pass

#This function checks if a response to a message has been received and returns it. This has already been done for you.
#Returns 'error' if there is a response timeout
#Returns the message if it is received within the response time
def checkReceivedMessages():

    ret_message = "timeout"

    t_start = time.perf_counter()

    while(time.perf_counter() - t_start < RESPONSE_TIMEOUT):
        if(ser_com.hasMessage()):
            total_message = ser_com.getMessage().strip()
            # print(total_message)
            ret_message = total_message.split(';')
            # print(ret_message)
            # Special case for running analog sample
            if (ret_message[0] == 'rawstaterror') and (ret_message[1] == '1'):
                print('Error - currently performing analog test')
            break

    return(ret_message)

# Reset caller board
def resetBoard():

    # Send serial command
    ser_com.send('reset;0')

    # Print response
    response = checkReceivedMessages()
    num = -1
    if response[0] == 'rst_ack':
        num = int(response[1])
        if num == 1:
            print('Board Reset')
        else:
            num = -1
            print('Board Reset Error')
    else:
        print('Board Reset Error')

    return num

#Helper Functions

#Function to save the RTT data
def saveData(rtt_data_list, sr_status, dt_info):

    # Format: mon,day,hour,minute,sr_stat,list_of_rtt_values_seperated_by_;_character

    # Convert results array to string
    rtt_str = ''
    for i in rtt_data_list:
        rtt_str += str(i) + ';'

    # Combine date, stingray status, and results strings
    save_data = dt_info.strftime('%m,%d,%H,%M,') + sr_status + ',' + rtt_str[:-1] + '\n'

    # Write data to corresponding file
    f = open(DATAFILE_NAME, 'a')
    f.write(save_data)
    f.close()

    # Write data to aggregate file
    f = open('results/total_data.csv', 'a')
    f.write(save_data)
    f.close()

#Function for scheduling a data collection
def scheduler():
    global EXP_SCHEDULE
    global QUIT
    while (not QUIT):
        time.sleep(0.1)
        for item in EXP_SCHEDULE:
            if (datetime.datetime.now() - item[0]).total_seconds() > 0:
                result = runExperiments(item[1], item[2], item[3])
                if result == 1:
                    EXP_SCHEDULE.pop(0)
                print('Task: ', end = '')
                time.sleep(0.1)

# Handle signals
def exit_gracefully(signum, frame):
    if getCallStatus() == 4:
        endCall()
    resetBoard()
    ser_com.quit()
    global QUIT
    QUIT = True
    sys.exit()

#See excel sheet
def mainLoop():
    global QUIT
    cpid = threading.Thread(target=scheduler)
    cpid.start()
    while(not QUIT):
        #Look for keyboard commands and handle accordingly
        task = input('Task: ')
        sendMessage(task)
        # time.sleep(0.1)
        #Check if it's time to run experiments
    return

#Initial Function that starts up the serial communication
if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    i = ser_com.connect()
    mainLoop()
