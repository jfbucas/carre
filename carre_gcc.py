#!/usr/bin/python3

import os
import sys
import time
import ctypes
import subprocess


SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

NB_CORES=5
MIN_JOBS_NUMBER = 100 # To get a finer granularity spreading the jobs amongst the cores
COMMENT_MARKER=" # "
M0 = 0xffffffff
M1 = 0xffffffff00000000

# --------------------------------------------------------------------------------------------------------------------------------------

nb_labels = 0
def genLibraryOptimizedASM( board_w, board_h, LesSauts, start_positions ):

	def genLibraryOptimizedASM_AuxCountDepth( nb_sauts, i, j, masque, depth_limit ):
		count = 0
		
		new_masque = masque | (1 << (i + j*board_w))

		if (nb_sauts+1 >= depth_limit):
			count = 1
		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
					if (masque & (1 << (i1 + j1*board_w))) == 0:
						count += genLibraryOptimizedASM_AuxCountDepth( nb_sauts+1, i1, j1, new_masque, depth_limit )
		return count

	def genLibraryOptimizedASM_AuxListMasques( nb_sauts, i, j, masque, depth_limit ):
		list_masques = []

		new_masque = masque | (1 << (i + j*board_w))

		if (nb_sauts+1 == depth_limit):
			list_masques.append( (new_masque, i, j) )
		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
					if (masque & (1 << (i1 + j1*board_w))) == 0:
						list_masques.extend( genLibraryOptimizedASM_AuxListMasques( nb_sauts+1, i1, j1, new_masque, depth_limit ) )
		return list_masques

	def genLibraryOptimizedASM_Aux( nb_sauts, i, j, masque ):
		global nb_labels
		output = ""
		if (depth + nb_sauts) == (board_w*board_h-1):
			if (masque & M1) != 0:
				output += "	test	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque).rjust(32,"0") +" i="+str(i)+",j="+str(j)+"\n"
			else:
				output += "	test	ecx, "+str( masque & M0 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0).rjust(32,"0") +" i="+str(i)+",j="+str(j)+"\n"
			output += "	sete	al\n"
			output += "	add	rdx, rax\n"

		elif nb_sauts == 1:
			if (masque & M1) != 0:
				output += "	test	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque).rjust(32,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		xor	ebx, "+str( masque >> 32 ).rjust(12," ") + "\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+1) + "\n"
				output += "		xor	ebx, "+str( masque >> 32 ).rjust(12," ") + "\n"
				output += "	label"+str( nb_labels )+":\n"
			else:
				output += "	test	ecx, "+str( masque & M0 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0).rjust(32,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		xor	ecx, "+str( masque & M0 ).rjust(12," ") + "\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+1) + "\n"
				output += "		xor	ecx, "+str( masque & M0 ).rjust(12," ") + "\n"
				output += "	label"+str( nb_labels )+":\n"
			nb_labels += 1

		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
					if (masque & (1 << (i1 + j1*board_w))) == 0:
						new_masque = masque | (1 << (i1 + j1*board_w))
						output += genLibraryOptimizedASM_Aux( nb_sauts+1, i1, j1, new_masque )

		return output

	symbols = ".intel_syntax noprefix\n"
	symbols += ".text\n"

	output  = ""
	for (i, j) in start_positions:
		# Get the depth at which we can split the search tree in a reasonable number of blocks
		depth_limit = 0
		while ( genLibraryOptimizedASM_AuxCountDepth( 0, i, j, 0, depth_limit) <= MIN_JOBS_NUMBER ):
			depth_limit += 1

		# Get the list of all the masques for that depth and where to start
		list_masques = genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, depth_limit)
		output += "# Depth_Jobs=" +str(depth_limit) + " => " + str(len(list_masques))+" Jobs\n"
		if NB_CORES > 1:
			nb_jobs_per_core = (len(list_masques) // (NB_CORES-1)) 
		else:
			nb_jobs_per_core = len(list_masques)


		for c in range(0, NB_CORES):
			output += ".globl start_" + str(i) + "_" + str(j) + "_" + str(c) + "\n"
			output += ".type start_" + str(i) + "_" + str(j) + "_" + str(c) + ", @function\n"
			output += "start_" + str(i) + "_" + str(j) + "_" + str(c) + ":\n"
			output += "	xor	rax, rax\n" # sete al for incrementing rdx
			output += "	xor	rbx, rbx\n" # Mask bits 32-63
			output += "	xor	rcx, rcx\n" # Mask bits 0-31
			output += "	xor	rdx, rdx\n" # return value
			for (masque, si, sj) in list_masques[c*nb_jobs_per_core:(c+1)*nb_jobs_per_core]:
				output += "	mov	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque >> 32).rjust(32,"0") +" \n"
				output += "	mov	ecx, "+str( masque & M0  ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0 ).rjust(32,"0") +" \n" # Mark initial position
				output += "	call	SauteDepuis_"+ str(si) +"_"+ str(sj)+"_" + str(depth_limit-1) +"\n"
			output += "	mov	rax, rdx\n"
			output += "	ret\n"
	output += "\n"

	for depth in range(0, board_w*board_h-1):
		for j in range(board_h):
			for i in range(board_w):
				output += 'SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + ":\n"
				output += genLibraryOptimizedASM_Aux( 0, i, j, 0 )
				output += "	ret\n\n"

	return symbols + output


# --------------------------------------------------------------------------------------------------------------------------------------

def genCore( start_positions ):
	bash_compile = open("cores/compile", "w")
	bash_compile.write("#!/bin/bash\n")
	bash_run = open("cores/run", "w")
	bash_run.write("#!/bin/bash\n")
	bash_run.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:.:..\n")
	for (i, j) in start_positions:
		for c in range(NB_CORES):
			f = "cores/"+str(i)+"_"+str(j)+"_"+str(c)
			gen = open(f+".c", "w")
			gen.write("#include <stdio.h>\n")
			gen.write("extern int start_"+str(i)+"_"+str(j)+"_"+str(c)+"();int main() { printf(\"%i\\n\", start_"+str(i)+"_"+str(j)+"_"+str(c)+"()); }\n" )
			gen.close()
			bash_compile.write("gcc "+f+".c -L. -L.. -o "+f+" -lSaute\n")
			bash_run.write("./"+f+" > "+f+".output &\n")
		bash_run.write("wait\n")

	bash_compile.close()
	bash_run.close()



# --------------------------------------------------------------------------------------------------------------------------------------

def CompileLibASM(w, h, S, start_positions):
	f = "libSaute"

	gen = open(f+".s", "w")
	gen.write(genLibraryOptimizedASM(w, h, S, start_positions))
	gen.close()


	GCC_BIN = "gcc "
	GCC_PARAMS = "-s -shared -fPIC -O3"

	if (not os.path.exists(f + ".so")) or (os.path.getmtime(f + ".s") > os.path.getmtime(f + ".so")):

		GCC_FILES = f + ".s -o " + f + ".so"
		GCC_CMD = GCC_BIN + " " + GCC_PARAMS + " " + GCC_FILES
		(val, output) = subprocess.getstatusoutput(GCC_CMD)
		if val != 0:
			print(output)

	return "Ok"


	


# --------------------------------------------------------------------------------------------------------------------------------------

# ----- Chronos
topTime = {}
def top( n=0 ):
	if not n in topTime:
		topTime[ n ] = 0
	r = "%.2f" % (time.time() - topTime[ n ] ) + "s"
	topTime[ n ] = time.time()
	return r


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Vous devez donner les dimensions")
		exit(1)

	#result="nb_solutions"
	S = SautsCarre
	w = int(sys.argv[1])
	h = int(sys.argv[2])
	if len(sys.argv) > 3:
		NB_CORES = int(sys.argv[3])
	#if len(sys.argv) > 4:
	#	result = sys.argv[4]

	# Get the list of position
	positions_to_check = []
	for j in range((h+1)//2):
		for i in range((w+1)//2):
			if w == h:
				if j>=i:
					positions_to_check.append( (i, j) )
			else:
				positions_to_check.append( (i, j) )
	# Compiling
	print("Compiling : ", end="")
	sys.stdout.flush()
	top(0)
	CompileLibASM(w, h, S, positions_to_check)
	genCore(positions_to_check)
	print(top(0))
	sys.stdout.flush()

	#print("Starting")
	LibSaute = ctypes.cdll.LoadLibrary("./libSaute.so")
	#LibSaute.start.argtypes = [ctypes.c_ulonglong, ]


	#print( positions_to_check )
			
	for (i, j) in positions_to_check:
		print("" + str(i+1) + " x " + str(j+1), end=" : ")
		sys.stdout.flush()
		top(1)
		#LibSaute.start(i + j * w)

		r = 0
		for c in range(NB_CORES):
			s = getattr(LibSaute, "start_"+str(i)+"_"+str(j)+"_"+str(c))
			s.restype = ctypes.c_int64
			r += s()
		print( r, "in", top(1) )
		#print("in " + str().rjust(25, " "), end=" seconds = ")
		#print("" + str(ctypes.c_int.in_dll( LibSaute, "nb_solutions" ).value), " solutions")
		sys.stdout.flush()
