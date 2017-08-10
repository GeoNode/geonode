import os
inDir = os.path.abspath('/home/geonode/Work/Data/Renamed/Agno/Agno_Blk5C_20130418')
count = 1

print inDir

if not os.path.isdir(inDir):
    print 'Input directory error!'
    exit(1)

for path, dirs, files in os.walk(inDir):
    print 'COUNT', count
    print path
    print dirs
    print files
    count+=1
        # for laz in files:
        #     if las.endswith(".laz"):
