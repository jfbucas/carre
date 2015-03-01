#!/usr/bin/python3

import os
import sys
import time
import ctypes
import subprocess


SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

SAUTS_PER_DEPTH=1 # We should limit to 1 as the mask is now ebx:ecx
COMMENT_MARKER=" # "
M0 = 0xffffffff
M1 = 0xffffffff00000000

# --------------------------------------------------------------------------------------------------------------------------------------

nb_labels = 0
def genLibraryOptimizedASM( board_w, board_h, LesSauts, result="nb_solutions" ):

	def genLibraryOptimizedASM_AuxCountDepth( nb_sauts, i, j, masque, depth_limit ):
		count = 0
		
		if (nb_sauts == depth_limit):
			count += 1
		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
					if (masque & (1 << (i1 + j1*board_w))) == 0:
						new_masque = masque | (1 << (i1 + j1*board_w))
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
				output += "	test	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
			else:
				output += "	test	ecx, "+str( masque & M0 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
			output += "	sete	al\n"
			output += "	add	rdx, rax\n"

		elif nb_sauts == SAUTS_PER_DEPTH:
			if (masque & M1) != 0:
				output += "	test	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		xor	ebx, "+str( masque >> 32 ).rjust(12," ") + "\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+SAUTS_PER_DEPTH) + "\n"
				output += "		xor	ebx, "+str( masque >> 32 ).rjust(12," ") + "\n"
				output += "	label"+str( nb_labels )+":\n"
			else:
				output += "	test	ecx, "+str( masque & M0 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		xor	ecx, "+str( masque & M0 ).rjust(12," ") + "\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+SAUTS_PER_DEPTH) + "\n"
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
	symbols += "test:\n"

	MIN_JOBS_NUMBER = 200

	output  = ""
	for j in range(board_h):
		for i in range(board_w):
			# Get the depth at which we can split the search tree in a reasonable number of blocks
			depth_limit = 0
			while ( genLibraryOptimizedASM_AuxCountDepth( 0, i, j, 0, depth_limit) <= MIN_JOBS_NUMBER ):
				depth_limit += 1
			output += "# " +str(depth_limit) + ":" + str( genLibraryOptimizedASM_AuxCountDepth( 0, i, j, 0, depth_limit)) + "\n"

			# Get the list of all the masques for that depth and where to start
			list_masques = genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, depth_limit)
			output += "# " + str( list_masques ) + "\n"

			symbols += ".globl start_" + str(i) + "_" + str(j) + "\n"
			symbols += ".type start_" + str(i) + "_" + str(j) + ", @function\n"
			output += "start_" + str(i) + "_" + str(j) + ":\n"
			output += "	xor	rax, rax\n" # sete al for incrementing result
			output += "	xor	rbx, rbx\n" # Mask bits 32-63
			output += "	xor	rcx, rcx\n" # Mask bits 0-31
			output += "	xor	rdx, rdx\n" # return value
			for (masque, si, sj) in list_masques:
				output += "	mov	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque >> 32).rjust(64,"0") +" \n"
				output += "	mov	ecx, "+str( masque & M0  ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0 ).rjust(64,"0") +" \n" # Mark initial position
				output += "	call	SauteDepuis_"+ str(si) +"_"+ str(sj)+"_" + str(depth_limit-1) +"\n"
			output += "	mov	rax, rdx\n"
			output += "	ret\n"
	output += "\n"

	for depth in range(0, board_w*board_h-1, SAUTS_PER_DEPTH):
		for j in range(board_h):
			for i in range(board_w):
				output += 'SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + ":\n"
				output += genLibraryOptimizedASM_Aux( 0, i, j, 0 )
				output += "	ret\n\n"

	return symbols + output



# --------------------------------------------------------------------------------------------------------------------------------------

def CompileLibASM(w, h, S, result="nb_solutions"):
	f = "libSaute"

	gen = open(f+".s", "w")
	gen.write(genLibraryOptimizedASM(w, h, S, result))
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

	result="nb_solutions"
	S = SautsCarre
	w = int(sys.argv[1])
	h = int(sys.argv[2])
	if len(sys.argv) > 2:
		SAUTS_PER_DEPTH = int(sys.argv[3])
	if len(sys.argv) > 4:
		result = sys.argv[4]

	print("Compiling : ", end="")
	sys.stdout.flush()
	top(0)
	CompileLibASM(w, h, S, result)
	print(top(0))
	sys.stdout.flush()

	#print("Starting")
	LibSaute = ctypes.cdll.LoadLibrary("./libSaute.so")
	#LibSaute.start.argtypes = [ctypes.c_ulonglong, ]

	positions_to_check = []
	for j in range((h+1)//2):
		for i in range((w+1)//2):
			if w == h:
				if j>=i:
					positions_to_check.append( (i, j) )
			else:
				positions_to_check.append( (i, j) )

	#print( positions_to_check )
			
	for (i, j) in positions_to_check:
		print("" + str(i+1) + " x " + str(j+1), end=" : ")
		sys.stdout.flush()
		top(1)
		#LibSaute.start(i + j * w)
		s = getattr(LibSaute, "start_"+str(i)+"_"+str(j))
		s.restype = ctypes.c_int64
		r = s()
		print( r, "in", top(1) )
		#print("in " + str().rjust(25, " "), end=" seconds = ")
		#print("" + str(ctypes.c_int.in_dll( LibSaute, "nb_solutions" ).value), " solutions")
		sys.stdout.flush()
