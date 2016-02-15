# -*- coding: utf-8 -*-
import os,codecs,struct
import zlib
import math
from cStringIO import StringIO
def fixRPX(elf_name , rpx_name , dest_rpx_name):
    fp = open(elf_name , "rb")
    fp.seek(21980899)
    data = fp.read(942988)
    fp.close()
    zdata = zlib.compress(data)
    if zdata[:2] == "\x78\x9c":
        print("compressing .data chunk:ok")
        o_rpx_file = open(rpx_name , "rb")
        o_rpx_data = o_rpx_file.read()
        o_rpx_file.close()
        rpx_buffer = StringIO()
        rpx_buffer.write(o_rpx_data)
        rpx_buffer.seek(0)
        rpx_buffer.seek(0x4ea00)
        if len(zdata) <= (0x771c0 - 0x4ea00 - 4):
            print("mathing rpx space :ok")
            rpx_buffer.write(struct.pack(">I" , len(data)))
            rpx_buffer.write(zdata)
            tmp = rpx_buffer.tell()
            print("writing pad :ok")
            rpx_buffer.write("\x00" * (0x771c0 - tmp))
            rpx_buffer.seek(0x11c)
            rpx_buffer.write(struct.pack(">I" , len(zdata) + 4))
        dest = open(dest_rpx_name , "wb")
        dest.write(rpx_buffer.getvalue())
        dest.close()
    else:
        print("errpr:got wrong zlib header")

def math_sector_align(count,align):
    return int(math.ceil(float(count)/ float(align)))

def dir_fn(adr):
    dirlst=[]
    for root,dirs,files in os.walk(adr):
        for name in files:
            adrlist=os.path.join(root, name)
            dirlst.append(adrlist)
    return dirlst
