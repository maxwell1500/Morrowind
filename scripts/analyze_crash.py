import struct
dump_path = r'C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.48064.dmp'
with open(dump_path, 'rb') as f:
    header = f.read(32)
num_streams = struct.unpack('<I', header[8:12])[0]
stream_dir_rva = struct.unpack('<I', header[12:16])[0]
with open(dump_path, 'rb') as f:
    f.seek(stream_dir_rva)
    for i in range(num_streams):
        stream_type = struct.unpack('<I', f.read(4))[0]
        data_size = struct.unpack('<I', f.read(4))[0]
        rva = struct.unpack('<I', f.read(4))[0]
        if stream_type == 6:
            f.seek(rva)
            thread_id = struct.unpack('<I', f.read(4))[0]
            f.read(4)  # padding
            exception_code = struct.unpack('<I', f.read(4))[0]
            exception_flags = struct.unpack('<I', f.read(4))[0]
            exception_record = struct.unpack('<Q', f.read(8))[0]
            exception_address = struct.unpack('<Q', f.read(8))[0]
            num_params = struct.unpack('<I', f.read(4))[0]
            reserved = struct.unpack('<I', f.read(4))[0]
            params = []
            for j in range(min(num_params, 5)):
                params.append(struct.unpack('<Q', f.read(8))[0])
            print('Crash dump: %s' % dump_path)
            print('Exception code: 0x%08X (Access Violation)' % exception_code)
            print('Exception address: 0x%016X' % exception_address)
            print('Access type: %d (0=Read,1=Write)' % params[0] if params else 'unknown')
            print('Faulting memory address: 0x%016X' % params[1] if len(params) > 1 else 'unknown')
            print('Offset from CK base: 0x%X' % (exception_address - 0x140000000))
            break
