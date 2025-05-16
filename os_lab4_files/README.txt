OS Laboratory 4 - Test Archives
=============================

This directory contains test archives for the OS Lab 4 assignment.

Files included:
- archive_le.hex: Little-endian archive in plain hex format
- archive_be.hex: Big-endian archive in plain hex format
- archive_*_with_offsets.txt: Archives with xxd-style offsets and ASCII

Archive Format:
1. Header:
   - Magic number (4 bytes): 0x41524348 ('ARCH')
   - Version (1 byte): 0x01

2. For each file entry:
   - Name length (4 bytes)
   - File name (variable length)
   - Original size (8 bytes)
   - Processed size (8 bytes)
   - Processing method (1 byte):
     * 0x00: No processing
     * 0x01: zlib compression
     * 0x02: LZMA compression
     * 0x03: Fernet encryption
   - For encrypted files: the first 44 bytes contain the encryption key
   - Processed data (variable length)

Note: The binary .bin files are included for reference only.
Your implementation should work with the .hex and .txt files.
