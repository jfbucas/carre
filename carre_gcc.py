#!/usr/bin/python3

import os
import sys
import time
import ctypes
import subprocess


SautsCavalier = ( (1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1) )
SautsCarre    = ( (3,0),(0,3),(-3,0),(0,-3),(2,2),(-2,2),(2,-2),(-2,-2) )

NB_CORES=5
MIN_JOBS_PER_POSITION = 100 # To get a finer granularity spreading the jobs amongst the cores
COMMENT_MARKER=" # "
M0 = 0xffffffff
M1 = 0xffffffff00000000
MAX_W = 10
MAX_H = 10

nb_labels = 0
w = 0
h = 0
LesSauts = SautsCarre

GCC_BIN="gcc"
#GCC_BIN="/usr/linux-k1om-4.7/bin/x86_64-k1om-linux-gcc"
if os.environ.get('GCC') != None:
	GCC_BIN = os.environ.get('GCC')
	print('[ Env GCC found :', GCC_BIN, ' ]')


# --------------------------------------------------------------------------------------------------------------------------------------

def printMask(masque_a, masque_b=None):
	w2=w
	if masque_b:
		w2=w*2
	
	o = "/" + "--" * w2 + "-\\\n"
	for j in range(h):
		o+="|"
		for i in range(w):
			if masque_a & (1 << (i + j*w)):
				o += "<>"
			else:
				o += "  "
		if masque_b:
			o+="|"
			for i in range(w):
				if masque_b & (1 << (i + j*w)):
					o += "<>"
				else:
					o += "  "
		o+="|\n"
	o += "\\" + "--" * w2 + "-/\n"
	print(o)
	
# --------------------------------------------------------------------------------------------------------------------------------------

def symetricHMask(masque):
	new_masque = 0
	for j in range(h):
		for i in range(w):
			if masque & (1 << (i + j*w)):
				new_masque |= (1 << ((w-1-i) + j*w))
	return new_masque

def symetricVMask(masque):
	new_masque = 0
	for j in range(h):
		for i in range(w):
			if masque & (1 << (i + j*w)):
				new_masque |= (1 << (i + (h-1-j)*w))
	return new_masque

def symetricD1Mask(masque):
	new_masque = 0
	for j in range(h):
		for i in range(w):
			if masque & (1 << (i + j*w)):
				new_masque |= (1 << (j + i*w))
	return new_masque
	
def symetricD2Mask(masque):
	return symetricD1Mask(symetricHMask(symetricVMask(masque)))


# --------------------------------------------------------------------------------------------------------------------------------------


def genLibraryOptimizedASM_AuxListMasques( nb_sauts, i, j, masque, coef, depth_limit, what="count" ):
	list_masques = None
	count = 0
	if what == "list":
		list_masques = []

	new_masque = masque | (1 << (i + j*w))

	if (nb_sauts+1 >= depth_limit):
		count = 1
		if what == "list":
			list_masques.append( (new_masque, i, j, coef) )

	else:
		if nb_sauts <= 4:
			# Try to detect symetrical situations for up to 3 levels of deepness
			LesSautsMasques = []
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<w) and (j1>=0) and (j1<h):
					if (new_masque & (1 << (i1 + j1*w))) == 0:
						#LesSautsMasques.append( (i1, j1, new_masque | (1 << (i1 + j1*w)) ) )
						LesSautsMasques.append( new_masque | (1 << (i1 + j1*w)) )

			c = [ coef ] * len( LesSautsMasques )
			for lsa in range(0, len(LesSautsMasques)):
				m = LesSautsMasques[ lsa ]
				if c[ lsa ] == 1:
					for lsb in range(0, len(LesSautsMasques)):
						n = LesSautsMasques[ lsb ]
						if ((m == symetricHMask( n )) or
							(m == symetricVMask( n )) or
							(m == symetricD1Mask( n )) or
							(m == symetricD2Mask( n ))):
								c[ lsa ] += 1
								c[ lsb ] -= 1

			#print( i, j, depth_limit )
			#print( c )
			#for lsa in range(0, len(LesSautsMasques)):
			#	m = LesSautsMasques[ lsa ]
			#	printMask( m )

			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<w) and (j1>=0) and (j1<h):
					if (new_masque & (1 << (i1 + j1*w))) == 0:
						m = (new_masque | (1 << (i1 + j1*w)))
						for lsa in range(0, len(LesSautsMasques)):
							n = LesSautsMasques[ lsa ]
							if (m == n) and (c[ lsa ] > 0):
								if what == "list":
									list_masques.extend( genLibraryOptimizedASM_AuxListMasques( nb_sauts+1, i1, j1, new_masque, c[ lsa ], depth_limit, what ) )
								else:
									count += genLibraryOptimizedASM_AuxListMasques( nb_sauts+1, i1, j1, new_masque, c[ lsa ], depth_limit, what )
									
						
		else:
			for ( sx, sy ) in LesSauts:
				i1 = i + sx
				j1 = j + sy
				if (i1>=0) and (i1<w) and (j1>=0) and (j1<h):
					if (new_masque & (1 << (i1 + j1*w))) == 0:
						if what == "list":
							list_masques.extend( genLibraryOptimizedASM_AuxListMasques( nb_sauts+1, i1, j1, new_masque, coef, depth_limit, what ) )
						else:
							count += genLibraryOptimizedASM_AuxListMasques( nb_sauts+1, i1, j1, new_masque, coef, depth_limit, what )

	if what == "list":
		return list_masques
	return count

def genLibraryOptimizedASM_Aux( depth, nb_sauts, i, j, masque, masque_avoid=0 ):
	global nb_labels
	output = ""
	if (depth + nb_sauts) == (w*h-1):
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
			if (i1>=0) and (i1<w) and (j1>=0) and (j1<h):
				if ((masque & (1 << (i1 + j1*w))) == 0) and ((masque_avoid & (1 << (i1 + j1*w))) == 0):
					new_masque = masque | (1 << (i1 + j1*w))
					output += genLibraryOptimizedASM_Aux( depth, nb_sauts+1, i1, j1, new_masque )

	return output

def genLibraryOptimizedASM( start_positions ):


	symbols = ".intel_syntax noprefix\n"
	symbols += ".text\n"

	output  = ""
	for (i, j) in start_positions:
		# Get the depth at which we can split the search tree in a reasonable number of blocks
		depth_limit = 0
		while ( genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit) <= MIN_JOBS_PER_POSITION ):
			depth_limit += 1

		# Get the list of all the masques for that depth and where to start
		list_masques = genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit, "list")
		output += COMMENT_MARKER + "=[ start_position "+ str(i)+","+str(j)+"]=======================================================================================\n"
		output += COMMENT_MARKER + "Depth limit " +str(depth_limit) + " => " + str(len(list_masques))+" Jobs\n"

		"""
		for na in range(0, 10):
			print(i, j, '-------------------------')
			(masque_a, si_a, sj_a, coef_a) = list_masques[ na ]
			masque_b = symetricHMask(masque_a)
			printMask(masque_a, masque_b)
			masque_b = symetricVMask(masque_a)
			printMask(masque_a, masque_b)
			masque_b = symetricD1Mask(masque_a)
			printMask(masque_a, masque_b)
			masque_b = symetricD2Mask(masque_a)
			printMask(masque_a, masque_b)
		
		a = 0
		for na in range(0, len(list_masques)):
			for nb in range(0, len(list_masques)):
				if na != nb:
					(masque_a, si_a, sj_a, coef_a) = list_masques[ na ]
					(masque_b, si_b, sj_b, coef_b) = list_masques[ nb ]
					if (si_a == si_b) and ( sj_a == sj_b ) and (masque_a == masque_b):
						printMask(masque_a, masque_b)
						a += 1
		print( a )
		"""

		for n in range(0, len(list_masques)):
			(masque, si, sj, coef) = list_masques[n]
			output += ".globl start_" + str(i) + "_" + str(j) + "_" + str(n) + "\n"
			output += ".type start_" + str(i) + "_" + str(j) + "_" + str(n) + ", @function\n"
			output += "start_" + str(i) + "_" + str(j) + "_" + str(n) + ":\n"
			output += "	xor	rax, rax\n" # sete al for incrementing rdx
			output += "	xor	rbx, rbx\n" # Mask bits 32-63
			output += "	xor	rcx, rcx\n" # Mask bits 0-31
			output += "	xor	rdx, rdx\n" # return value
			output += "	mov	ebx, "+str( masque >> 32 ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque >> 32).rjust(32,"0") +" \n"
			output += "	mov	ecx, "+str( masque & M0  ).rjust(12," ") + COMMENT_MARKER + "{0:b}".format(masque & M0 ).rjust(32,"0") +" \n" # Mark initial position
			output += "	call	SauteDepuis_"+ str(si) +"_"+ str(sj)+"_" + str(depth_limit-1) +"\n"
			output += "	mov	rax, rdx\n"
			for n in range(1,coef):
				output += "	add	rax, rdx\n"
			output += "	ret\n"

	output += "\n"
	output += COMMENT_MARKER + "--------------------------------------------------\n"

	for depth in range(0, w*h-1):
		for j in range(h):
			for i in range(w):
				output += 'SauteDepuis_' + str(i) + "_" + str(j) + "_" + str(depth) + ":\n"
				output += genLibraryOptimizedASM_Aux( depth, 0, i, j, 0, masque_avoid=masque )
				output += "	ret\n\n"
	
	output += "\n"


	return symbols + output


# --------------------------------------------------------------------------------------------------------------------------------------

def CompileJob(f):

	GCC_PARAMS = "-L. -L.. -L../.. -lSaute"

	GCC_FILES = "cores/"+f + ".c -o cores/" + f + ""
	GCC_CMD = GCC_BIN + " " + GCC_FILES + " " + GCC_PARAMS 
	print(GCC_CMD)
	(val, output) = subprocess.getstatusoutput(GCC_CMD)
	if val != 0:
		print(output)

	return "Ok"


def genCore( start_positions ):
	try:
		os.makedirs('cores/out'+str(w)+"x"+str(h))
	except OSError:
		pass
	
	base="carre_"+str(w)+"x"+str(h)

	gen = open("cores/" +base+".c", "w")
	gen.write("#include <stdio.h>\n")
	nb_jobs=0
	main_func = "int main (int argc, char *argv[]) {\n	int i;\n"
	main_func += "	if (argc > 1) {\n		i = atoi(argv[1]);\n"

	for (i, j) in start_positions:
		# Get the depth at which we can split the search tree in a reasonable number of blocks
		depth_limit = 0
		while ( genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit) <= MIN_JOBS_PER_POSITION ):
			depth_limit += 1

		# Get the list of all the masques for that depth and where to start
		list_masques = genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit, "list")
		gen.write("/* Prechewed depth: "+str(depth_limit)+" */\n")

		for n in range(0, len(list_masques)):
			gen.write("extern int start_"+str(i)+"_"+str(j)+"_"+str(n)+"();int main"+str(nb_jobs).rjust(6,"0")+"() { printf(\""+str(i)+"_"+str(j)+"_"+str(n)+"\\n%i\\n\", start_"+str(i)+"_"+str(j)+"_"+str(n)+"()); }\n" )
			main_func += "		if (i == "+str(nb_jobs)+") main"+str(nb_jobs).rjust(6,"0")+"();\n"
			nb_jobs += 1
	
	main_func += "	} else {\n		printf(\"%i\\n\", "+str(nb_jobs)+");\n	}\n"
	main_func += "	return 0;\n}\n\n"
	gen.write(main_func)

	gen.close()
	CompileJob( base )

	bash_run = open("cores/run_"+base, "w")
	bash_run.write("#!/bin/bash\n")
	bash_run.write("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:.:..\n")
	bash_run.write("NB_CORES=\"$(grep processor /proc/cpuinfo | wc -l)\"\n")
	bash_run.write("nb_jobs=$(./cores/"+base+")\n")
	bash_run.write("current_job=0\n")
	bash_run.write("nb_running=0\n")
	bash_run.write("while [ $current_job -lt $nb_jobs ]; do\n")
	bash_run.write("	if [ $nb_running -lt $NB_CORES ]; then\n")
	bash_run.write("		nb_start=$(( $NB_CORES - $nb_running ))\n")
	bash_run.write("		for ((n = 0; n < $nb_start; n++)); do\n")
	bash_run.write("			if [ $current_job -lt $nb_jobs ]; then\n")
	bash_run.write("				echo \"Start job $current_job\"\n")
	bash_run.write("				./cores/"+base+" $current_job > ./cores/out"+str(w)+"x"+str(h)+"/$current_job &\n")
	bash_run.write("				(( current_job ++ ))\n")
	bash_run.write("			fi\n")
	bash_run.write("		done\n")
	bash_run.write("	fi\n")
	bash_run.write("	sleep 1\n")
	bash_run.write("	nb_running=$(pgrep "+base+" | wc -l)\n")
	bash_run.write("done\n")
	bash_run.write("wait\n")
	for (i, j) in start_positions:
		bash_run.write("total=0\n")
		bash_run.write("for o in $(grep -l ^"+str(i)+"_"+str(j)+" cores/out"+str(w)+"x"+str(h)+"/*); do\n")
		bash_run.write("	total=$(( $total + $(tail -1 $o) ))\n")
		bash_run.write("done\n")
		bash_run.write("echo \""+str(i)+"x"+str(j)+" : $total\"\n")

	bash_run.close()



# --------------------------------------------------------------------------------------------------------------------------------------

def CompileLibASM(start_positions):
	f = "libSaute"

	gen = open(f+".s", "w")
	gen.write(genLibraryOptimizedASM(start_positions))
	gen.close()


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
	CompileLibASM(positions_to_check)
	genCore( positions_to_check)
	print(top(0))
	sys.stdout.flush()

	# If we are not cross compiling
	if os.environ.get('GCC') == None:
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
			# Get the depth at which we can split the search tree in a reasonable number of blocks
			depth_limit = 0
			while ( genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit) <= MIN_JOBS_PER_POSITION ):
				depth_limit += 1

			# Get the list of all the masques for that depth and where to start
			list_masques = genLibraryOptimizedASM_AuxListMasques( 0, i, j, 0, 1, depth_limit, "list")
			for n in range(0, len(list_masques)):
				s = getattr(LibSaute, "start_"+str(i)+"_"+str(j)+"_"+str(n))
				s.restype = ctypes.c_int64
				r += s()
			print( r, "in", top(1) )
			#print("in " + str().rjust(25, " "), end=" seconds = ")
			#print("" + str(ctypes.c_int.in_dll( LibSaute, "nb_solutions" ).value), " solutions")
			sys.stdout.flush()
