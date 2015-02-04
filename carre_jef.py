#!/usr/bin/python3

import os
import sys
import ctypes
import timeit
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

def CompileLib(w, h, S):
	gen = open("libSaute.c", "w")
	gen.write(genLibraryOptimized(w, h, S))
	gen.close()

	GCC_BIN = "gcc"
	GCC_PARAMS = "-O3 -shared -fPIC"

	f = "libSaute"
	if (not os.path.exists(f + ".so")) or (os.path.getmtime(f + ".c") > os.path.getmtime(f + ".so")):

		GCC_FILES = f + ".c -o " + f + ".so"
		GCC_CMD = GCC_BIN + " " + GCC_PARAMS + " " + GCC_FILES
		print(GCC_CMD)
		(val, output) = subprocess.getstatusoutput(GCC_CMD)
		if val != 0:
			print(output)


# --------------------------------------------------------------------------------------------------------------------------------------

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
	print("Time : " + str(timeit.timeit(
		"CompileLib(w, h, S)",
		number=1,
		setup="from __main__ import CompileLib, w,  h, S"
	)))
	sys.stdout.flush()

	print("Starting")
	LibSaute = ctypes.cdll.LoadLibrary("./libSaute.so")
	LibSaute.start.argtypes = [ctypes.c_ulonglong, ]

	for j in range(h):
		for i in range(w):
			print("Position " + str(i+1) + " x " + str(j+1), end=" : ")
			sys.stdout.flush()
			print("in " + str(timeit.timeit(
				"LibSaute.start(i + j * w)",
				number=1,
				setup="from __main__ import LibSaute, i, j, w"
			)).rjust(25, " "), end=" seconds = ")
			print("" + str(ctypes.c_int.in_dll( LibSaute, "nb_solutions" ).value), " solutions")
			sys.stdout.flush()
