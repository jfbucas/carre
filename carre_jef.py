#!/usr/bin/python3

import os
import ctypes
import subprocess

DEBUG=1

SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

def genLibrary( board_w, board_h, LesSauts ):

	Fin = (1<<(board_w*board_h))-1

	output = "typedef unsigned long long int uint64;\n"
	output += "uint64 nb_solutions;" + "\n"
	output += "uint64 masque;" + "\n"
	output += "void start( uint64 position ) {" + "\n"
	output += "	nb_solutions = 0; " + "\n"
	output += "	masque = 0; " + "\n"
	output += "	switch (position) {" + "\n"
	for j in range(board_h):
		for i in range(board_w):
			output += '		case ' + str(i + j*board_w  ) + ":  SauteDepuis_"+ str(i) +"_"+ str(j)+"_0 (); break;" + "\n"
	output += "	}" + "\n"
	output += "}" + "\n"

	for depth in range(board_w*board_h):
		for j in range(board_h):
			for i in range(board_w):

				if depth == (board_w*board_h-1):
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"
					output += "	nb_solutions ++;" + "\n"
					output += "};" + "\n"

				else:
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"

					for (sx,sy) in LesSauts:
						i1=i+sx
						j1=j+sy
						if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
							output += "	// Saute Vers " + str( i1 ) + ", " + str(j1) + "\n"
							output += "	if ((masque & " + str( 1 << (i1 + j1*board_w) ) + ") == 0 ) {" + "\n"
							output += "		masque ^= " + str( 1 << (i1 + j1*board_w) ) + ";" + "\n"
#							output += "		if ( masque == " + str(Fin) +" ) {" + "\n"
#							output += "			nb_solutions ++;" + "\n"
#							output += "		} else {" + "\n"
							output += "		SauteDepuis_" + str(i1) + "_" + str(j1) +"_" + str(depth+1) + "();" + "\n"
							#output += "		}" + "\n"
							output += "		masque ^= " + str( (1 << (i1 + j1*board_w)) ) + ";" + "\n"
							output += "	}" + "\n"

					output += "	return;" + "\n"
					output += "}" + "\n"
					output += "" + "\n"
	
	return output


gen = open( "libSaute.c", "w" )
gen.write( genLibrary( 5, 5, SautsCarre ) )
gen.close()


GCC_CMD="gcc "
GCC_PARAMS="-O3 -shared -fPIC"

f="libSaute"
if (not os.path.exists( f+".so" )) or (os.path.getmtime(f+".c") > os.path.getmtime(f+".so")):

	GCC_FILES = " " + f + ".c -o " +f +".so"

	if DEBUG > 0:
		print(GCC_CMD + GCC_PARAMS + GCC_FILES)
	(val, output) = subprocess.getstatusoutput(GCC_CMD + GCC_PARAMS + GCC_FILES)
	if val != 0:
		print(GCC_CMD + GCC_PARAMS + GCC_FILES)
		print(output)
	else:
		if DEBUG > 0:
			print(output)
			print()


LibSaute = ctypes.cdll.LoadLibrary("./libSaute.so")
LibSaute.start.argtypes = [ ctypes.c_ulonglong, ]


LibSaute.start( 0 )
print( ctypes.c_int.in_dll(LibSaute, "nb_solutions" ) )
