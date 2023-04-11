#Python 3
import multiprocessing as mp
import threading
import serial
import time
import glob
import sys
#58 possible combos (0-9, 24 lower and 24 uppercase)

MESSAGES_COMMAND = []
MESSAGES_RECEIVED = []
QUIT = False

class SmsMonitor:
	connected = False
	has_messages = False
	COMPLETE = False
	SER = serial.Serial()
	CPID_COORDINATOR = 0
	HEADER = '#$ls;'
	COMMAND_MESSAGE_LOCK = threading.Lock()
	RECEIVED_MESSAGE_LOCK = threading.Lock()


	def __init__(self):
		connected = False
		has_messages = False

	def getSerialPorts(self):
		#For Linux
		#https://makersportal.com/blog/2018/2/25/python-datalogger-reading-the-serial-output-from-arduino-to-analyze-data-using-pyserial
		ports = glob.glob('/dev/ttyACM*')
		#For Mac
		# ports = glob.glob('/dev/tty.*')
		result = []
		for port in ports:
			try:
				s = serial.Serial(port)
				s.close()
				result.append(port)
			except (OSError, serial.SerialException):
				pass
		return result

	def connect(self):
		r = self.getSerialPorts()
		port = ""
		for i in r:
			if i.find("usbmodem") != -1:
				port = i
		port = i
		print("Checking Port:")
		print(port)
		if(port != ""):
			ser = serial.Serial(port, 115200, timeout=1)
			self.SER = ser
			#initialize
			while(self.COMPLETE == False):
				if(ser.in_waiting != 0):
					ser_data = ser.read_until()
					# print(ser_data)
					if(ser_data == b'leopard_seal_init\r\n'):
						self.COMPLETE = True
						connected = True
						self.SER.write(b'#$ls;ls_confirm_ready\n')
						self.SER.reset_input_buffer()
						self.beginMonitor()
			return 1
		else:
			return 0

	def send(self, message):
		# print("Writing to Coord Pipe")
		m = self.HEADER + message
		self.COMMAND_MESSAGE_LOCK.acquire()
		MESSAGES_COMMAND.append(m)
		self.COMMAND_MESSAGE_LOCK.release()
		# print("Wrote to coord pipe")

	def hasMessage(self):
		self.RECEIVED_MESSAGE_LOCK.acquire()
		message_count = len(MESSAGES_RECEIVED)
		self.RECEIVED_MESSAGE_LOCK.release()

		if(message_count >= 1):
			return 1
		else:
			return 0

	def getMessage(self):
		if(len(MESSAGES_RECEIVED) > 0):
			self.RECEIVED_MESSAGE_LOCK.acquire()
			got_message = MESSAGES_RECEIVED.pop(0)
			self.RECEIVED_MESSAGE_LOCK.release()
			got_message = got_message.replace(self.HEADER, '')
			return got_message
		else:
			return "NULL"

	def quit(self):
		global QUIT
		QUIT = True
		time.sleep(1)

	def beginMonitor(self):
		#Fork Thread
		cpid = threading.Thread(target=self.coordinator, args=(self.COMMAND_MESSAGE_LOCK, self.RECEIVED_MESSAGE_LOCK))
		cpid.start()
		self.CPID_COORDINATOR = cpid
		print("Monitor Started")

	def coordinator(self, cm_lock, rm_lock):
		global QUIT
		print("Coordinator started")
		while QUIT == False:
			time.sleep(0.1)
			if(len(MESSAGES_COMMAND) > 0):
				cm_lock.acquire()
				command = MESSAGES_COMMAND[0]
				MESSAGES_COMMAND.pop(0)
				cm_lock.release()

				# print("Coordinator got message from Main: " + command)

				# print("SENDING MESSAGE TO HARDWARE")
				# m = self.HEADER + command
				m = command
				to_send = bytes(m, 'ascii')
				# print(to_send)
				self.SER.write(to_send)

			if(self.SER.in_waiting != 0):
				ser_data = self.SER.read_until()
				ser_string = ser_data.decode('ASCII')
				# print(ser_string)
				if(ser_string.find(self.HEADER) != -1):
					rm_lock.acquire()
					MESSAGES_RECEIVED.append(ser_string)
					rm_lock.release()
				elif(ser_string.find('Threshold') != -1 or ser_string.find('Value') != -1):
					print(ser_string)
