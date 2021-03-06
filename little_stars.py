from socket import *
import struct
import logging
import sys

BROADCAST_IP = '255.255.255.255'
BROADCAST_PORT = 32108

HELLO_PORT = 32100

QUIC_PORT = 8070
QUIC_RDY_PORT = 8080

PPPP_MAGIC_NUMBER=             0xF1

KEY_TABLE = [
  0x7C, 0x9C, 0xE8, 0x4A, 0x13, 0xDE, 0xDC, 0xB2, 0x2F, 0x21, 0x23, 0xE4, 0x30, 0x7B, 0x3D, 0x8C,
  0xBC, 0x0B, 0x27, 0x0C, 0x3C, 0xF7, 0x9A, 0xE7, 0x08, 0x71, 0x96, 0x00, 0x97, 0x85, 0xEF, 0xC1,
  0x1F, 0xC4, 0xDB, 0xA1, 0xC2, 0xEB, 0xD9, 0x01, 0xFA, 0xBA, 0x3B, 0x05, 0xB8, 0x15, 0x87, 0x83,
  0x28, 0x72, 0xD1, 0x8B, 0x5A, 0xD6, 0xDA, 0x93, 0x58, 0xFE, 0xAA, 0xCC, 0x6E, 0x1B, 0xF0, 0xA3,
  0x88, 0xAB, 0x43, 0xC0, 0x0D, 0xB5, 0x45, 0x38, 0x4F, 0x50, 0x22, 0x66, 0x20, 0x7F, 0x07, 0x5B,
  0x14, 0x98, 0x1D, 0x9B, 0xA7, 0x2A, 0xB9, 0xA8, 0xCB, 0xF1, 0xFC, 0x49, 0x47, 0x06, 0x3E, 0xB1,
  0x0E, 0x04, 0x3A, 0x94, 0x5E, 0xEE, 0x54, 0x11, 0x34, 0xDD, 0x4D, 0xF9, 0xEC, 0xC7, 0xC9, 0xE3,
  0x78, 0x1A, 0x6F, 0x70, 0x6B, 0xA4, 0xBD, 0xA9, 0x5D, 0xD5, 0xF8, 0xE5, 0xBB, 0x26, 0xAF, 0x42,
  0x37, 0xD8, 0xE1, 0x02, 0x0A, 0xAE, 0x5F, 0x1C, 0xC5, 0x73, 0x09, 0x4E, 0x69, 0x24, 0x90, 0x6D,
  0x12, 0xB3, 0x19, 0xAD, 0x74, 0x8A, 0x29, 0x40, 0xF5, 0x2D, 0xBE, 0xA5, 0x59, 0xE0, 0xF4, 0x79,
  0xD2, 0x4B, 0xCE, 0x89, 0x82, 0x48, 0x84, 0x25, 0xC6, 0x91, 0x2B, 0xA2, 0xFB, 0x8F, 0xE9, 0xA6,
  0xB0, 0x9E, 0x3F, 0x65, 0xF6, 0x03, 0x31, 0x2E, 0xAC, 0x0F, 0x95, 0x2C, 0x5C, 0xED, 0x39, 0xB7,
  0x33, 0x6C, 0x56, 0x7E, 0xB4, 0xA0, 0xFD, 0x7A, 0x81, 0x53, 0x51, 0x86, 0x8D, 0x9F, 0x77, 0xFF,
  0x6A, 0x80, 0xDF, 0xE2, 0xBF, 0x10, 0xD7, 0x75, 0x64, 0x57, 0x76, 0xF3, 0x55, 0xCD, 0xD0, 0xC8,
  0x18, 0xE6, 0x36, 0x41, 0x62, 0xCF, 0x99, 0xF2, 0x32, 0x4C, 0x67, 0x60, 0x61, 0x92, 0xCA, 0xD3,
  0xEA, 0x63, 0x7D, 0x16, 0xB6, 0x8E, 0xD4, 0x68, 0x35, 0xC3, 0x52, 0x9D, 0x46, 0x44, 0x1E, 0x17
];

TEST_PACKET = [
	0xa8, 0x5e, 0x45, 0xd7, 0x97, 0xfe, 0x00, 0x1e, #header
	0xb5, 0x22, 0xda, 0x32, 0x08, 0x00, 0x45, 0x00, #header
	0x05, 0xdc, 0x4b, 0xd4, 0x00, 0x00, 0xff, 0x11, #header, byte 4 is a counter of some sort
	0xdf, 0xed, 0xc0, 0xa8, 0x04, 0x99, 0xc0, 0xa8, #header, byte 2 counts down, maybe part of timestamp
	0x04, 0x65, 0x1f, 0x86, 0xc3, 0xb2, 0x05, 0xc8, 
	0xdf, 0xd3, 0xf7, 0xff, 0xf7, 0xff, 0xfc, 0xff, 
	0xfb, 0xff, 0xfe, 0xff, 0xff, 0xff, 0xfd, 0xff, 
	0xfc, 0xff, 0xfc, 0xff, 0xfe, 0xff, 0xfb, 0xff, 
	0xfc, 0xff, 0xfe, 0xff, 0xfd, 0xff, 0xff, 0xff, 
	0xfd, 0xff, 0xfc, 0xff, 0xfe, 0xff, 0xfe, 0xff, 
	0xfd, 0xff, 0xfe, 0xff, 0xfe, 0xff, 0x01, 0x00, 
	0x06, 0x00, 0x06, 0x00, 0x05, 0x00, 0x07, 0x00, 
	0x05, 0x00, 0x04, 0x00, 0x05, 0x00, 0x03, 0x00, 
	0x01, 0x00, 0xff, 0xff, 0xfb, 0xff, 0xf9, 0xff, 
	0xfd, 0xff, 0xfd, 0xff, 0xfb, 0xff, 0xfd, 0xff, 
	0xfd, 0xff, 0xfe, 0xff, 0xfd, 0xff, 0xfd, 0xff, 
	0xfe, 0xff, 0x00, 0x00, 0x03, 0x00, 0x02, 0x00, 
	0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0xfb, 0xff, 
	0x19, 0x00, 0x45, 0x00, 0x0d, 0x00, 0xe6, 0xff, 
	0xf2, 0xff, 0xf1, 0xff, 0xfa, 0xff, 0xfc, 0xff, 
	0xfe, 0xff, 0x04, 0x00, 0x06, 0x00, 0x08, 0x00, 
	0x09, 0x00, 0x08, 0x00, 0x07, 0x00, 0x0a, 0x00, 
	0x07, 0x00, 0x06, 0x00, 0x07, 0x00, 0x05, 0x00, 
	0x04, 0x00, 0x05, 0x00, 0x01, 0x00, 0x06, 0x00, 
	0x09, 0x00, 0x09, 0x00, 0x07, 0x00, 0x01, 0x00, 
	0x04, 0x00, 0x05, 0x00, 0x08, 0x00, 0x07, 0x00, 
	0x04, 0x00, 0x04, 0x00, 0xff, 0xff, 0xff, 0xff, 
	0x01, 0x00, 0xfe, 0xff, 0xfc, 0xff, 0xfc, 0xff, 
	0xfc, 0xff, 0xfd, 0xff, 0xfb, 0xff, 0xfc, 0xff, 
	0xfd, 0xff, 0xfd, 0xff, 0xfb, 0xff, 0xf7, 0xff, 
	0xf4, 0xff, 0xf3, 0xff, 0xf2, 0xff, 0xf6, 0xff, 
	0xf7, 0xff, 0xfa, 0xff, 0xfa, 0xff, 0xfa, 0xff, 
	0xfd, 0xff, 0x01, 0x00, 0x04, 0x00, 0x06, 0x00, 
	0x06, 0x00, 0x07, 0x00, 0x0b, 0x00, 0x0a, 0x00, 
	0x08, 0x00, 0x05, 0x00, 0x06, 0x00, 0x06, 0x00, 
	0x04, 0x00, 0x02, 0x00, 0x00, 0x00, 0xfd, 0xff, 
	0xfd, 0xff, 0xf9, 0xff, 0xfb, 0xff, 0xf6, 0xff, 
	0xf9, 0xff, 0xf5, 0xff, 0xf1, 0xff, 0xf0, 0xff, 
	0xee, 0xff, 0xef, 0xff, 0xf2, 0xff, 0xf4, 0xff, 
	0xf7, 0xff, 0xfa, 0xff, 0xfc, 0xff, 0xfb, 0xff, 
	0xf8, 0xff, 0xf8, 0xff, 0xf7, 0xff, 0xf9, 0xff, 
	0xf8, 0xff, 0xf5, 0xff, 0xf7, 0xff, 0xf7, 0xff, 
	0xf9, 0xff, 0xf9, 0xff, 0xfb, 0xff, 0xf7, 0xff, 
	0xf6, 0xff, 0xfa, 0xff, 0xfa, 0xff, 0xff, 0xff, 
	0x01, 0x00, 0x01, 0x00, 0x05, 0x00, 0x07, 0x00, 
	0x0a, 0x00, 0x0a, 0x00, 0x0a, 0x00, 0x09, 0x00, 
	0x09, 0x00, 0x0a, 0x00, 0x06, 0x00, 0x07, 0x00, 
	0x02, 0x00, 0x08, 0x00, 0x06, 0x00, 0x22, 0x00, 
	0x4e, 0x00, 0x12, 0x00, 0xec, 0xff, 0xf3, 0xff, 
	0xf8, 0xff, 0xfa, 0xff, 0xfa, 0xff, 0x03, 0x00, 
	0x09, 0x00, 0x0c, 0x00, 0x0c, 0x00, 0x0e, 0x00, 
	0x0a, 0x00, 0x0b, 0x00, 0x07, 0x00, 0x05, 0x00, 
	0x07, 0x00, 0x07, 0x00, 0x04, 0x00, 0x01, 0x00, 
	0x02, 0x00, 0x03, 0x00, 0x03, 0x00, 0xfe, 0xff, 
	0xfc, 0xff, 0xfb, 0xff, 0xf7, 0xff, 0xf8, 0xff, 
	0xfb, 0xff, 0xf8, 0xff, 0xf7, 0xff, 0xf7, 0xff, 
	0xfc, 0xff, 0xfb, 0xff, 0xfa, 0xff, 0xfb, 0xff, 
	0xfa, 0xff, 0xfb, 0xff, 0xfc, 0xff, 0xfb, 0xff, 
	0xfe, 0xff, 0xfc, 0xff, 0xfb, 0xff, 0xfa, 0xff, 
	0xf7, 0xff, 0xfa, 0xff, 0xf8, 0xff, 0xf8, 0xff, 
	0xfc, 0xff, 0xfb, 0xff, 0xfe, 0xff, 0x00, 0x00, 
	0xff, 0xff, 0xfd, 0xff, 0xfb, 0xff, 0xff, 0xff, 
	0xff, 0xff, 0xfb, 0xff, 0xfc, 0xff, 0xfb, 0xff, 
	0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x04, 0x00, 
	0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 
	0x01, 0x00, 0x03, 0x00, 0x01, 0x00, 0xfe, 0xff, 
	0xfc, 0xff, 0xff, 0xff, 0x01, 0x00, 0x02, 0x00, 
	0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 0x00, 
	0x04, 0x00, 0x04, 0x00, 0x06, 0x00, 0x04, 0x00, 
	0x00, 0x00, 0xfe, 0xff, 0xfe, 0xff, 0xfc, 0xff, 
	0x00, 0x00, 0xff, 0xff, 0xfd, 0xff, 0x00, 0x00, 
	0x02, 0x00, 0x02, 0x00, 0x07, 0x00, 0x0c, 0x00, 
	0x07, 0x00, 0x07, 0x00, 0x06, 0x00, 0x05, 0x00, 
	0x06, 0x00, 0x07, 0x00, 0x07, 0x00, 0x06, 0x00, 
	0x09, 0x00, 0x0a, 0x00, 0x0a, 0x00, 0x08, 0x00, 
	0x13, 0x00, 0x4a, 0x00, 0x2e, 0x00, 0xf2, 0xff, 
	0xf4, 0xff, 0xf8, 0xff, 0xff, 0xff, 0x00, 0x00, 
	0x03, 0x00, 0xfe, 0xff, 0x02, 0x00, 0x05, 0x00, 
	0x03, 0x00, 0x03, 0x00, 0x05, 0x00, 0x03, 0x00, 
	0x02, 0x00, 0x04, 0x00, 0x14, 0x00, 0x4b, 0x00, 
	0x29, 0x00, 0xec, 0xff, 0xee, 0xff, 0xed, 0xff, 
	0xf3, 0xff, 0xf6, 0xff, 0xf8, 0xff, 0xf9, 0xff, 
	0xfd, 0xff, 0xfc, 0xff, 0xfc, 0xff, 0x01, 0x00, 
	0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0xff, 0xff, 
	0x02, 0x00, 0x09, 0x00, 0x07, 0x00, 0x06, 0x00, 
	0x05, 0x00, 0x03, 0x00, 0x04, 0x00, 0xfd, 0xff, 
	0xfe, 0xff, 0xff, 0xff, 0xfe, 0xff, 0x01, 0x00, 
	0xfd, 0xff, 0xfc, 0xff, 0xff, 0xff, 0x01, 0x00, 
	0x02, 0x00, 0x01, 0x00, 0xff, 0xff, 0xfe, 0xff, 
	0xfe, 0xff, 0xfd, 0xff, 0xfe, 0xff, 0xfc, 0xff, 
	0xfb, 0xff, 0xfb, 0xff, 0xf6, 0xff, 0xf8, 0xff, 
	0xf5, 0xff, 0xf6, 0xff, 0xf8, 0xff, 0xfc, 0xff, 
	0xfe, 0xff, 0xfe, 0xff, 0xfc, 0xff, 0xfb, 0xff, 
	0xfd, 0xff, 0xfb, 0xff, 0xfc, 0xff, 0xfd, 0xff, 
	0xfa, 0xff, 0xfb, 0xff, 0xf9, 0xff, 0xfa, 0xff, 
	0xfa, 0xff, 0xfd, 0xff, 0xfe, 0xff, 0xff, 0xff, 
	0x03, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 
	0x02, 0x00, 0x02, 0x00, 0x01, 0x00, 0x03, 0x00, 
	0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x00, 0x00, 
	0x02, 0x00, 0x00, 0x00, 0xfc, 0xff, 0xfd, 0xff, 
	0xfa, 0xff, 0xf9, 0xff, 0xfa, 0xff, 0xf9, 0xff, 
	0xf5, 0xff, 0xf8, 0xff, 0xfa, 0xff, 0xf8, 0xff, 
	0xf9, 0xff, 0xf9, 0xff, 0xf8, 0xff, 0xfc, 0xff, 
	0xfb, 0xff, 0xf9, 0xff, 0xfb, 0xff, 0xff, 0xff, 
	0xfe, 0xff, 0xfd, 0xff, 0xfe, 0xff, 0xfb, 0xff, 
	0xfc, 0xff, 0x01, 0x00, 0xfd, 0xff, 0xfd, 0xff, 
	0xfc, 0xff, 0x00, 0x00, 0x00, 0x00, 0xfe, 0xff, 
	0xfd, 0xff, 0xfe, 0xff, 0xfd, 0xff, 0xfe, 0xff, 
	0x02, 0x00, 0x03, 0x00, 0x03, 0x00, 0x02, 0x00, 
	0x00, 0x00, 0x0d, 0x00, 0x4b, 0x00, 0x2e, 0x00, 
	0xf3, 0xff, 0x2e, 0x00, 0x1e, 0x00, 0xdd, 0xff, 
	0xdb, 0xff, 0xe8, 0xff, 0xeb, 0xff, 0xee, 0xff, 
	0xf4, 0xff, 0xf8, 0xff, 0xf9, 0xff, 0xfa, 0xff, 
	0xfc, 0xff, 0xf8, 0xff, 0xfa, 0xff, 0xf7, 0xff, 
	0xf6, 0xff, 0xf7, 0xff, 0xf5, 0xff, 0xf6, 0xff, 
	0xf6, 0xff, 0xfa, 0xff, 0xfc, 0xff, 0xfb, 0xff, 
	0xfe, 0xff, 0xff, 0xff, 0x00, 0x00, 0x02, 0x00, 
	0x00, 0x00, 0x02, 0x00, 0x05, 0x00, 0x04, 0x00, 
	0x07, 0x00, 0x04, 0x00, 0x09, 0x00, 0x0d, 0x00, 
	0x0c, 0x00, 0x10, 0x00, 0x13, 0x00, 0x11, 0x00, 
	0x0d, 0x00, 0x09, 0x00, 0x08, 0x00, 0x07, 0x00, 
	0x08, 0x00, 0x09, 0x00, 0x05, 0x00, 0x04, 0x00, 
	0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 
	0x09, 0x00, 0x05, 0x00, 0x06, 0x00, 0x05, 0x00, 
	0x01, 0x00, 0x01, 0x00, 0xff, 0xff, 0xff, 0xff, 
	0x00, 0x00, 0xff, 0xff, 0xfd, 0xff, 0xfc, 0xff, 
	0xfd, 0xff, 0xf7, 0xff, 0xf6, 0xff, 0xf8, 0xff, 
	0xf6, 0xff, 0xf8, 0xff, 0xf7, 0xff, 0xfb, 0xff, 
	0xf7, 0xff, 0xf3, 0xff, 0xf6, 0xff, 0xf4, 0xff, 
	0xf7, 0xff, 0xf0, 0xff, 0xf9, 0xff, 0xee, 0xff, 
	0x1c, 0x00, 0x58, 0x00, 0x50, 0x00, 0x53, 0x00, 
	0x48, 0x00, 0x45, 0x00, 0x3c, 0x00, 0x37, 0x00, 
	0x3a, 0x00, 0xf3, 0xff, 0xd5, 0xff, 0xe3, 0xff, 
	0xde, 0xff, 0xe3, 0xff, 0xe3, 0xff, 0xe8, 0xff, 
	0xe8, 0xff, 0xea, 0xff, 0xeb, 0xff, 0xec, 0xff, 
	0xee, 0xff, 0xee, 0xff, 0xf1, 0xff, 0xf1, 0xff, 
	0xf2, 0xff, 0xf0, 0xff, 0xf5, 0xff, 0xf7, 0xff, 
	0xf5, 0xff, 0xf6, 0xff, 0xfc, 0xff, 0xfa, 0xff, 
	0xf5, 0xff, 0xf8, 0xff, 0xf8, 0xff, 0xff, 0xff, 
	0xfc, 0xff, 0xf9, 0xff, 0xfa, 0xff, 0xfd, 0xff, 
	0xfb, 0xff, 0xfa, 0xff, 0xf7, 0xff, 0x02, 0x00, 
	0xfd, 0xff, 0x28, 0x00, 0x47, 0x00, 0x01, 0x00, 
	0xf0, 0xff, 0xfb, 0xff, 0xfa, 0xff, 0xff, 0xff, 
	0x05, 0x00, 0x04, 0x00, 0x08, 0x00, 0x0a, 0x00, 
	0x0c, 0x00, 0x0c, 0x00, 0x09, 0x00, 0x09, 0x00, 
	0x08, 0x00, 0x07, 0x00, 0x05, 0x00, 0x06, 0x00, 
	0x06, 0x00, 0x08, 0x00, 0x0c, 0x00, 0x0b, 0x00, 
	0x0f, 0x00, 0x0f, 0x00, 0x0e, 0x00, 0x10, 0x00, 
	0x11, 0x00, 0x10, 0x00, 0x14, 0x00, 0x17, 0x00, 
	0x10, 0x00, 0x0d, 0x00, 0x07, 0x00, 0x07, 0x00, 
	0x05, 0x00, 0x06, 0x00, 0x04, 0x00, 0x01, 0x00, 
	0xff, 0xff, 0xfc, 0xff, 0xfc, 0xff, 0xfd, 0xff, 
	0x03, 0x00, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 
	0x02, 0x00, 0x02, 0x00, 0x04, 0x00, 0x09, 0x00, 
	0x06, 0x00, 0x07, 0x00, 0x0b, 0x00, 0x0f, 0x00, 
	0x08, 0x00, 0x05, 0x00, 0x09, 0x00, 0x0b, 0x00, 
	0x0b, 0x00, 0x0c, 0x00, 0x0e, 0x00, 0x0c, 0x00, 
	0x09, 0x00, 0x0a, 0x00, 0x0f, 0x00, 0x0b, 0x00, 
	0x08, 0x00, 0x08, 0x00, 0x09, 0x00, 0x07, 0x00, 
	0x04, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 
	0xff, 0xff, 0x01, 0x00, 0x03, 0x00, 0x06, 0x00, 
	0x0b, 0x00, 0x08, 0x00, 0x06, 0x00, 0x07, 0x00, 
	0x04, 0x00, 0x02, 0x00, 0x03, 0x00, 0x04, 0x00, 
	0x01, 0x00, 0x00, 0x00, 0x05, 0x00, 0x04, 0x00, 
	0x01, 0x00, 0x01, 0x00, 0xfc, 0xff, 0xf9, 0xff, 
	0xfb, 0xff, 0xfa, 0xff, 0xf8, 0xff, 0xf8, 0xff, 
	0xfa, 0xff, 0xfa, 0xff, 0xf7, 0xff, 0xf5, 0xff, 
	0xf6, 0xff, 0xf6, 0xff, 0xf3, 0xff, 0xf5, 0xff, 
	0xf5, 0xff, 0xf8, 0xff, 0xf7, 0xff, 0xf4, 0xff, 
	0xf7, 0xff, 0xf5, 0xff, 0xf9, 0xff, 0xfa, 0xff, 
	0xf8, 0xff, 0xf5, 0xff, 0xf5, 0xff, 0xf4, 0xff, 
	0xf7, 0xff, 0xf7, 0xff, 0xf5, 0xff, 0xf9, 0xff, 
	0xf9, 0xff, 0xf8, 0xff, 0xf8, 0xff, 0xfb, 0xff, 
	0xfc, 0xff, 0xfc, 0xff, 0xfe, 0xff, 0xfd, 0xff, 
	0xfd, 0xff, 0x01, 0x00, 0xff, 0xff, 0xfe, 0xff, 
	0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x00, 
	0x02, 0x00, 0x01, 0x00, 0x05, 0x00, 0x07, 0x00, 
	0x05, 0x00, 0x01, 0x00, 0xfb, 0xff, 0xfc, 0xff, 
	0xfa, 0xff, 0xf7, 0xff, 0xf5, 0xff, 0xf0, 0xff, 
	0xf2, 0xff, 0xf6, 0xff, 0xf6, 0xff, 0xf9, 0xff, 
	0xf8, 0xff, 0xf7, 0xff, 0xf8, 0xff, 0xf9, 0xff, 
	0xf8, 0xff, 0xfb, 0xff, 0xf9, 0xff, 0xf8, 0xff, 
	0xfc, 0xff, 0xfb, 0xff, 0xfe, 0xff, 0xfd, 0xff, 
	0x01, 0x00, 0xfe, 0xff, 0xfd, 0xff, 0xff, 0xff, 
	0xfe, 0xff, 0x01, 0x00, 0xff, 0xff, 0x02, 0x00, 
	0x03, 0x00, 0x03, 0x00, 0x02, 0x00, 0x01, 0x00, 
	0xff, 0xff, 0xfe, 0xff, 0x00, 0x00, 0xfb, 0xff, 
	0x01, 0x00, 0x06, 0x00, 0x06, 0x00, 0x05, 0x00, 
	0x02, 0x00, 0x05, 0x00, 0x03, 0x00, 0x01, 0x00, 
	0x01, 0x00                                      
];

LITTLE_STARS_KEY = [0xDD, 0xF1, 0x01, 0x81] #[0xB8, 0x48, 0x90, 0x00] #0xB8489000

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

HEADER_FMT = '>BBH' #-> Big Endian( unsigned Byte, unsigned Byte, unsigned Short )

#def listen(addr):

QUIC_HEADER_FMT = '>BB'
	

def lan_search():
	#big endian
	#magic number
	#msg code
	#16 bits (msg size)
	#msg = struct.pack(HEADER_FMT, PPPP_MAGIC_NUMBER, MSG_LAN_SEARCH, 0) #pppp
	msg = struct.pack(QUIC_HEADER_FMT, MSG_LAN_SEARCH, 0x67) #quic
	msg_notify = struct.pack(QUIC_HEADER_FMT, MSG_LAN_SEARCH, 0x66)
	msg_ready = struct.pack(QUIC_HEADER_FMT, MSG_P2P_RDY, 0x76)

	s = socket(AF_INET, SOCK_DGRAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	#s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

	s.bind(('', 0))
	print(s.getsockname())

	size = s.sendto(msg, ('192.168.4.153', QUIC_PORT))
	print(size)
	size = s.sendto(msg_notify, ('192.168.4.153', QUIC_PORT))
	print(size)

	#then confirm with MSG_P2P_RDY (found in wireshark session between android emu and camera on wifidirect)
	size = s.sendto(msg_ready, ('192.168.4.153', QUIC_RDY_PORT))
	print(size)

	#now it should begin spamming us with packets...

	while True:     
		try:
			#print("trying")
			(buff, rinfo) = s.recvfrom(4096)
			print(rinfo)
			print(buff)
			#logging.debug('Data from %s: %s', (rinfo, buff))
		except socket.timeout as e:
			print("socket timeout")
	s.close()

def hello():
	msg = struct.pack(HEADER_FMT, PPPP_MAGIC_NUMBER, MSG_HELLO, 0)
	s = socket(AF_INET, SOCK_DGRAM)
	s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	size = s.sendto(msg, ('192.168.4.153', HELLO_PORT))
	print(size)
	s.close()

def encrypt(buf, key):
	prev_byte = 0
	for i in range(0, len(buf)):
		key_idx = ( key[prev_byte & 0x03] + prev_byte ) & 0xFF
		buf[i] = buf[i] ^ KEY_TABLE[key_idx]
		prev_byte = buf[i]
	return buf

def decrypt(buf, key):
	prev_byte = 0
	for i in range(0, len(buf)):
		key_idx = ( key[prev_byte & 0x03] + prev_byte ) & 0xFF
		prev_byte = buf[i]
		buf[i] = buf[i] ^ KEY_TABLE[key_idx]
	return buf

d = decrypt(TEST_PACKET, LITTLE_STARS_KEY)
#print( ' '.join([hex(i) for i in d]) )

test = bytearray("Hello World!", "ASCII")
#print(test)
e = encrypt(test, LITTLE_STARS_KEY)
#print( ' '.join([hex(i) for i in e]) )
#print(e)
td = decrypt(e, LITTLE_STARS_KEY)
#print(td)
lan_search()
#hello()
