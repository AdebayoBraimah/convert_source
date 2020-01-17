import os
import sys
import pdb

def run(outlierFile):
    """docstring for run"""

    fileDir = os.path.dirname(outlierFile)

    with open(outlierFile, 'r') as fopen:
        lines = fopen.readlines()

    #pdb.set_trace()
    lines = [line.strip().split('  ') for line in lines]
    for item in range(0, len(lines[0])):
        with open(os.path.join(fileDir, 'outlier_{}.txt'.format(item+1)), 'w') as fopen:
                for i in range(0,len(lines)):
                    fopen.write(lines[i][item]+'\n')




if __name__=="__main__":

    outlierFile = sys.argv[1]
    run(outlierFile)
