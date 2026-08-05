import struct
import os
import glob
import datetime

dumps = sorted(glob.glob(r"C:\Users\max\AppData\Local\CrashDumps\CreationKit.exe.*.dmp"), key=os.path.getmtime, reverse=True)
for dump_path in dumps[:3]:
    try:
        with open(dump_path, "rb") as f:
            header = f.read(32)
        num_streams = struct.unpack("<I", header[8:12])[0]
        stream_dir_rva = struct.unpack("<I", header[12:16])[0]
        with open(dump_path, "rb") as f:
            f.seek(stream_dir_rva)
            for i in range(num_streams):
                stream_type = struct.unpack("<I", f.read(4))[0]
                data_size = struct.unpack("<I", f.read(4))[0]
                rva = struct.unpack("<I", f.read(4))[0]
                if stream_type == 6:
                    f.seek(rva)
                    f.read(4)  # thread id
                    f.read(4)  # padding
                    exception_code = struct.unpack("<I", f.read(4))[0]
                    f.read(4)   # flags
                    f.read(8)   # exception record
                    exception_address = struct.unpack("<Q", f.read(8))[0]
                    num_params = struct.unpack("<I", f.read(4))[0]
                    f.read(4)   # reserved
                    params = []
                    for j in range(min(num_params, 2)):
                        params.append(struct.unpack("<Q", f.read(8))[0])
                    mtime = os.path.getmtime(dump_path)
                    ts = datetime.datetime.fromtimestamp(mtime).strftime("%H:%M:%S")
                    offset = exception_address - 0x140000000
                    fault = params[1] if len(params) > 1 else 0
                    print("%s offset=0x%X fault=0x%016X" % (ts, offset, fault))
                    break
    except Exception as e:
        print("Error: %s" % e)