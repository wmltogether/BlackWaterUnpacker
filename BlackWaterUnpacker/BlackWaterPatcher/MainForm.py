# -*- coding: utf-8 -*-
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')
clr.AddReference("IronPython")
clr.AddReference("IronPython.Modules")
import os,codecs,struct
import zlib
import math
from cStringIO import StringIO
import System.Windows.Forms
from System.Drawing import *
from System.Windows.Forms import *
import util
from util import *
class PAK:
	def __init__(self):
		self.pak_name = "archive00.lnk"
		self.dest_folder = "archive00_lnk"
		self.patch_folder = "patch"
		self.need_patch_name = "import\\archive00.lnk"
		self.elf_name = "patch\\main.elf"
		self.backup_rpx_name = "patch\\backup.rpx"
		self.dest_rpx_name = "import\\lens5_cafe.rpx"
		self.dict_name = "patch\\dpfilelist.txt"

	def getDict(self):
		fp = open(self.dict_name , "rb")
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
		if not os.path.exists(self.dest_folder):
			os.makedirs(self.dest_folder)
		if not os.path.exists(self.pak_name):
			return None
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
		if not os.path.exists(self.need_patch_name):
			MessageBox.Show("Error:Archive not found.")
			return None
		if not os.path.exists(self.patch_folder):
			MessageBox.Show("Error:Patch folder not found.\nPlease set the Patch folder.")
			return None
		if not os.path.exists(self.elf_name):
			MessageBox.Show("Error:elf not found.\nPlease set the Patch folder.")
			return None
		if not os.path.exists(self.backup_rpx_name):
			MessageBox.Show("Error:backup rpx not found.\nPlease set the Patch folder.")
			return None
		dict = self.getDict()
		fl = dir_fn(self.patch_folder)
		dest = open(self.need_patch_name , "rb+")
		dest.seek(0)
		sig = dest.read(4)
		if sig != "\x4c\x4e\x53\x35":
			MessageBox.Show("Error:Archive Header Error!\nNot a LNS5 Pack.")
			return None
		elf_file = open(self.elf_name , "rb+")
		fStream = Base(dest)
		s_nums = 0
		for fn in fl:
			pname = fn[len(self.patch_folder):]
			pname = pname.replace("\\" ,"/")
			if pname in dict:
				s_nums += 1
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
				if math_sector_align(len(zdata),0x800) <= math_sector_align(ZSIZE,0x800):
					print("USE INJECT METHOD")
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
					print("USE EXTEND METHOD")
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
		dest.seek(4)
		ZERO = fStream.ReadBEUInt64()
		FILE_NUMS = fStream.ReadBEUInt32()
		ARCHIVE_SIZE = fStream.ReadBEUInt64()
		ALIGN = fStream.ReadBEUInt64()
		for file_id in xrange(FILE_NUMS):
			OFFSET = fStream.ReadBEUInt64()
			SIZE = fStream.ReadBEUInt64()
			ZSIZE = fStream.ReadBEUInt64()
			comFlag = fStream.ReadBEUInt64()
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
		fixRPX(self.elf_name, self.backup_rpx_name , self.dest_rpx_name)
		MessageBox.Show("Patch Successed:\n%d file Patched!\nRPX fixed!"%(s_nums))

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

class MainForm(Form):
	def __init__(self):
		self.InitializeComponent()
	
	def InitializeComponent(self):
		self._buttonSelectArchive = System.Windows.Forms.Button()
		self._buttonUnpackPack = System.Windows.Forms.Button()
		self._textArchivePath = System.Windows.Forms.TextBox()
		self._label1 = System.Windows.Forms.Label()
		self._buttonSelectPath = System.Windows.Forms.Button()
		self._checkBoxBuildRPX = System.Windows.Forms.CheckBox()
		self._label2 = System.Windows.Forms.Label()
		self._textBoxPatchPath = System.Windows.Forms.TextBox()
		self._label3 = System.Windows.Forms.Label()
		self._label4 = System.Windows.Forms.Label()
		self._textBoxRPXPath = System.Windows.Forms.TextBox()
		self._buttonSelectRPX = System.Windows.Forms.Button()
		self.SuspendLayout()
		# 
		# buttonSelectArchive
		# 
		self._buttonSelectArchive.Location = System.Drawing.Point(24, 249)
		self._buttonSelectArchive.Name = "buttonSelectArchive"
		self._buttonSelectArchive.Size = System.Drawing.Size(116, 23)
		self._buttonSelectArchive.TabIndex = 0
		self._buttonSelectArchive.Text = "Patch lnk pack"
		self._buttonSelectArchive.UseVisualStyleBackColor = True
		self._buttonSelectArchive.Click += self.ButtonSelectArchiveClick
		# 
		# buttonUnpackPack
		# 
		self._buttonUnpackPack.Location = System.Drawing.Point(24, 204)
		self._buttonUnpackPack.Name = "buttonUnpackPack"
		self._buttonUnpackPack.Size = System.Drawing.Size(116, 23)
		self._buttonUnpackPack.TabIndex = 1
		self._buttonUnpackPack.Text = "Unpack lnk Pack"
		self._buttonUnpackPack.UseVisualStyleBackColor = True
		# 
		# textArchivePath
		# 
		self._textArchivePath.Location = System.Drawing.Point(24, 44)
		self._textArchivePath.Name = "textArchivePath"
		self._textArchivePath.Size = System.Drawing.Size(276, 21)
		self._textArchivePath.TabIndex = 2
		# 
		# label1
		# 
		self._label1.Location = System.Drawing.Point(24, 23)
		self._label1.Name = "label1"
		self._label1.Size = System.Drawing.Size(100, 18)
		self._label1.TabIndex = 3
		self._label1.Text = "LNK Pack Path:"
		# 
		# buttonSelectPath
		# 
		self._buttonSelectPath.Location = System.Drawing.Point(307, 44)
		self._buttonSelectPath.Name = "buttonSelectPath"
		self._buttonSelectPath.Size = System.Drawing.Size(33, 21)
		self._buttonSelectPath.TabIndex = 4
		self._buttonSelectPath.Text = "..."
		self._buttonSelectPath.UseVisualStyleBackColor = True
		self._buttonSelectPath.Click += self.ButtonSelectPathClick
		# 
		# checkBoxBuildRPX
		# 
		self._checkBoxBuildRPX.Checked = True
		self._checkBoxBuildRPX.CheckState = System.Windows.Forms.CheckState.Checked
		self._checkBoxBuildRPX.Location = System.Drawing.Point(158, 249)
		self._checkBoxBuildRPX.Name = "checkBoxBuildRPX"
		self._checkBoxBuildRPX.Size = System.Drawing.Size(104, 24)
		self._checkBoxBuildRPX.TabIndex = 5
		self._checkBoxBuildRPX.Text = "Build RPX"
		self._checkBoxBuildRPX.UseVisualStyleBackColor = True
		# 
		# label2
		# 
		self._label2.Location = System.Drawing.Point(24, 141)
		self._label2.Name = "label2"
		self._label2.Size = System.Drawing.Size(100, 19)
		self._label2.TabIndex = 6
		self._label2.Text = "Patch Path:"
		# 
		# textBoxPatchPath
		# 
		self._textBoxPatchPath.Location = System.Drawing.Point(24, 164)
		self._textBoxPatchPath.Name = "textBoxPatchPath"
		self._textBoxPatchPath.ReadOnly = True
		self._textBoxPatchPath.Size = System.Drawing.Size(275, 21)
		self._textBoxPatchPath.TabIndex = 7
		self._textBoxPatchPath.Text = "Patch"
		# 
		# label3
		# 
		self._label3.Font = System.Drawing.Font("微软雅黑", 8.25, System.Drawing.FontStyle.Underline, System.Drawing.GraphicsUnit.Point, 134)
		self._label3.ForeColor = System.Drawing.SystemColors.MenuHighlight
		self._label3.Location = System.Drawing.Point(23, 296)
		self._label3.Name = "label3"
		self._label3.Size = System.Drawing.Size(323, 31)
		self._label3.TabIndex = 8
		self._label3.Text = "(c)https://github.com/wmltogether/BlackWaterUnpacker"
		# 
		# label4
		# 
		self._label4.Location = System.Drawing.Point(24, 81)
		self._label4.Name = "label4"
		self._label4.Size = System.Drawing.Size(100, 23)
		self._label4.TabIndex = 9
		self._label4.Text = "RPX Path:"
		# 
		# textBoxRPXPath
		# 
		self._textBoxRPXPath.Location = System.Drawing.Point(24, 108)
		self._textBoxRPXPath.Name = "textBoxRPXPath"
		self._textBoxRPXPath.Size = System.Drawing.Size(276, 21)
		self._textBoxRPXPath.TabIndex = 10
		# 
		# buttonSelectRPX
		# 
		self._buttonSelectRPX.Location = System.Drawing.Point(307, 108)
		self._buttonSelectRPX.Name = "buttonSelectRPX"
		self._buttonSelectRPX.Size = System.Drawing.Size(33, 23)
		self._buttonSelectRPX.TabIndex = 11
		self._buttonSelectRPX.Text = "..."
		self._buttonSelectRPX.UseVisualStyleBackColor = True
		self._buttonSelectRPX.Click += self.ButtonSelectRPXClick
		# 
		# MainForm
		# 
		self.ClientSize = System.Drawing.Size(460, 331)
		self.Controls.Add(self._buttonSelectRPX)
		self.Controls.Add(self._textBoxRPXPath)
		self.Controls.Add(self._label4)
		self.Controls.Add(self._label3)
		self.Controls.Add(self._textBoxPatchPath)
		self.Controls.Add(self._label2)
		self.Controls.Add(self._checkBoxBuildRPX)
		self.Controls.Add(self._buttonSelectPath)
		self.Controls.Add(self._label1)
		self.Controls.Add(self._textArchivePath)
		self.Controls.Add(self._buttonUnpackPack)
		self.Controls.Add(self._buttonSelectArchive)
		self.Name = "MainForm"
		self.Text = "Maiden of Black Water JAP Archive Patcher"
		self.ResumeLayout(False)
		self.PerformLayout()

	def buttonStartPatchPressed(self , sender ,args):
		# patching event
		MessageBox.Show("clicked")
		

	def ButtonSelectPathClick(self, sender, e):
		dialog = OpenFileDialog()
		dialog.Filter = "LNK# files (*.lnk)|*.lnk"
		if dialog.ShowDialog(self) == DialogResult.OK:
			self._textArchivePath.Text = dialog.FileName
		pass

	def ButtonSelectArchiveClick(self, sender, e):
		pak = PAK()
		pak.pak_name = self._textArchivePath.Text
		pak.need_patch_name = self._textArchivePath.Text
		pak.dest_rpx_name = self._textBoxRPXPath.Text
		pak.inject()
		
		pass

	def ButtonSelectRPXClick(self, sender, e):
		dialog = SaveFileDialog()
		dialog.Filter = "RPX# files (*.rpx)|*.rpx"
		if dialog.ShowDialog(self) == DialogResult.OK:
			self._textBoxRPXPath.Text = dialog.FileName
		pass