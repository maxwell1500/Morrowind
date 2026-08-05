import struct
nam0 = bytes.fromhex('002080c500007ac4')
nam9 = bytes.fromhex('0000484300001645')
print('NAM0:', struct.unpack('<ff', nam0))
print('NAM9:', struct.unpack('<ff', nam9))
