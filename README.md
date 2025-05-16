# OS Lab 4 - Archive Extraction Tool

A Python utility to parse, decrypt, and extract files from custom binary archives transmitted between VMs.

## Features
- Supports both little-endian and big-endian archives
- Handles compressed (zlib/LZMA) and encrypted (Fernet) files
- Automatic endianness detection
- Robust error handling and logging

## Requirements
- Python 3.8+
- VirtualBox (for network setup)

## Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/os-lab4.git
cd os-lab4
```

2. Install dependencies:
```bash
pip install cryptography zlib lzma
```

## Usage
Basic command:
```bash
python archextract.py -i <input_file> -o <output_dir> [-v LEVEL]
```

Options:
- `-i`: Input file (required)
- `-o`: Output directory (default: ./extracted)
- `-v`: Verbosity level (0-2, default: 0)

Examples:
```bash
# Extract with debug output
python script.py -i archive_le.hex -o ./output -v 2

# Quiet mode (errors only)
python script.py -i archive_be_with_offsets.txt
```

## Archive Format
Archives contain:
1. Header (5 bytes):
   - Magic number: 'ARCH' (big-endian) or 'HCRA' (little-endian)
   - Version: 0x01 or 0x02

2. File entries:
   - Filename (UTF-8)
   - Original/processed sizes
   - Processing method (0x00-0x03)
   - Data (compressed/encrypted)
