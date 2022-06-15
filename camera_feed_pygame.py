from PIL import Image

from socket import *
import struct
import sys
import io
import pygame


BROADCAST_IP = '255.255.255.255'
BROADCAST_PORT = 32108

HELLO_PORT = 32100

CAM_PORT = 8070
CAM_RDY_PORT = 8080

PPPP_MAGIC_NUMBER = 0xF1

MSG_HELLO=                     0x00
MSG_HELLO_ACK=                 0x01
MSG_HELLO_TO=                  0x02
MSG_HELLO_TO_ACK=              0x03
MSG_QUERY_DID=                 0x08
MSG_QUERY_DID_ACK=             0x09
MSG_DEV_LGN=                   0x10
MSG_DEV_LGN_ACK=               0x11
MSG_DEV_LGN_CRC=               0x12
MSG_DEV_LGN_ACK_CRC=           0x13
MSG_DEV_LGN_KEY=               0x14
MSG_DEV_LGN_ACK_KEY=           0x15  
MSG_DEV_ONLINE_REQ=            0x18
MSG_DEV_ONLINE_REQ_ACK=        0x19  
MSG_P2P_REQ=                   0x20
MSG_P2P_REQ_ACK=               0x21
MSG_LAN_SEARCH=                0x30 #sent without magic number
MSG_LAN_NOTIFY=                0x31 #immediately after, again no magic
MSG_LAN_NOTIFY_ACK=            0x32 #maybe 0x04 -> 0x32 (endianess is wrong in decrypted packet) 
MSG_PUNCH_TO=                  0x40
MSG_PUNCH_PKT=                 0x41
MSG_PUNCH_PKT_EX=              0x41
MSG_P2P_RDY=                   0x42
MSG_P2P_RDY_EX=                0x42
MSG_P2P_RDY_ACK=               0x43
MSG_RS_LGN=                    0x60
MSG_RS_LGN_ACK=                0x61
MSG_RS_LGN1=                   0x62
MSG_RS_LGN1_ACK=               0x63
MSG_LIST_REQ1=                 0x67
MSG_LIST_REQ=                  0x68
MSG_LIST_REQ_ACK=              0x69
MSG_RLY_HELLO=                 0x70
MSG_RLY_HELLO_ACK=             0x71
MSG_RLY_PORT=                  0x72
MSG_RLY_PORT_ACK=              0x73
MSG_RLY_PORT_KEY=              0x74
MSG_RLY_PORT_ACK_KEY=          0x75  
MSG_RLY_BYTE_COUNT=            0x78
MSG_RLY_REQ=                   0x80
MSG_RLY_REQ_ACK=               0x81
MSG_RLY_TO=                    0x82
MSG_RLY_PKT=                   0x83
MSG_RLY_RDY=                   0x84
MSG_RLY_TO_ACK=                0x85
MSG_RLY_SERVER_REQ=            0x87
MSG_RLY_SERVER_REQ_ACK=        0x87  
MSG_SDEV_RUN=                  0x90
MSG_SDEV_LGN=                  0x91
MSG_SDEV_LGN_ACK=              0x91
MSG_SDEV_LGN_CRC=              0x92
MSG_SDEV_LGN_ACK_CRC=          0x92
MSG_SDEV_REPORT=               0x94
MSG_CONNECT_REPORT=            0xA0
MSG_REPORT_REQ=                0xA1
MSG_REPORT=                    0xA2
MSG_DRW=                       0xD0
MSG_DRW_ACK=                   0xD1
MSG_PSR=                       0xD8
MSG_ALIVE=                     0xE0
MSG_ALIVE_ACK=                 0xE1
MSG_CLOSE=                     0xF0
MSG_MGM_DUMP_LOGIN_DID=        0xF4
MSG_MGM_DUMP_LOGIN_DID_DETAIL= 0xF5
MSG_MGM_DUMP_LOGIN_DID_1=      0xF6
MSG_MGM_LOG_CONTROL=           0xF7
MSG_MGM_REMOTE_MANAGEMENT=     0xF8

HEADER_FMT = '>BB'


def network_loop(screen):
	#print("network loop()")

	s = socket(AF_INET, SOCK_DGRAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	s.bind(('',0))

	camera_initialized = initiate_camera(s)
	if( not camera_initialized ):
		print("Unable to initialize camera...")
		print("Make sure your computer is connected to the camera's WiFi AP")
		

	frame = bytearray()
	while camera_initialized:
		(buf, rinfo) = s.recvfrom(4096)
		port = rinfo[1]
		
		if(port == 8080):
			#print("8080 packet")
			if(packet_is_image_start(buf)):
				frame = bytearray(buf)[8:]
			else:
				frame += bytearray(buf)[8:]

			if(packet_is_image_end(buf)):
				#create image and enqueue it
				#print("end packet")
				try:
					raw_image = Image.open(io.BytesIO(bytes(frame[:])))

					surface = pil_img_to_surface(raw_image)
					screen.blit(surface, (0,0))
					pygame.display.flip()

					#tk_image = ImageTk.PhotoImage(raw_image)
					#image_queue.put(tk_image, False)
				except OSError as e:
					print(e)
				except Exception as e:
					print(e)
				
		#elif(port == 8070):
			#print("8070 packet")

def initiate_camera(sock):
	#3 msgs, 6 bytes
	msg1 = struct.pack(HEADER_FMT, MSG_LAN_SEARCH, 0x67)
	msg2 = struct.pack(HEADER_FMT, MSG_LAN_SEARCH, 0x66)
	msg_rdy = struct.pack(HEADER_FMT, MSG_P2P_RDY, 0x76)

	size = sock.sendto(msg1, ('192.168.4.153', CAM_PORT))
	size += sock.sendto(msg2, ('192.168.4.153', CAM_PORT))
	size += sock.sendto(msg_rdy, ('192.168.4.153', CAM_RDY_PORT))

	return (size == 6)

def packet_is_image_start(buf):
	#may also want to look for the full JFIF header...
	IMAGE_START = [0xff, 0xd8] #JFIF image start identifier
	for i in range(0, len(buf)-1):
		if(buf[i] == IMAGE_START[0] and buf[i+1] == IMAGE_START[1]):
			return True
	return False

def packet_is_image_end(buf):
	IMAGE_END = [0xff, 0xd9]
	for i in range(0, len(buf)-1):
		if(buf[i] == IMAGE_END[0] and buf[i+1] == IMAGE_END[1]):
			return True
	return False

def pil_img_to_surface(pil_image):
	return pygame.image.fromstring(pil_image.tobytes(), pil_image.size, pil_image.mode).convert()

if __name__ == '__main__':
	
	pygame.init()
	w = 640
	h = 480
	screen = pygame.display.set_mode((w,h))
	pygame.display.set_caption('Little Stars Hack')

	#_thread.start_new_thread(network_loop, ())
	#no threading because no tkinter, we render to screen in the main loop
	network_loop(screen)
