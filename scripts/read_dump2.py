import struct

dump_path = r'C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.48064.dmp'
with open(dump_path, 'rb') as f:
    data = f.read(4096)

num_streams = struct.unpack('<I', data[8:12])[0]
stream_dir_rva = struct.unpack('<I', data[12:16])[0]

with open(dump_path, 'rb') as f:
    f.seek(stream_dir_rva)
    for i in range(num_streams):
        stream_type = struct.unpack('<I', f.read(4))[0]
        data_size = struct.unpack('<I', f.read(4))[0]
        rva = struct.unpack('<I', f.read(4))[0]
        if stream_type == 6:  # ExceptionStream
            pos = f.tell()
            f.seek(rva)
            thread_id = struct.unpack('<I', f.read(4))[0]
            # Alignment padding (4 bytes)
            f.read(4)
            # EXCEPTION_RECORD (64-bit: 152 bytes)
            exception_code = struct.unpack('<I', f.read(4))[0]
            exception_flags = struct.unpack('<I', f.read(4))[0]
            exception_record = struct.unpack('<Q', f.read(8))[0]
            exception_address = struct.unpack('<Q', f.read(8))[0]
            num_params = struct.unpack('<I', f.read(4))[0]
            reserved = struct.unpack('<I', f.read(4))[0]
            print('Exception thread ID: %d' % thread_id)
            print('Exception code: 0x%08X' % exception_code)
            print('Exception address: 0x%016X' % exception_address)
            print('Num params: %d' % num_params)
            for j in range(min(num_params, 5)):
                param = struct.unpack('<Q', f.read(8))[0]
                print('  Param %d: 0x%016X' % (j, param))
            f.seek(pos)
            break
