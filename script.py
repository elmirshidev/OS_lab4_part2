import argparse
import os
import struct
import binascii
from cryptography.fernet import Fernet
import zlib
import lzma
import base64
import logging

def parse_xxd_format(hex_lines):
    binary = b''
    for line in hex_lines:
        line = line.strip()
        if ':' in line:
            hex_part = line.split(':', 1)[1].split('  ', 1)[0].replace(' ', '')
            binary += binascii.unhexlify(hex_part)
    return binary

def parse_plain_hex(hex_lines):
    hex_str = ''.join(line.strip() for line in hex_lines)
    return binascii.unhexlify(hex_str)

def detect_hex_format(lines):
    for line in lines:
        if ':' in line:
            return 'xxd'
    return 'plain'

def main():
    parser = argparse.ArgumentParser(description='Extract files from custom archive.')
    parser.add_argument('-i', '--input', required=True, help='Input hexdump file')
    parser.add_argument('-o', '--output', default='./extracted', help='Output directory')
    parser.add_argument('-v', '--verbose', type=int, default=0, choices=[0, 1, 2])
    args = parser.parse_args()

    logging.basicConfig(filename='errors.log', level=logging.ERROR)
    os.makedirs(args.output, exist_ok=True)

    with open(args.input, 'r') as f:
        lines = f.readlines()

    hex_format = detect_hex_format(lines)
    if hex_format == 'xxd':
        binary_data = parse_xxd_format(lines)
    else:
        binary_data = parse_plain_hex(lines)

    # Check magic number and endianness
    magic = binary_data[:4]
    if magic == b'ARCH':
        endian = '>'
    elif magic == b'HCRA':
        endian = '<'
    else:
        raise ValueError("Invalid archive: Magic number not found.")

    version = binary_data[4]
    if version not in [0x01, 0x02]:
        raise ValueError("Unsupported archive version.")

    offset = 5
    metadata = []

    while offset < len(binary_data):
        try:
            # Read name length (4 bytes)
            name_length = struct.unpack(f'{endian}I', binary_data[offset:offset+4])[0]
            offset += 4

            # Read filename
            filename = binary_data[offset:offset+name_length].decode('utf-8')
            offset += name_length

            # Read sizes (8 bytes each)
            original_size = struct.unpack(f'{endian}Q', binary_data[offset:offset+8])[0]
            offset +=8
            processed_size = struct.unpack(f'{endian}Q', binary_data[offset:offset+8])[0]
            offset +=8

            # Read processing method
            method = binary_data[offset]
            offset +=1

            # Read processed data
            processed_data = binary_data[offset:offset+processed_size]
            offset += processed_size

            # Process data
            if method == 0x00:
                data = processed_data
            elif method == 0x01:
                data = zlib.decompress(processed_data)
            elif method == 0x02:
                data = lzma.decompress(processed_data)
            elif method == 0x03:
                if len(processed_data) < 44:
                    raise ValueError("Insufficient data for encryption key.")
                key_b64 = processed_data[:44]

                # 1. Ensure proper URL-safe base64 encoding
                # Replace all '-' with '+' and '_' with '/' (reverse of URL-safe encoding)
                standard_b64 = key_b64.replace(b'-', b'+').replace(b'_', b'/')
                
                # 2. Pad to proper length (44 chars)
                standard_b64 = standard_b64.ljust(44, b'=')


                encrypted_data = processed_data[44:]

                try:
                    key = base64.b64decode(standard_b64)
                except:
                    logging.error(f"Invalid Base64 key for {filename}.")
                    continue
                if len(key) != 32:
                    logging.error(f"Invalid Fernet key length ({len(key)} bytes) for {filename}.")
                    continue
                try:
                    fernet = Fernet(base64.urlsafe_b64encode(key))
                    data = fernet.decrypt(encrypted_data)
                except Exception as e:
                    logging.error(f"Decryption failed for {filename}: {str(e)}")
                    continue
            else:
                logging.error(f"Unknown processing method {method} for {filename}.")
                continue

            # Validate data size
            if len(data) != original_size:
                logging.warning(f"Size mismatch for {filename} (expected {original_size}, got {len(data)}).")

            # Write file
            output_path = os.path.join(args.output, filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)

            # Update metadata
            method_str = ['none', 'zlib', 'LZMA', 'Fernet'][method]
            metadata.append(f"{filename}\t{original_size}\t{processed_size}\t{method_str}")

        except Exception as e:
            logging.error(f"Error at offset {offset}: {str(e)}")
            break  # Exit on critical errors

    # Write metadata
    with open(os.path.join(args.output, 'metadata.txt'), 'w') as f:
        f.write('\n'.join(metadata))

if __name__ == '__main__':
    main()