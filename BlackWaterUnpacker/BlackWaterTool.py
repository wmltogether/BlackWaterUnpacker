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
class Base:
    def __init__(self , baseStream):
        self.base_stream = baseStream

    def ReadByte(self):
        return self.base_stream.read(1)

    def ReadBytes(self , count):
        return self.base_stream.read(count)

    def ReadChar(self):
        return ord(self.base_stream.read(1))

    def ReadChars(self , count):
        return struct.unpack('%dB' , self.base_steam.read(count))

    def ReadInt16(self):
        return struct.unpack('h' , self.base_stream.read(2))[0]

    def ReadInt32(self):
        return struct.unpack('i' , self.base_stream.read(4))[0]

    def ReadInt64(self):
        return struct.unpack('q' , self.base_stream.read(8))[0]

    def ReadUInt16(self):
        return struct.unpack('H' , self.base_stream.read(2))[0]

    def ReadUInt32(self):
        return struct.unpack('I' , self.base_stream.read(4))[0]

    def ReadUInt64(self):
        return struct.unpack('Q' , self.base_stream.read(8))[0]

    def ReadFloat(self):
        return struct.unpack('f' , self.base_stream.read(4))[0]

    def ReadBEInt16(self):
        return struct.unpack('>h' , self.base_stream.read(2))[0]

    def ReadBEInt32(self):
        return struct.unpack('>i' , self.base_stream.read(4))[0]

    def ReadBEInt64(self):
        return struct.unpack('>q' , self.base_stream.read(8))[0]

    def ReadBEUInt16(self):
        return struct.unpack('>H' , self.base_stream.read(2))[0]

    def ReadBEUInt32(self):
        return struct.unpack('>I' , self.base_stream.read(4))[0]

    def ReadBEUInt64(self):
        return struct.unpack('>Q' , self.base_stream.read(8))[0]

    def GetString(self):
        string = ""
        while True:
            char = self.base_stream.read(1)
            if ord(char) == 0:
                break
            string += char
        return string

class PAK:
    def __init__(self):
        self.pak_name = "archive00.lnk"
        self.dest_folder = "archive00_lnk"
        self.patch_folder = "patch"
        self.need_patch_name = "import\\archive00.lnk"
        self.elf_name = "import\\main.elf"

    def getDict(self):
        fp = open("dpfilelist.txt" , "rb")
        lines = fp.readlines()
        dict = {}
        for line in lines:
            if "=" in line:
                file_id = int(line.split("=")[0])
                file_name = line.split("=")[1].replace("\r\n" , "")
                dict[file_name] = file_id
        fp.close()
        return dict

    def getFileInfo(self , input_name , output_name):
        fp = open(input_name , 'rb')
        dest = open(output_name , "wb")
        fStream = Base(fp)
        idstring = fp.read(4)
        DUMMY = fStream.ReadBEUInt32()
        FILE_NUMS = fStream.ReadBEInt32()
        DUMMY_OFF = fStream.ReadBEInt32()
        INFO_OFF = fStream.ReadBEInt32()
        ARCHIVE_NAME = fStream.ReadBEInt32()
        NAMES_OFF = fStream.ReadBEInt32()
        fp.seek(INFO_OFF)
        tmp = []
        for i in xrange(FILE_NUMS):
            FILE_ID = fStream.ReadBEInt64()
            NAME_OFF = fStream.ReadBEInt32()
            pos = fp.tell()
            fp.seek(NAME_OFF)
            NAME = fStream.GetString()
            fp.seek(pos)
            tmp.append((FILE_ID , NAME))
            dest.write("%d=%s\r\n"%(FILE_ID , NAME))
        fp.close()
        return tmp

    def unpack(self):
        log = open("FILE_LBA.txt" , "wb")
        log2 = open("LNK.txt" , "wb")
        tmp = self.getFileInfo("lfm_order.bin" ,"dpfilelist.txt")
        fp = open(self.pak_name , "rb")
        fStream = Base(fp)
        sig = fp.read(4)
        ZERO = fStream.ReadBEUInt64()
        FILE_NUMS = fStream.ReadBEUInt32()
        ARCHIVE_SIZE = fStream.ReadBEUInt64()
        ALIGN = fStream.ReadBEUInt64()
        for i in xrange(FILE_NUMS):
            #print("%s//%s"%(self.dest_folder , tmp[i][1]))
            dest_dir = os.path.split("%s//%s"%(self.dest_folder , tmp[i][1]))[0]
            if not os.path.exists(dest_dir):os.makedirs(dest_dir)

            OFFSET = fStream.ReadBEUInt64()
            SIZE = fStream.ReadBEUInt64()
            ZSIZE = fStream.ReadBEUInt64()
            comFlag = fStream.ReadBEUInt64()
            #print("%08x\t%08x\t%08x\t"%(OFFSET,SIZE,ZSIZE))
            BACK_OFF = fp.tell()
            if comFlag != 1:
                print("ERROR:%08x"%OFFSET)
            else:
                fp.seek(OFFSET)
                MEMORY_FILE = StringIO()
                MEMORY_FILE.seek(0)
                tmp_size = 0
                while tmp_size != ZSIZE:
                    CHUNK_ZSIZE = fStream.ReadBEUInt32()
                    tmp_size += 4
                    tmp_offset = fp.tell()
                    if CHUNK_ZSIZE & 0x8000:
                        # Compressed
                        CHUNK_ZSIZE = CHUNK_ZSIZE & 0x7fff
                        MEMORY_FILE.write(zlib.decompress(fp.read(CHUNK_ZSIZE)))
                    else:
                        MEMORY_FILE.write(fp.read(CHUNK_ZSIZE))
                    tmp_size += CHUNK_ZSIZE
                    tmp_offset += CHUNK_ZSIZE
                    fp.seek(tmp_offset)
                    padding = (0x10 - (tmp_offset % 0x10))%0x10
                    tmp_size += padding
                    fp.seek(padding,1)
                mdata = MEMORY_FILE.getvalue()
                dest = open("%s//%s"%(self.dest_folder , tmp[i][1]) , "wb")
                dest.write(mdata)
                log.write("%s,%08x\r\n"%(tmp[i][1] , len(mdata)))
                log2.write("%08x\r\n"%(len(mdata)))
                dest.close()
            fp.seek(BACK_OFF)
        fp.close()
        log.close()
        log2.close()

    def compress_block(self , data):
        tmpBuffer = StringIO()
        destBuffer = StringIO()
        destBuffer.seek(0)
        tmpBuffer.write(data)
        tmpBuffer.seek(0)
        comFlag = False
        block_nums = int(math.ceil(float(len(data)/float(0x800*8))))
        for i in xrange(block_nums):
            data = tmpBuffer.read(0x800*8)
            if data <= 0x100:
                Z_DATA = data
                destBuffer.write(struct.pack(">I" , (len(Z_DATA))))
            else:
                Z_DATA = zlib.compress(data)
                destBuffer.write(struct.pack(">I" , (len(Z_DATA) ^ 0x8000)))
            destBuffer.write(Z_DATA)
            tmp_offset = destBuffer.tell()
            padding = (0x10 - (tmp_offset % 0x10))%0x10
            destBuffer.write("\x00" * padding)
        cmp_block = destBuffer.getvalue()
        return cmp_block



    def inject(self):
        dict = self.getDict()
        fl = dir_fn(self.patch_folder)
        dest = open(self.need_patch_name , "rb+")
        elf_file = open(self.elf_name , "rb+")
        fStream = Base(dest)
        for fn in fl:
            pname = fn[len(self.patch_folder):]
            pname = pname.replace("\\" ,"/")
            if pname in dict:
                print("patching :%s"%pname)
                file_id = dict[pname]
                pfile = open(fn , "rb")
                pdata = pfile.read()
                dsize = len(pdata)
                zdata = self.compress_block(pdata)
                pfile.close()
                index_offset = 0x20 + file_id * 0x20
                dest.seek(index_offset)
                OFFSET = fStream.ReadBEUInt64()
                SIZE = fStream.ReadBEUInt64()
                ZSIZE = fStream.ReadBEUInt64()
                comFlag = fStream.ReadBEUInt64()
                if math_sector_align(ZSIZE,0x800) <= math_sector_align(ZSIZE,0x800):
                    #print("USE INJECT METHOD")
                    dest.seek(OFFSET)
                    dest.write(zdata)
                    tmp_offset = OFFSET + len(zdata)
                    padding = (0x800 - (tmp_offset % 0x800))%0x800
                    dest.write("\x00" * padding)
                    dest.seek(index_offset)
                    dest.write(struct.pack(">Q" , OFFSET))
                    dest.write(struct.pack(">Q" , dsize))
                    dest.write(struct.pack(">Q" , len(zdata)))
                    if 0 <= file_id <= 1409:
                        elf_file.seek(file_id * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    elif 1410 <= file_id <= 2526:
                        elf_file.seek((file_id + 76) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    elif 2527 <= file_id <= 2643:
                        elf_file.seek((file_id + 356) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    else:

                        elf_file.seek((file_id + 358) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                else:
                    #print("USE EXTEND METHOD")
                    dest.seek(0,2)
                    i_offset = dest.tell()
                    dest.write(zdata)
                    tmp_offset = OFFSET + len(zdata)
                    padding = (0x800 - (tmp_offset % 0x800))%0x800
                    dest.write("\x00" * padding)
                    dest.seek(index_offset)
                    dest.write(struct.pack(">Q" , i_offset))
                    dest.write(struct.pack(">Q" , dsize))
                    dest.write(struct.pack(">Q" , len(zdata)))
                    if 0 <= file_id <= 1409:
                        elf_file.seek(file_id * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    elif 1410 <= file_id <= 2526:
                        elf_file.seek((file_id + 76) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    elif 2527 <= file_id <= 2643:
                        elf_file.seek((file_id + 356) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
                    else:
                        elf_file.seek((file_id + 358) * 8 + 0x015A0B3B)
                        elf_file.write(struct.pack(">I" , dsize))
        dest.seek(0,2)
        end_offset = dest.tell()
        dest.seek(0x10,0)
        dest.write(struct.pack(">Q" , end_offset))
        dest.close()
        elf_file.close()
        

pak = PAK()
pak.unpack()
#pak.inject()
fixRPX("import\\main.elf", "import\\backup.rpx" , "import\\lens5_cafe.rpx")
os.system("pause")
