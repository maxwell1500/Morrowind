import struct, os, glob
dumps = sorted(glob.glob(r'C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.*.dmp'), key=os.path.getmtime, reverse=True)
for dump_path in dumps[:8]:
    try:
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
                    f.read(4)
                    f.read(4)
                    exception_code = struct.unpack('<I', f.read(4))[0]
                    f.read(4)
                    f.read(8)
                    exception_address = struct.unpack('<Q', f.read(8))[0]
                    num_params = struct.unpack('<I', f.read(4))[0]
                    f.read(4)
                    params = []
                    for j in range(min(num_params, 2)):
                        params.append(struct.unpack('<Q', f.read(8))[0])
                    fname = os.path.basename(dump_path)
                    mtime = os.path.getmtime(dump_path)
                    import datetime
                    ts = datetime.datetime.fromtimestamp(mtime).strftime('MM-dd HH:mm')
                    print('%s | addr=0x%016X offset=0x%X access=%d fault=0x%016X' % (ts.replace('M','%m'), exception_address, exception_address - 0x140000000, params[0] if params else -1, params[1] if len(params)>1 else 0))
                    break
    except Exception as e:
        print('Error reading %s: %s' % (os.path.basename(dump_path), e))
