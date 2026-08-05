import struct

dump_path = r'C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.48064.dmp'
with open(dump_path, 'rb') as f:
    data = f.read(4096)

# MINIDUMP header
sig = data[:4]
print('Signature:', sig)
version = struct.unpack('<I', data[4:8])[0]
num_streams = struct.unpack('<I', data[8:12])[0]
stream_dir_rva = struct.unpack('<I', data[12:16])[0]
print('Num streams:', num_streams, 'Dir RVA:', stream_dir_rva)

# Read stream directory
with open(dump_path, 'rb') as f:
    f.seek(stream_dir_rva)
    for i in range(min(num_streams, 20)):
        stream_type = struct.unpack('<I', f.read(4))[0]
        data_size = struct.unpack('<I', f.read(4))[0]
        rva = struct.unpack('<I', f.read(4))[0]
        print('Stream %d: type=%d size=%d rva=%d' % (i, stream_type, data_size, rva))
        if stream_type == 6:  # ExceptionStream
            # Read exception stream
            pos = f.tell()
            f.seek(rva)
            thread_id = struct.unpack('<I', f.read(4))[0]
            print('  Exception thread ID:', thread_id)
            # EXCEPTION_RECORD
            exception_code = struct.unpack('<I', f.read(4))[0]
            exception_flags = struct.unpack('<I', f.read(4))[0]
            exception_record = struct.unpack('<Q', f.read(8))[0]
            exception_address = struct.unpack('<Q', f.read(8))[0]
            num_params = struct.unpack('<I', f.read(4))[0]
            reserved = struct.unpack('<I', f.read(4))[0]
            print('  Exception code: 0x%08X' % exception_code)
            print('  Exception address: 0x%016X' % exception_address)
            f.seek(pos)
