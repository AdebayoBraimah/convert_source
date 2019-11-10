import os
import subprocess
import tempfile
import multiprocessing
import sys
import pdb
import glob
import shutil

def getFileName(inputfile):
    """docstring for getFileName"""
    filename = os.path.splitext(os.path.basename(inputfile))
    if filename[1] == '.gz':
        filename = os.path.splitext(filename[0])[0]

    return filename


def run(inputFile, refFile, matrix, outputFile):
    """docstring for run"""
    infoOutput = subprocess.check_output(["fslinfo", inputFile])
    infoOutput = infoOutput.decode("utf-8")
    tr=infoOutput.split("\n")[9].split(' ')[-1]
    len_input =int(infoOutput.split("\n")[4].split(' ')[-1])

    # Create temporary file
    filename = getFileName(inputFile)
    newTempDir = tempfile.mkdtemp(prefix=filename)
    print(newTempDir)

    # split func file
    newFiles = splitFile(inputFile, newTempDir)

    # Align func files - multiprocessing
    alignedPrefix = "Aligned_"
    jobs = []
    maxJobs=200

    for item, thisFile in enumerate(newFiles):
        p = multiprocessing.Process(target=alignFile, args=(thisFile, refFile, matrix, alignedPrefix))
        jobs.append(p)
        p.start()
        if len(jobs) == maxJobs:
            for j in jobs:
                j.join()
                #print '%s.exitcode = %s' % (j.name, j.exitcode)
            jobs = []


    for j in jobs:
        j.join()
        #print '%s.exitcode = %s' % (j.name, j.exitcode)
    jobs = []

    # Recombine aligned files
    alignedFiles = []
    i=0
    while len(newFiles) != len(alignedFiles):
        i = i+1
        if i > 1000:
            raise Exception("Input and output files do not have the same dimension!!!")
        alignedFiles = glob.glob(os.path.join(newTempDir, alignedPrefix + "*"))

    alignedFiles.sort()
    print(alignedFiles)
    # Output file
    query = ["fslmerge", "-tr", outputFile]
    for thisFile in alignedFiles:
        query.append(thisFile)
    query.append(tr)
    print(query)
    subprocess.call(query)

    infoOutput2 = subprocess.check_output(["fslinfo", outputFile])
    infoOutput2 = infoOutput2.decode('utf-8')
    len_output =int(infoOutput2.split("\n")[4].split(' ')[-1])
    if len_input != len_output:
        raise Exception("Input and output files do not have the same dimension!!!")

    #level = 0
    #filePrefix = getFileName(alignedFiles[0])
    #while len(alignedFiles) > 1:
    #    print "On level {}".format(level)
    #    print "\tLength of file list: {}".format(len(alignedFiles))
    #    alignedFiles = merge_list(alignedFiles, level, filePrefix)
    #    level += 1

    #shutil.copyfile(alignedFiles[0], outputFile)

    print("Cleanup temp files and dir")
    import shutil
    shutil.rmtree(newTempDir)

def merge_list(filelist, level, filePrefix):

    listlen = len(filelist)
    if listlen % 2 != 0:
        subprocess.call(["fslmerge", "-tr", filelist[-2], filelist[-2], filelist[-1] , "2"])
        filelist = filelist[0:-1]
        listlen = len(filelist)

    newFileList = []
    outdir = os.path.dirname(filelist[0])

    njobs = int(.0125 * listlen)
    if njobs < 0:
        njobs = 1

    jobs = []
    for i, j in enumerate(range(0, listlen, 2)):
        thisFile = filelist[j]
        nextFile = filelist[j+1]
        outfileName = filePrefix + "_level_{}_file_{}.nii.gz".format(level, i)
        outfile = os.path.join(outdir, outfileName)
        print("\tOn item {} of {}".format(i, listlen/2))

        p = multiprocessing.Process(target=merge, args=(thisFile, nextFile, outfile))
        jobs.append(p)
        p.start()
        if len(jobs) == njobs:
            for j in jobs:
                j.join()
                #print '%s.exitcode = %s' % (j.name, j.exitcode)
            jobs = []

        #subprocess.call(["fslmerge", "-tr", outfile, thisfile, nextFile, "2"])
        #newfileList.append(outfile)

    newfileList = glob.glob(os.path.join(outdir, "*_level_{}_file*".format(level)))
    newfileList.sort()

    return newfileList


def merge(file1, file2, outfile):
    subprocess.call(["fslmerge", "-tr", outfile, file1, file2, "2"])


def splitFile(inputFile, outDir):
    """docstring for splitFile"""

    outDirFiles = os.listdir(outDir)
    if not outDirFiles == []:
        raise Exception("Output directory is not empty! {}".format(outDir))
    filename = getFileName(inputFile)

    subprocess.call(["fslsplit", inputFile, os.path.join(outDir, filename + "_"), "-t"])

    files = os.listdir(outDir)

    files = [os.path.join(outDir, thisfile) for thisfile in files]

    return files



def alignFile(inputFile, refFile, matrix, alignedPrefix):
    """docstring for alignFile"""

    print("Aligning file {}".format(inputFile))
    outdir = os.path.dirname(inputFile)
    outfile = getFileName(inputFile)
    outfile = os.path.join(outdir, alignedPrefix + outfile)
    print("\t{}".format(outfile))

    subprocess.call(["flirt", "-in", inputFile, "-ref", refFile, "-applyisoxfm", "2.0", "-init", matrix, "-out", outfile])





if __name__=='__main__':

    inputFunc = sys.argv[1]
    ref = sys.argv[2]
    matrix = sys.argv[3]
    outputFile = sys.argv[4]

    run(inputFunc, ref, matrix, outputFile)
