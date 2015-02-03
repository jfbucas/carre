#!/usr/bin/python3

import os
import ctypes
import subprocess

DEBUG=1

SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

# --------------------------------------------------------------------------------------------------------------------------------------
def genLibrary( board_w, board_h, LesSauts ):

	defs    = "typedef unsigned long long int uint64;\n"
	output  = "uint64 nb_solutions;" + "\n"
	output += "uint64 masque;" + "\n"
	defs   += "void start( uint64 position );" + "\n"
	output += "void start( uint64 position ) {" + "\n"
	output += "	nb_solutions = 0; " + "\n"
	output += "	masque = 0; " + "\n"
	output += "	switch (position) {" + "\n"
	for j in range(board_h):
		for i in range(board_w):
			output += '		case ' + str(i + j*board_w  ) + ":  SauteDepuis_"+ str(i) +"_"+ str(j)+"_0 (); break;" + "\n"
	output += "	}" + "\n"
	output += "}" + "\n"
	output += "\n"

	for depth in range(board_w*board_h):
		for j in range(board_h):
			for i in range(board_w):

				if depth == (board_w*board_h-1):
					defs   += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "();" + "\n"
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"
					output += "	nb_solutions ++;" + "\n"
					output += "};" + "\n"

				else:
					defs   += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "();" + "\n"
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"
					output += "	masque ^= " + str( 1 << (i + j*board_w) ) + ";" + "\n"

					for (sx,sy) in LesSauts:
						i1=i+sx
						j1=j+sy
						if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
							output += "	if ((masque & " + str( 1 << (i1 + j1*board_w) ).rjust(12," ") + ") == 0 ) SauteDepuis_" + str(i1) + "_" + str(j1) +"_" + str(depth+1) + "();" + "\n"

					output += "	masque ^= " + str( 1 << (i + j*board_w) ) + ";" + "\n"
					output += "	return;" + "\n"
					output += "}" + "\n"
					output += "" + "\n"

	defs += "\n"
	
	return defs + output

# --------------------------------------------------------------------------------------------------------------------------------------
def genLibraryOptimized( board_w, board_h, LesSauts ):

	defs    = "typedef unsigned long long int uint64;\n"
	output  = "uint64 nb_solutions;" + "\n"
	output += "uint64 masque;" + "\n"
	defs   += "void start( uint64 position );" + "\n"
	output += "void start( uint64 position ) {" + "\n"
	output += "	nb_solutions = 0; " + "\n"
	output += "	masque = 0; " + "\n"
	output += "	switch (position) {" + "\n"
	for j in range(board_h):
		for i in range(board_w):
			output += "		case " + str(i + j*board_w  ) + ":\n"
			output += "			masque ^= (1 << position ); // mark the initial position as being used\n"
			output += "			SauteDepuis_"+ str(i) +"_"+ str(j)+"_0 ();\n"
			output += "			break;\n"
	output += "	}\n"
	output += "}\n\n"

	for depth in range(board_w*board_h//2):
		for j in range(board_h):
			for i in range(board_w):

				if depth == ((board_w*board_h//2)-1):
					defs   += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "();" + "\n"
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"
				
					if (board_w*board_h % 2) == 0:
						for (sx1,sy1) in LesSauts:
							i1=i+sx1
							j1=j+sy1
							if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
									masque = (1 << (i1 + j1*board_w))
									output += "	nb_solutions += (uint64)((masque & " + str( masque ).rjust(12," ") + ") == 0 );\n"
					else:
						for (sx1,sy1) in LesSauts:
							i1=i+sx1
							j1=j+sy1
							if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
								for (sx2,sy2) in LesSauts:
									i2=i1+sx2
									j2=j1+sy2
									if (i2>=0) and (i2<board_w) and (j2>=0) and (j2<board_h):
										masque = (1 << (i1 + j1*board_w)) | (1 << (i2 + j2*board_w))
										output += "	nb_solutions += (uint64)((masque & " + str( masque ).rjust(12," ") + ") == 0 );\n"
					output += "};" + "\n"

				else:
					defs   += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "();" + "\n"
					output += 'void SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + "() {" + "\n"

					for (sx1,sy1) in LesSauts:
						i1=i+sx1
						j1=j+sy1
						if (i1>=0) and (i1<board_w) and (j1>=0) and (j1<board_h):
							for (sx2,sy2) in LesSauts:
								i2=i1+sx2
								j2=j1+sy2
								if (i2>=0) and (i2<board_w) and (j2>=0) and (j2<board_h):
									masque = (1 << (i1 + j1*board_w)) | (1 << (i2 + j2*board_w))
									output += "	if ((masque & " + str( masque ).rjust(12," ") + ") == 0 ) {\n"
									output += "		masque ^= " + str( masque ) + ";\n"
									output += "		SauteDepuis_" + str(i2) + "_" + str(j2) +"_" + str(depth+1) + "();\n"
									output += "		masque ^= " + str( masque ) + ";\n"
									output += "	}\n"

					output += "}\n\n"

	defs += "\n"
	
	return defs + output



# --------------------------------------------------------------------------------------------------------------------------------------

w=5
h=5
S=SautsCarre

gen = open( "libSaute.c", "w" )
gen.write( genLibraryOptimized( w, h, S ) )
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

for j in range(h):
	for i in range(w):
		LibSaute.start( i + j*w )
		print( ctypes.c_int.in_dll(LibSaute, "nb_solutions" ) )
