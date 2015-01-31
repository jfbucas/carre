
all:carre run-carre cavalier run-cavalier carlar run-carlar

carre:carre.c
	gcc -O3 -Wall carre.c -o carre

run-carre:make-run
	./make-run carre

cavalier:carre.c
	gcc -O3 -Wall carre.c -o cavalier -DCAVALIER

run-cavalier:make-run
	./make-run cavalier

carlar:carlar.c
	gcc -O3 -Wall carlar.c -o carlar

run-carlar:make-run
	./make-run carlar

tree:
	mkdir recherches recherches/carre recherches/cavalier recherches/carlar

clean:
	rm -f carre run-carre cavalier run-cavalier carlar run-carlar *~ nohup.out

start:
	nohup ./run.sh &
