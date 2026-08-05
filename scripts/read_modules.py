import struct

dump_path = r'C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.48064.dmp'
with open(dump_path, 'rb') as f:
    header = f.read(32)

num_streams = struct.unpack('<I', header[8:12])[0]
stream_dir_rva = struct.unpack('<I', header[12:16])[0]

with open(dump_path, 'rb') as f:
    f.seek(stream_dir_rva)
    module_list_rva = None
    for i in range(num_streams):
        stream_type = struct.unpack('<I', f.read(4))[0]
        data_size = struct.unpack('<I', f.read(4))[0]
        rva = struct.unpack('<I', f.read(4))[0]
        if stream_type == 4:  # ModuleListStream
            module_list_rva = rva
            module_list_size = data_size

    if module_list_rva:
        f.seek(module_list_rva)
        num_modules = struct.unpack('<I', f.read(4))[0]
        print('Number of modules:', num_modules)
        # Each MINIDUMP_MODULE is 108 bytes
        for i in range(min(num_modules, 5)):
            base = struct.unpack('<Q', f.read(8))[0]
            size = struct.unpack('<I', f.read(4))[0]
            checksum = struct.unpack('<I', f.read(4))[0]
            timestamp = struct.unpack('<I', f.read(4))[0]
            name_rva = struct.unpack('<I', f.read(4))[0]
            # Skip rest of module entry (76 bytes)
            f.read(76)
            # Read name
            pos = f.tell()
            f.seek(name_rva)
            name_len = struct.unpack('<I', f.read(4))[0]
            name = f.read(name_len).decode('utf-16-le', errors='replace').rstrip('\x00')
            print('Module %d: base=0x%016X size=%d name=%s' % (i, base, size, name))
            f.seek(pos)
