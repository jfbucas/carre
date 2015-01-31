/******************************************************************************
*
* Carre.c 
*
* Recherche des solutions pour le fameux problème du carré :
* Dans un carré, on commence à 1 dans le coin supérieur gauche, et on a le 
* droit de se déplacer soit horizontalement ou verticalement en sautant 2  
* cases, soit en diagonales en sautant une case. On inscrit alors le nombre
* suivant dans la case atteinte. On ne peut pas passer par une case déjà
* occupée par un nombre.
*
* Le but est d'inscrire tous les nombres dans le carré.
*
* Il est possible de trouver manuellement une solution pour les carrés de côté
* 5 à 12. En dessous de 5, il n'y a pas de solution. Au dessus de 12, c'est 
* très long...
*
* Ce programme recherche toutes les solutions possibles, et donne leur nombre.
* Les versions précédentes de ce programme (en Basic et en Pascal) ont donné 
* les résultats suivants :
* taille   solutions
*  5x5        552
*  6x6     302282
*
* Cette version va essayer d'aller plus loin, d'abord par une écriture en C,
* ensuite par une optimisation de l'algorithme. De plus, toutes les 
* positions de départ vont être explorées (en tenant compte des symétries
* pour gagner un peu de temps)
*
* Le redémarrage est prévu, sachant qu'une sauvegarde est effectuée 
* régulièrement, et qu'au redémarrage, cette sauvegarde est détectée et reprise
* automatiquement.
*
******************************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <sys/time.h>
#include <time.h>

/* Pas la peine de dépasser 10, il faut déjà l'atteindre ... */
#define Dimension 10

/* Nombre de boucles de recherche entre 2 sauvegardes */
#define NbBouclesSauvegarde 10000000000L

#define aNombres   1
#define anbArcs    2
#define aSolutions 3
#define aArc       4

/******************************************************************************
*******************************************************************************
* 
* TYPES
* 
*******************************************************************************
******************************************************************************/

/******************************************************************************
* Contient les sauts autorisés d'une case à une autre : on a le droit de se 
* déplacer soit horizontalement ou verticalement en sautant 2 cases, soit en 
* diagonales en sautant une case.
******************************************************************************/
typedef struct UnSaut{
	int x,y;
}UnSaut;

#ifdef CAVALIER
UnSaut LesSauts[8] =
{{1,2}
,{2,1}
,{1,-2}
,{2,-1}
,{-1,2}
,{-2,1}
,{-1,-2}
,{-2,-1}
};
#else
UnSaut LesSauts[8] =
{{3,0}
,{0,3}
,{-3,0}
,{0,-3}
,{2,2}
,{-2,2}
,{2,-2}
,{-2,-2}
};
#endif

/******************************************************************************
* Décrit une case du carré
* nombre : le nombre qui est actuellement assigné à cette case
* nbCasesCibles : nombre de cases qui peuvent être atteintes par les sauts
* autorisés, et à l'intérieur du carré.
* LesCasesCibles : liste des cases qui peuvent être atteintes
******************************************************************************/
typedef struct UneCase{
  /* Valeurs fixes au cours de la recherche */
	int x, y, nbArcs;
	struct UneCase *(Arcs[8]);
	/* Valeurs qui changent au cours de la recherche */
	int arc, nombre;
	long nbSolutions;
	struct UneCase *LaSource;
}UneCase;

/******************************************************************************
*******************************************************************************
* 
* VARIABLES
* 
*******************************************************************************
******************************************************************************/

/******************************************************************************
* Le carré est surdimensionné
******************************************************************************/
UneCase Carre[Dimension][Dimension];

/******************************************************************************
* Dimensions du carré
******************************************************************************/
int Longueur, Largeur, Max;

/******************************************************************************
* Statistiques
******************************************************************************/
FILE *FichierResultat;
char nomFichierResultat[100];
FILE *FichierSauvegarde;
char nomFichierSauvegarde[100];
struct timeval Debut, Fin, DebutPosition, FinPosition;

/******************************************************************************
* Reprise
******************************************************************************/
int Reprise, r_depart_x, r_depart_y, r_courant_x, r_courant_y;
long r_nbSolutions;

/******************************************************************************
*******************************************************************************
* 
* FONCTIONS
* 
*******************************************************************************
******************************************************************************/

/******************************************************************************
* Affiche la date et l'heure à un instant donné
* La variable d'entrée "top" conserve cette heure après l'appel
******************************************************************************/
void affdateheure(char *titre, struct timeval *top)
{
	struct tm Details;
	
	gettimeofday(top, NULL);
	Details = *localtime(&(top->tv_sec));
	fprintf(FichierResultat, "%s : %4d-%02d-%02d %02d:%02d:%02d\n", titre, Details.tm_year+1900, Details.tm_mon+1, Details.tm_mday, Details.tm_hour, Details.tm_min, Details.tm_sec);
}

/******************************************************************************
* Affiche la durée entre deux instants
******************************************************************************/
void affduree(char *titre, struct timeval Debut, struct timeval Fin)
{
	int duree, duree_heures, duree_minutes, duree_secondes;

	duree = Fin.tv_sec - Debut.tv_sec;
	duree_heures = duree / 3600;
	duree_minutes = (duree / 60) % 60;
	duree_secondes = duree % 60;
	fprintf(FichierResultat, "%s : %d:%02d:%02d\n", titre, duree_heures, duree_minutes, duree_secondes);
}

/******************************************************************************
* Affiche les valeurs des cases d'un carré
******************************************************************************/
void affcarre(FILE *LeFichier, int Valeur)
{
	int i, j;
	long val=0;
	for(i=0;i<Longueur;i++)
	{
		for(j=0;j<Largeur;j++)
		{
			switch(Valeur)
			{
				case aNombres:   val = Carre[i][j].nombre;			break;
				case anbArcs:    val = Carre[i][j].nbArcs;			break;
				case aSolutions: val = Carre[i][j].nbSolutions;	break;
				case aArc:       val = Carre[i][j].arc;					break;
			}
			fprintf(LeFichier, " %ld", val);
		}
		fprintf(LeFichier, " \n");
	}
	/* Pour que l'on puisse consulter le contenu du fichier avant la fin du programme */
	fflush(LeFichier);
}

/******************************************************************************
* Sortie du programme sur un test
******************************************************************************/
void exitif(int test, char *message)
{
	if(test)
	{
		printf("Carre : %s\n",message);
		exit(1);
	}
}
/******************************************************************************
* Sauvegarde
******************************************************************************/
void sauvegarde(int depart_x, int depart_y, int courant_x, int courant_y, long nbSolutions)
{
	int i,j;
	
	FichierSauvegarde = fopen(nomFichierSauvegarde,"w");
	/* 
	* Sauvegarder
	* - La position de départ actuelle
	* - La position actuelle
	* - Le nombre de solutions actuel
	* - Toutes les cases du carré
	*
	* On ajoute 1 aux indices pour la lisibilité du fichier
	* On affiche les carrés pour l'utilisateur
	*/
	fprintf(FichierSauvegarde, "%d %d %d %d %ld\n", depart_x+1, depart_y+1, courant_x+1, courant_y+1, nbSolutions);
	for(i=0;i<Longueur;i++)
		for(j=0;j<Largeur;j++)
		  if(Carre[i][j].LaSource == NULL) /* Si c'est la position de départ, il n'y a pas de prédécesseur */
		  	fprintf(FichierSauvegarde, "%d %d %d %d %d %d %ld\n", i+1, j+1, Carre[i][j].nombre, Carre[i][j].arc, -1, -1, Carre[i][j].nbSolutions);
		  else
				fprintf(FichierSauvegarde, "%d %d %d %d %d %d %ld\n", i+1, j+1, Carre[i][j].nombre, Carre[i][j].arc, Carre[i][j].LaSource->x+1, Carre[i][j].LaSource->y+1, Carre[i][j].nbSolutions);
	fprintf(FichierSauvegarde, "\n");
	affcarre(FichierSauvegarde, aNombres);
	fprintf(FichierSauvegarde, "\n");
	affcarre(FichierSauvegarde, anbArcs);
	fprintf(FichierSauvegarde, "\n");
	affcarre(FichierSauvegarde, aArc);
	fprintf(FichierSauvegarde, "\n");
	affcarre(FichierSauvegarde, aSolutions);
	fclose(FichierSauvegarde);
}

/******************************************************************************
* Recharge
******************************************************************************/
int recharge()
{
	int x, y, nombre, arc, source_x, source_y, i;
	long nbSolutions;
	
	FichierSauvegarde = fopen(nomFichierSauvegarde,"r");
	if( FichierSauvegarde != NULL )
	{
		Reprise = 1;
		fscanf(FichierSauvegarde, "%d %d %d %d %ld\n", &r_depart_x, &r_depart_y, &r_courant_x, &r_courant_y, &r_nbSolutions);
		r_depart_x -= 1;
		r_depart_y -= 1;
		r_courant_x -= 1;
		r_courant_y -= 1;
		for( i=0; i<Max; i++)
		{
		  fscanf(FichierSauvegarde, "%d %d %d %d %d %d %ld\n", &x, &y, &nombre, &arc, &source_x, &source_y, &nbSolutions);
		  x-=1;
		  y-=1;
		  Carre[x][y].nombre = nombre;
		  Carre[x][y].arc = arc;
		  Carre[x][y].nbSolutions = nbSolutions;
		  /* Si c'est la position de départ, il n'y a pas de prédécesseur */
		  if((source_x == -1) && (source_y == -1))
		    Carre[x][y].LaSource = NULL;
		  else
		    Carre[x][y].LaSource = &(Carre[source_x-1][source_y-1]);
		}
	}
  else
    Reprise = 0;
  return Reprise;
}
/******************************************************************************
* Initialise le carré
* - Vérifie les dimensions
* - Crée les arcs pour le parcours du graphe (sous forme de pointeurs)
* - Ouvre le fichier pour écrire les résultats
******************************************************************************/
void init(int argc, char **argv)
{
	int i, j, k, i1, j1;
	
	exitif(argc<3, "Pas assez d'arguments");
	
	/* Lecture des dimensions demandées */
	Longueur = atoi(argv[1]);
	exitif(Longueur >= Dimension, "Longueur trop grande.");
	exitif(Longueur < 4,          "Longueur trop petite.");
	Largeur  = atoi(argv[2]);
	exitif(Largeur >= Dimension, "Largeur trop grande.");
	exitif(Largeur < 4,          "Largeur trop petite.");

	/* Initialisation du carré */
	Max = Longueur * Largeur;
	
	for(i=0;i<Longueur;i++)
		for(j=0;j<Largeur;j++)
		{
			Carre[i][j].nombre = 0;
			Carre[i][j].arc = 0;
			Carre[i][j].nbSolutions = 0;
			Carre[i][j].nbArcs = 0;
			Carre[i][j].x = i;
			Carre[i][j].y = j;
			for(k=0; k<8; k++)
			{
				i1=i+LesSauts[k].x;
				j1=j+LesSauts[k].y;
				if((i1>=0)&&(i1<Longueur)
				&&(j1>=0)&&(j1<Largeur))
				{
					Carre[i][j].Arcs[Carre[i][j].nbArcs] = &(Carre[i1][j1]);
					Carre[i][j].nbArcs++;
				}
			}
		}
	sprintf(nomFichierResultat, "c-%dx%d.txt", Longueur, Largeur);
	sprintf(nomFichierSauvegarde, "c-%dx%d.sav", Longueur, Largeur);
	/* Ici, on vérifie si un fichier de sauvegarde existe */
	if(recharge())
	{
		FichierResultat = fopen(nomFichierResultat,"a");
		affdateheure("Reprise", &Debut);
		DebutPosition = Debut;
		fprintf(FichierResultat, "Solutions actuelles : %ld\n", r_nbSolutions);
	}
	else
	{
		FichierResultat = fopen(nomFichierResultat,"w");
		affdateheure("Debut global", &Debut);
		fprintf(FichierResultat, "Nombre d'arcs par case :\n");
		affcarre(FichierResultat, anbArcs);
	}
}
	
/******************************************************************************
* Recherche itérative (non-récursive) des solutions
******************************************************************************/
void recherche(int x, int y)
{
	int JusteAvantMax;
	long nbSolutions, boucles, regNbBouclesSauvegarde;
	UneCase *LaCase, *LaCible;

	if(Reprise&&(x==r_depart_x)&&(y==r_depart_y))
	{
		nbSolutions = r_nbSolutions;
		LaCase = &(Carre[r_courant_x][r_courant_y]);
	}
	else
	{
		fprintf(FichierResultat, "\nPosition depart : %3d %3d\n", x+1, y+1);
		affdateheure("Debut", &DebutPosition);
		/* Pour que l'on puisse consulter le contenu du fichier avant la fin du programme */
		fflush(FichierResultat);
		
		/* Initialisation*/
		nbSolutions = 0;
		Carre[x][y].nombre = 1;
		Carre[x][y].arc = 0;
		Carre[x][y].LaSource = NULL;
		LaCase = &(Carre[x][y]);
	}
	JusteAvantMax = Max - 1;
	/* Début de la boucle */
	boucles = 0;
	regNbBouclesSauvegarde = NbBouclesSauvegarde;
	do
	{
		/* Sauvegarde pour une reprise ultérieure */
/*		boucles++;
		if(boucles == regNbBouclesSauvegarde)
		{
			boucles = 0;
			sauvegarde(x, y, LaCase->x, LaCase->y, nbSolutions);
		}*/
		/* Si on a pas dépassé le nombre maximal d'arcs pour la case */
		if( LaCase->arc < LaCase->nbArcs )
		{
			LaCible = LaCase->Arcs[LaCase->arc];
			/* Passer à l'arc suivant */
			LaCase->arc++;
			/* Vérifier si la case est libre */
			if(LaCible->nombre == 0)
			{
			  if(LaCase->nombre == JusteAvantMax)
			  {/* Si on est juste avant une solution, pas besoin d'aller dans la case vide */
					nbSolutions++;
					/* Optionnel */
/*					if(nbSolutions==1)
					{
						LaCible->nombre = Max;
						fprintf(FichierResultat, "Premiere solution :\n");
						affcarre(FichierResultat, aNombres);
						LaCible->nombre = 0;
					}*/
			  }
			  else
				{/* Sinon, on avance dans la case vide trouvée */
					LaCible->nombre = LaCase->nombre + 1;
					LaCible->arc = 0;
					LaCible->LaSource = LaCase;
					LaCase = LaCible;
				}
			}
		}
		else
		{/* Tous les arcs ont été visités, plus de saut possible à partir d'ici */
		  LaCase->nombre = 0;
		  LaCase = LaCase->LaSource;
		}
	}	while(LaCase != NULL);
	/* Fin de la boucle */
	Carre[x][y].nbSolutions = nbSolutions;
	affdateheure("Fin", &FinPosition);
	fprintf(FichierResultat, "Solutions : %ld\n", nbSolutions);
	affduree("Duree", DebutPosition, FinPosition);
	/* Pour que l'on puisse consulter le contenu du fichier avant la fin du programme */
	fflush(FichierResultat);
}

/******************************************************************************
* Programme principal
* Lance la recherche avec plusieurs coordonnées de départ en tenant compte
* des symétries pour ne pas recalculer
******************************************************************************/
void run(void)
{
	int max_x, max_y, x, y, XL, YL;
	
	XL = Longueur - 1;
	YL = Largeur - 1;
	
	max_x = (Longueur + 1)/2;
	max_y = (Largeur + 1)/2;
	
	if(Reprise)
	{
		x = r_depart_x;
		y = r_depart_y;
	}
	else
	{
		x = 0;
		y = 0;
	}
	/* Si c'est un rectangle : avec la symétrie, on ne fait qu'un quart */
	/* Si c'est un carré : avec la symétrie, on ne fait qu'un huitième, */
	/* on élimine une partie de la recherche en dessous de la diagonale */
	while((x<max_x)&&(y<max_y))
	{
  	recherche(x, y);
  	/* On reproduit le nombres de solutions dans les cases symétriques */
  	/* Il y a pour les carrés 8 cases de symétrie (avec recouvrement possible) */
  	/* Il y a pour les rectangles 4 cases de symétrie (avec recouvrement possible) */
  	Carre[XL-x][y   ].nbSolutions = Carre[x][y].nbSolutions;
  	Carre[XL-x][YL-y].nbSolutions = Carre[x][y].nbSolutions;
  	Carre[x   ][YL-y].nbSolutions = Carre[x][y].nbSolutions;
  	/* Pour un carré, on tient compte de la symétrie par  rapport à la diagonale */
  	if( Longueur == Largeur )
		{
	  	Carre[YL-y][x   ].nbSolutions = Carre[x][y].nbSolutions;
	  	Carre[YL-y][XL-x].nbSolutions = Carre[x][y].nbSolutions;
	  	Carre[y   ][x   ].nbSolutions = Carre[x][y].nbSolutions;
	  	Carre[y   ][XL-x].nbSolutions = Carre[x][y].nbSolutions;
	  }
  	y++;
  	if( !(y<max_y))
  	{
  		x++;
  		/* Pour un carré, on tient compte de la symétrie par  rapport à la diagonale */
  		if( Longueur == Largeur ) y=x; else y=0;
  	}
  }
}

/******************************************************************************
* Fin du programme
* Affiche les éléments globaux de temps et de solutions
******************************************************************************/
void done(void)
{
	int i, j;
	long SolutionsGlobales = 0;
	
	for(i=0;i<Longueur;i++)
		for(j=0;j<Largeur;j++)
			SolutionsGlobales += Carre[i][j].nbSolutions;
	fprintf(FichierResultat, "\nNombre de solutions par case :\n");
	affcarre(FichierResultat, aSolutions);
	affdateheure("\nFin globale", &Fin);
	fprintf(FichierResultat, "Solutions globales : %ld\n", SolutionsGlobales);
	affduree("Duree globale", Debut, Fin);
	fclose(FichierResultat);
}

/******************************************************************************
* Main ? Ça veut dire quoi ?
******************************************************************************/
int main(int argc, char **argv)
{
	init(argc, argv);
	run();
	done();
	exit(0);
}
/******************************************************************************
* Fin
******************************************************************************/
