import struct,os
def getBFLIMSWIZZLE(fn):
    fp = open(fn , "rb")
    fp.seek(-5,2)
    SWIZZLE = ord(fp.read(1))
    SWIZZLE = (SWIZZLE - 4 )/ 0x20
    fp.close()
    return SWIZZLE

os.system("AMDCompressCLI.exe -fd BC4 \"inPNG\\image__titlelogowindwakermask_00^s.bflim.gtx.dds.PNG\" \"inDDS\\image__titlelogowindwakermask_00^s.bflim.gtx.dds\"")



fl = os.listdir("inDDS")
for fn in fl:
    print(fn.split(".")[0])
    SWIZZLE = getBFLIMSWIZZLE(fn.split(".")[0].replace("__" , "\\") + ".bflim")
    print(SWIZZLE)
    os.system("TexConv2.exe -i \"inDDS\%s\" -o \"inGTX\%s.gtx\" -swizzle %d"%(fn ,fn.split(".")[0] , SWIZZLE))

