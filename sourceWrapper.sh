#!/usr/bin/env bash

# directory variables
scriptsDir=$(dirname $(realpath ${0}))

# # 27 Sep 2019 variables, for 317H
# fileList=/Volumes/brac4g/IRC317H/BIDS/scripts/misc/fileLists/27_Sep_2019/parList_files.txt
# subList=/Volumes/brac4g/IRC317H/BIDS/scripts/misc/fileLists/27_Sep_2019/parList_IDs.txt

# # 11 Oct 2019 variables, for 317H
# fileList=/Volumes/brac4g/IRC317H/BIDS/scripts/misc/fileLists/11_Oct_2019/parList_files.txt
# subList=/Volumes/brac4g/IRC317H/BIDS/scripts/misc/fileLists/11_Oct_2019/parList_IDs.txt

# outDir=/Volumes/brac4g/IRC317H/BIDS/tmp_RawData

# 15 Oct 2019, for 287H
# fileList=/Volumes/brac4g/IRC287H/BIDS/scripts/misc/15_Oct_2019/287_files.txt
# subList=/Volumes/brac4g/IRC287H/BIDS/scripts/misc/15_Oct_2019/287_IDs.txt
# outDir=/Volumes/brac4g/IRC287H/BIDS/tmp_RawData

# 08 Nov 2019
fileList=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/08_Nov_2019/fileList.txt
subList=/Volumes/ADEBAYO_4/Repo/Scripts/ConvertSource/subLists/08_Nov_2019/ID_list.txt
outDir=/Volumes/brac4g/IRC287H/BIDS

# Perform source to raw data conversion

# ${scriptsDir}/source2BIDS.sh --file-list ${fileList} --sub-list ${subList} -P --ses 1 --output-dir ${outDir} --verbose --verbose-logging 
${scriptsDir}/source2BIDS.sh --file-list ${fileList} --sub-list ${subList} -D --ses 1 --output-dir ${outDir} --verbose --verbose-logging 