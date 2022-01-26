import concurrent.futures
import time
import os
import sys
import shutil

start = time.perf_counter()
AIM_location="/home/tlacour/git/AIM/AIM/AIM.py"

# Funcstion to read original input file and generate new partial ones
# it DOES require the use of start_frame and end_frame
def generate_input(file,CPUs):
    print('Analysing input file')
    fh=open(file,'r')
    while True:
        line=fh.readline()
        words=line.split()
        if len(words)>1:
            if words[0]=="start_frame":
                start_frame=int(words[1])
                print(str(start_frame))
            if words[0]=="end_frame":
                end_frame=int(words[1])
                print(str(end_frame))
        if not line:
            break
    frames=end_frame-start_frame+1
    frames_per_cpu=int(frames/CPUs)
    print(f'A total of {frames} frames are requested.')
    print(f'will do {frames_per_cpu} frames on each CPU.')
    fh.close()

    # Now write a new input file for each CPU
    for CPU in range(CPUs):
        fh=open(file,'r')
        fname="Parameters"+str(CPU)+".txt"
        fo=open(fname,'w')
        while True:
            line=fh.readline()
            words=line.split()
            if len(words)>1:
                if words[0]=="start_frame":
                    fo.write(words[0]+"   "+str(CPU*frames_per_cpu)+"\n")
                elif words[0]=="end_frame":
                    # The last CPU will pick up any leftovers from rounding
                    if CPU<CPUs-1:
                        fo.write(words[0]+"   "+str((CPU+1)*frames_per_cpu)+"\n")
                    else:
                        fo.write(words[0]+"   "+str(end_frame)+"\n")
                elif words[0]=="outfilename":
                    ofn="Hamiltonian"+str(CPU)+".tmp\n"
                    fo.write(words[0]+"   "+ofn)
                elif words[0]=="outdipfilename":
                    ofn="Dipole"+str(CPU)+".tmp\n"
                    fo.write(words[0]+"   "+ofn)
                elif words[0]=="outposfilename":
                    ofn="Position"+str(CPU)+".tmp\n"
                    fo.write(words[0]+"   "+ofn)
                elif words[0]=="outramfilename":
                    ofn="Raman"+str(CPU)+".tmp\n"
                    fo.write(words[0]+"   "+ofn)
                elif words[0]=="nFrames_to_calculate":
                    if CPU==0:
                        print("Leaving out nFrames_to_calculate")
                else:
                    fo.write(line)

            else:
                fo.write(line)
            if not line:
                break
        fo.close()
        fh.close()
    return

# This function merges all the temporary bin files and delete the
# temporary files in the process to avoid too much disk usage
def merge_bin(fname,outname,CPUs):
    fout=open(outname,'wb')
    files=[]
    for CPU in range(0,CPUs):
        files.append(fname+str(CPU)+".tmp.bin")
    for file in files:
        fh=open(file,'rb')
        shutil.copyfileobj(fh,fout,65536)
        fh.close()
        os.system("rm -f "+file)
    fout.close()

# This function starts the parallel jobs
def runjobs(job):
    print(f'Running job {job}...')
    job_string="python "+AIM_location+" Parameters"+str(job)+".txt"
    os.system(job_string)
    return f'Done running job {job}'

# Check that the script is called as
# python AIM.py inputfilename number_of_cpus
num_arg=len(sys.argv)
if (num_arg!=3):
    print('Wrong number of command line arguments!\n')
    exit(0)

myfile=str(sys.argv[1])
CPUs=int(sys.argv[2])
print(f'Running AIM parallel with input file {myfile}')
print(f'on {str(CPUs)} CPUs.')

generate_input(myfile,CPUs)

# Start the parallel runs
with concurrent.futures.ProcessPoolExecutor() as executor:
    jobs = list(range(0,CPUs))
    results = executor.map(runjobs, jobs)

# Merge the bin files
merge_bin("Hamiltonian","Hamiltonian.bin",CPUs)
merge_bin("Position","Position.bin",CPUs)
merge_bin("Dipole","Dipole.bin",CPUs)
merge_bin("Raman","Raman.bin",CPUs)

finish = time.perf_counter()

print(f'Finished in {round(finish-start, 2)} second(s)')

