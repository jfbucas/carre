#!/usr/bin/python3

import os
import sys
import time
import ctypes
import subprocess


SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

SAUTS_PER_DEPTH=1

# --------------------------------------------------------------------------------------------------------------------------------------

def genLibraryOptimized( board_w, board_h, LesSauts ):

	def genLibraryOptimized_Aux( nb_sauts, i, j, masque ):
		output = ""
		if (depth + nb_sauts) == (board_w*board_h-1):
			output += "	nb_solutions += ((masque & " + str( masque ).rjust(12," ") + "u ) == 0 ); // "+ "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"

		elif nb_sauts == SAUTS_PER_DEPTH:
			output += "	if ((masque & " + str( masque ).rjust(12," ") + "u ) == 0 ) { // "+ "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
			output += "		masque ^= " + str( masque ) + "u;\n"
			output += "		SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+SAUTS_PER_DEPTH) + "();\n"
			output += "		masque ^= " + str( masque ) + "u;\n"
			output += "	}\n"

		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
					if (masque & (1 << (i1 + j1*board_w))) == 0:
						new_masque = masque | (1 << (i1 + j1*board_w))
						output += genLibraryOptimized_Aux( nb_sauts+1, i1, j1, new_masque )

		return output

	defs    = "typedef unsigned long long int uint64;\n"
	output  = "uint64 nb_solutions;" + "\n"
	output += "uint64 masque;" + "\n"
	defs   += "void start( uint64 position );" + "\n"
	output += "void start( uint64 position ) {" + "\n"
	output += "	nb_solutions = 0; " + "\n"
	output += "	masque = 0u; " + "\n"
	output += "	switch ( position ) {" + "\n"
	for j in range(board_h):
		for i in range(board_w):
			output += "		case " + str( i + j*board_w  ) + ":\n"
			output += "			masque ^= " + str( 1 << (i + j*board_w)) +"u;\n" # Mark initial position
			output += "			SauteDepuis_"+ str(i) +"_"+ str(j)+"_0 ();\n"
			output += "			break;\n"
	output += "	}\n"
	output += "}\n\n"

	for depth in range(0, board_w*board_h-1, SAUTS_PER_DEPTH):
		for j in range(board_h):
			for i in range(board_w):
				defs   += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "();" + "\n"
				output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"
				output += genLibraryOptimized_Aux( 0, i, j, 0 )
				output += "}\n\n"

	defs += "\n"
	
	return defs + output

# --------------------------------------------------------------------------------------------------------------------------------------

nb_labels = 0
def genLibraryOptimizedASM( board_w, board_h, LesSauts ):


	def genLibraryOptimizedASM_Aux( nb_sauts, i, j, masque ):
		global nb_labels
		output = ""
		if (depth + nb_sauts) == (board_w*board_h-1):
			if masque > ( 1<<30 ):
				output += "	mov	rbx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	test	rcx, rbx\n"
			else:
				output += "	test	rcx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
			output += "	sete	al\n"
			output += "	add	rdx, rax\n"

		elif nb_sauts == SAUTS_PER_DEPTH:
			if masque > ( 1<<30 ):
				output += "	mov	rbx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	test	rcx, rbx\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		push	rcx\n"
				output += "		xor	rcx, rbx\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+SAUTS_PER_DEPTH) + "\n"
				output += "		pop	rcx\n"
				#output += "		mov	rbx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				#output += "		xor	rcx, rbx\n"
				output += "	label"+str( nb_labels )+":\n"
			else:
				output += "	test	rcx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n"
				output += "	jne	label"+str( nb_labels )+"\n"
				output += "		xor	rcx, "+str( masque ).rjust(12," ") + "\n"
				output += "		call	SauteDepuis_" + str(i) + "_" + str(j) +"_" + str(depth+SAUTS_PER_DEPTH) + "\n"
				output += "		xor	rcx, "+str( masque ).rjust(12," ") + "\n"
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

	#symbols = "global nb_solutions\n"
	symbols = "BITS 64\n"
	output  = ""
	#output += "section .data\n"
	#output += "nb_solutions:	dq 2\n"
	output += "section .text\n"
	for j in range(board_h):
		for i in range(board_w):
			masque = (1 << (i + j*board_w))
			symbols += 'global start_' + str(i) + "_" + str(j) + "\n"
			output += "start_" + str(i) + "_" + str(j) + ":\n"
			output += "	xor	rax, rax\n" # for incrementing nb_solutions
			output += "	xor	rbx, rbx\n" # for transfering imediate values bigger than (1<<31)
			output += "	xor	rcx, rcx \n" # Mask
			output += "	xor	rdx, rdx \n" # nb_solutions
			output += "	mov	rcx, "+str( masque ).rjust(12," ") + " ; " + "{0:b}".format(masque).rjust(64,"0") +" i="+str(i)+",j="+str(j)+"\n" # Mark initial position
			output += "	call	SauteDepuis_"+ str(i) +"_"+ str(j)+"_0\n"
			# http://www.tortall.net/projects/yasm/manual/html/manual.html#objfmt-elf64-wrt
			#output += "	mov	[rel nb_solutions wrt ..gotpcrel], rdx\n"
			#output += "	mov	[rel nb_solutions wrt ..got], rdx\n"
			#output += "	mov	[rel nb_solutions wrt ..plt], rdx\n"
			##output += "	mov	[rel nb_solutions wrt ..sym], rdx\n"
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

def CompileLib(w, h, S):
	f = "libSaute"

	gen = open(f+".c", "w")
	gen.write(genLibraryOptimized(w, h, S))
	gen.close()

	GCC_BIN = "gcc"
	GCC_PARAMS = "-O3 -shared -fPIC"

	if (not os.path.exists(f + ".so")) or (os.path.getmtime(f + ".c") > os.path.getmtime(f + ".so")):

		GCC_FILES = f + ".c -o " + f + ".so"
		GCC_CMD = GCC_BIN + " " + GCC_PARAMS + " " + GCC_FILES
		print(GCC_CMD)
		(val, output) = subprocess.getstatusoutput(GCC_CMD)
		if val != 0:
			print(output)

def CompileLibASM(w, h, S):
	f = "libSaute"

	gen = open(f+".asm", "w")
	gen.write(genLibraryOptimizedASM(w, h, S))
	gen.close()


	YASM_BIN = "yasm "
	YASM_PARAMS = "-f elf64"
	LD_BIN = "ld "
	LD_PARAMS = "-shared"

	if (not os.path.exists(f + ".o")) or (os.path.getmtime(f + ".asm") > os.path.getmtime(f + ".o")):

		YASM_FILES = f + ".asm -o " + f + ".o"
		YASM_CMD = YASM_BIN + " " + YASM_PARAMS + " " + YASM_FILES
		print(YASM_CMD)
		(val, output) = subprocess.getstatusoutput(YASM_CMD)
		if val != 0:
			print(output)

	if (not os.path.exists(f + ".so")) or (os.path.getmtime(f + ".o") > os.path.getmtime(f + ".so")):

		LD_FILES = f + ".o -o " + f + ".so"
		LD_CMD = LD_BIN + " " + LD_PARAMS + " " + LD_FILES
		print(LD_CMD)
		(val, output) = subprocess.getstatusoutput(LD_CMD)
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

	S = SautsCarre
	w = int(sys.argv[1])
	h = int(sys.argv[2])
	if len(sys.argv) > 2:
		SAUTS_PER_DEPTH = int(sys.argv[3])

	print("Compiling")
	sys.stdout.flush()
	top(0)
	#CompileLib(w, h, S)
	CompileLibASM(w, h, S)
	print("Time : " + top(0))
	sys.stdout.flush()

	print("Starting")
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
