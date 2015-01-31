; þ Les d‚placements dans un carr‚ magique en Assembleur þ
; þ En utilisant la th‚orie des graphes þ
; Edo F‚v 2001

[ORG 0100h]
[BITS 16]

Video_Seg       EQU 0B800h  ; adresse Segment de la video
Term		EQU 0FFh    ; Valeur terminale de la liste des d‚placements relatifs … chaque sommet
N  		EQU 7 	    ; c“t‚ du carr‚
NMAX  		EQU 0Fh     ; c“t‚ du carr‚ maximal
SomStart        EQU 00H     ; Sommet de D‚part

; C pour le prestige    |-]
db 'DEBUT'
pop  sp
pop  bp
dec  sp
; Fin du prestige 

call init
call run 
call done

@LAFIN:
mov   ax,04c00h
int   021H                   ; End Code

;; Initialisation
init:
 call Cls
 mov  dx,0748H
 call Aff_Heure

 call Exist                  ; Yatilune sauvegarde ?
 jc   @PasSauvegarde
 call Charger
 jmp  @Suitation
@PasSauvegarde:
  
 call Init_Normal

@Suitation:
 call Aff_Echec
ret

Init_Normal:
 cmp byte [Prob],0 
 ja @Pas_Cavalier
  call Init_Graph_Cavalier
 jmp @G_Inied
 @Pas_Cavalier:
  call Init_Graph_Magic
@G_Inied:

 mov  ax,SomStart          ; sommet de d‚part
 mov  si,0	           ; avec le voisin 0
 mov  word [chemin], ax      
 mov  word [chemin+2], si
 mov  di,tab
 add  di,ax
 mov  byte [di],1           ; Le premier sommet occup‚

 mov  cx,1
 mov  si,liberte
 mov  di,chemin
 mov  bp,tab
 mov  dx,[di]
ret
 
;; Routine Principale
run:
 @Boucle:

  @CalculSI:
   mov  si,liberte
   mov  ax,dx
   shl  ax,3
   add  ax,dx  
   add  si,ax             ; sommet *9 

  @rapid1:
   mov al,[si]
   cmp al,Term            ; ya til un voisin ?
   je  @plusdevoisin
    xor  ah,ah
    mov  bp,tab
    add  bp,ax
    cmp  byte [bp],0        ; ya til de la place ?
    jne  @pasdeplace
     mov  [di],dx     ; on empile
     mov  [di+2],si     
     add  di,4
     mov  dx,ax
     inc  cl
     mov  [bp],cl   ; on augmente le compteur, et on reserve la place
      cmp  cx,N*N   ; On regarde si le tableau est rempli = une solution
      jne  @pasdesolution
      call Solution
      @pasdesolution:

     jmp  @Boucle   
    @pasdeplace:    ; voisin suivant
     inc  si 
     jmp  @rapid1
    @plusdevoisin:  ; il ne reste plus de voisins
     mov  bp,tab
     add  bp,dx
     mov  byte [bp],0     ; on libŠre le sommet

     sub di,4
     cmp di,chemin-4      ; a t-on fait toutes les possibilit‚s ?
     jbe @Fini
     mov dx,[di]       ; on d‚sempile
     mov si,[di+2]
     inc si
     dec cl
    jmp @rapid1
@Fini:
ret

Solution:
 pusha
  inc  word [solu2]
  jnz  @ZzZ
  inc  dword [soluces]
  call Aff_Echec
 @ZzZ
  call Aff_Result
  call Keypressed
  jnz  @Touche
  jmp  @PasTouche
  @Touche:
   call Scankey       ; On lit la touche appuy‚e
    cmp   ax,011Bh    ; ESC
    je    @Quit
    ;;; autres touches a mettre ici
   call Aff_Echec
  @PasTouche:
 popa
ret

 @Quit:              ; Sortie pas hyper propre 
 popa
 call Sauvegarder
 mov  dx,0848H
 call Aff_Heure
 jmp  @LAFIN      ; Le truc Barbare !! mais alors de chez Barbare !

;; Terminaison
done:
 mov  dx,0848H
 call Aff_Heure
 call Aff_Result
ret

Init_Graph_Magic: ; Initialise le Graphe du Carr‚ MAGIC
 mov  di,liberte

 xor  ax,ax   ; on part du sommet zero
 xor  cx,cx   ; CH:y CL:x   
@Grah:
 xor  bx,bx
 
 cmp  ch,3 
 jb   @aa
 mov  dx,ax
 sub  dx,3*N   ; -3n
 call test_DX

@aa:
 cmp  ch,2
 jb   @cc
 cmp  cl,N-3
 ja   @bb
 mov  dx,ax
 sub  dx,2*N-2   ; -2n+2
 call test_DX
@bb:
 cmp  cl,2
 jb   @cc
 mov  dx,ax
 sub  dx,2*N+2   ; -2n-2
 call test_DX

@cc:
 cmp  cl,3
 jb   @dd
 mov  dx,ax
 sub  dx,3     ; -3
 call test_DX
@dd: 
 cmp  cl,N-4
 ja   @ee
 mov  dx,ax
 add  dx,3     ; +3
 call test_DX

@ee: 
 cmp  ch,N-3
 ja   @gg
 cmp  cl,N-3
 ja   @ff
 mov  dx,ax
 add  dx,2*N+2   ; +2n+2
 call test_DX
@ff:
 cmp  cl,2
 jb   @gg
 mov  dx,ax
 add  dx,2*N-2   ; +2n-2
 call test_DX

@gg: 
 cmp  ch,N-4
 ja   @hh
 mov  dx,ax
 add  dx,3*N     ; +3n
 call test_DX

@hh:
 mov  byte [di+bx],Term

 inc  cl
 cmp  cl,N
 jb   @ii
 mov  cl,0
 inc  ch
@ii:  

 add  di,9
 inc  ax
 cmp  ax,N*N
 jge  @FindeGrah
 jmp  @Grah 
 @FindeGrah
ret

Init_Graph_Cavalier:  ; Initialise le Graphe du Cavalier
 mov  di,liberte

 xor  ax,ax   ; on part du sommet zero
 xor  cx,cx   ; CH:y CL:x   
@GrahC:
 xor  bx,bx
 
 cmp  ch,2 
 jb   @bbC
 cmp  cl,1
 jb   @aaC
 mov  dx,ax
 sub  dx,2*N+1   ; -2n-1
 call test_DX
@aaC:
 cmp  cl,N-2
 ja   @bbC
 mov  dx,ax
 sub  dx,2*N-1   ; -2n+1
 call test_DX

@bbC:
 cmp  ch,1
 jb   @ddC
 cmp  cl,2
 jb   @ccC
 mov  dx,ax
 sub  dx,N+2   ; -n-2
 call test_DX
@ccC:
 cmp  cl,N-3
 ja   @ddC
 mov  dx,ax
 sub  dx,N-2   ; -n+2
 call test_DX

@ddC: 
 cmp  ch,N-2
 ja   @ffC
 cmp  cl,N-3
 ja   @eeC
 mov  dx,ax
 add  dx,N+2   ; +n+2
 call test_DX
@eeC:
 cmp  cl,2
 jb   @ffC
 mov  dx,ax
 add  dx,N-2   ; +n-2
 call test_DX

@ffC: 
 cmp  ch,N-3
 ja   @hhC
 cmp  cl,N-2
 ja   @ggC
 mov  dx,ax
 add  dx,2*N+1   ; +2n+1
 call test_DX
@ggC:
 cmp  cl,1
 jb   @hhC
 mov  dx,ax
 add  dx,2*N-1   ; +2n-1
 call test_DX

@hhC:
 mov  byte [di+bx],Term

 inc  cl
 cmp  cl,N
 jb   @iiC
 mov  cl,0
 inc  ch
@iiC:  

 add  di,9
 inc  ax
 cmp  ax,N*N
 jge  @FindeGrahC
 jmp  @GrahC 
 @FindeGrahC
ret

test_DX:   ; Teste si DX est pass‚ dans le n‚gatif
 cmp  dx,N*N  ; si dx>=Ný alors on a un d‚passement = pas bon
 jae  @sn
 mov  [di+bx],dl  ; si DX >0 on enregistre le sommet
 inc  bx
@sn:
ret 


Aff_Result:
 mov  word [Pos_Locate],80*12*2
 mov  eax,[soluces]
 call aff_dword
 mov  ax,[solu2]
 call aff_word
ret
 

Aff_Echec:
  pusha
  mov di, tab
  mov si, hex
  xor dx,dx
  @b1:
   mov dl,0
   @b2:  
     xor  bx,bx
     mov  bl,[di]
     mov  al,[si+bx]
     cmp  bx,1    
     jne  @paspremier
     mov  bl,10          ; le premier en vert
     jmp  @Hop
     @paspremier:
     cmp  bx,N*N
     jne  @pasdernier
     mov  bl,12          ; le dernier en rouge
     jmp  @Hop
     @pasdernier:
     cmp  bx,10
     jnb  @pasdizaine
     mov  bl,15          ; dans la premiere dizaine
     jmp  @Hop
     @pasdizaine:
     cmp  bx,20
     jnb  @pasvingtaine
     mov  bl,14          ; dans la premiere dizaine
     jmp  @Hop
     @pasvingtaine:
     mov  bl,7           ; case sans bcp d'interet
  
     @Hop:
     add  dh,4  ; pour centrer l'echiquier
     shl  dl,1
     call Locate
     shr  dl,1
     sub  dh,4
     call Put_Char
     inc di
     inc dl
    cmp dl,N
    jb  @b2
    inc dh
  cmp dh,N
  jb  @b1
  popa
ret

Aff_Heure:
  pusha
  call Locate
  mov  ah,02
  int  01AH
  push dx
  push cx
  mov  al, ch
  call aff_byte
  call Separateur  
  pop  cx
  mov  al, cl
  call aff_byte
  call Separateur  
  pop  dx
  mov  al, dh
  call aff_byte
  popa
ret

Separateur:
  mov  al,':'
  mov  bl,7
  call Put_Char
  add  byte [Pos_Locate],2
ret


Aff_Graph:      ; Entr‚e : DX : la position o— on veut l'afficher
 call Locate
 mov  di,liberte
 mov  cx,N*4
 @theloop:
  push cx
  mov  al,[di] 
  call aff_byte
  mov  al,[di+1] 
  call aff_byte
  mov  al,[di+2] 
  call aff_byte
  mov  al,[di+3] 
  call aff_byte
  mov  al,[di+4] 
  call aff_byte
  mov  al,[di+5] 
  call aff_byte
  mov  al,[di+6] 
  call aff_byte
  mov  al,[di+7]
  call aff_byte
  mov  al,[di+8]
  call aff_byte
  add  word [Pos_Locate],160-36 ; pour s‚parer un peu qd meme
  add  di,9
 pop  cx
 dec  cx
 jnz @theloop
ret

;;;;;; Les tonnes de proc‚dures en tout genres
                                    ; on renvoie si une touche a ‚t‚ press‚e
Keypressed:                         ; zero flag = touche press‚e
  mov   ah,11H
  int   16H
  ret

Scankey:                            ; Renvoi le code de la touche press‚e
  mov   ah,10H
  int   16H                         ; Code de la touche dans AX
  ret


Locate:                             ; positionne le curseur en dl,dh  - l'ecran commence en 0,0
 pusha
 mov  ax,dx           ; AX = (DH x 80)x2 + DLx2
 shr  ax,8
 mov  bx,ax
 shl  bx,5
 shl  ax,7
 add  ax,bx
 and  dx,000FFh
 shl  dx,1
 add  ax,dx

 mov  [Pos_Locate],ax
 popa
 ret

Put_Char:  ; affiche le caractere AL avec la couleur BL
 push ax
 push di

 push word Video_Seg
 pop  es

 mov  ah,bl
 mov  di,[Pos_Locate]
 mov  [es:di],ax

 pop  di
 pop  ax
ret

Put_MChar:  ; affiche multiples caracteres AL avec la couleur BL et le nombre CX
 pusha

 push word Video_Seg
 pop  es

 mov  di,[Pos_Locate]
 mov  ah,bl
 @LoopMChars:
  mov  [es:di],ax
  add  di,2
 loop @LoopMChars
 popa
ret

;;; Affichage
aff_dword:                   ; Enr‚e EAX
  ror   eax,16
  call  aff_word
  ror   eax,16
  call  aff_word
  ret

aff_word:                   ; Enr‚e AX
  xchg  al,ah
  call  aff_byte
  xchg  al,ah
  call  aff_byte
  ret

aff_byte:                    ; entr‚e AL : Byte
  push  bx
  push  dx
  xor   bx,bx

  mov   bl,al
  and   bl,0F0H
  shr   bl,4
  mov   cl,[hex+bx]
  mov   bl,al
  and   bl,0FH
  mov   ch,[hex+bx]         ; Isole les deux lettres

  mov   bl,15 ; en blanc
  mov   al,cl
  call  Put_Char            ; affiche le poids Fort
  add   word [Pos_Locate],2
  mov   al,ch
  call  Put_Char            ; affiche le poids Faible
  add   word [Pos_Locate],2
  
  pop   dx
  pop   bx
  ret

Cls:
  pusha
  xor  dx,dx
  call Locate
  mov  bl,7
  mov  al,' '
  mov  cx,2000   ; taille de l'ecran 80x25
  call Put_MChar
  popa
  ret

AffStr:                       ; DX adresse du message
  push  ax
  mov   ah,09h                ;Afficher le message
  int   021h
  pop   ax
  ret


;;;;;;;;;; Manipulation du Fichier OS=DOS 3.00 ou +
Creer_File:
  mov   ax,03c00h              ; Cr‚ation du fichier en I/O
  mov   cx,0                   ; pas d'attribut
  mov   dx,Nom_File
  int   021h
  jc    @Erreur_Fichier
  mov   [Handle],ax            ; on garde l'Handle !!
  ret

Open_File:                     ; ouvre ton bec
  mov   ax,03d02h              ; Ouverture du fichier en I/O
  mov   dx,Nom_File
  int   021h
  jc    @Erreur_Fichier
  mov   [Handle],ax            ; on garde l'Handle !!
  ret                          ; ne pas oublier le ret

Close_File:                    ; ferme ta gueule
  mov   bx,[Handle]
  mov   ah,03eh                ; On ferme le fichier
  int   021h
  jc    @Erreur_Fichier
  ret                          ; ne pas oublier le ret

;Seek_Fichier:                  ; D‚placement du pointeur du fichier
;  mov   ax,04200h
;  mov   bx,[Handle]
;  mov   cx,[Position_File+2]
;  mov   dx,[Position_File]
;  int   021h
;  jc    @Erreur_Fichier_Seek
;  ret

Read_File:                     ; on lit dans le fichier
  mov   ah,03Fh
  mov   bx,[Handle]
  mov   cx,Pos_Locate-miniN
  mov   dx,miniN
  int   021h
  jc    @Erreur_Fichier
  ret

Write_File:                    ; On ‚crit dans le fichier
  mov   ah,040h
  mov   bx,[Handle]
  mov   cx,Pos_Locate-miniN
  mov   dx,miniN
  int   021h
  jc    @Erreur_Fichier
  ret

@Erreur_Fichier_Seek:          ; On met la gestion d'erreur au milieu
  mov   dx,DMSG1               ; des proc‚dures pour que ce soit
  jmp   @Er2                   ; accessible en Short Jump ...  Astuce !!!
@Erreur_Fichier:
  cmp   ax,01
  jne   @Er2
  mov   dx,MSG1
  jmp   @Aff_Error
  @Er2:
  cmp   ax,02
  jne   @Er3
  mov   dx,MSG2
  jmp   @Aff_Error
  @Er3:
  cmp   ax,03
  jne   @Er4
  mov   dx,MSG3
  jmp   @Aff_Error
  @Er4:
  cmp   ax,04
  jne   @Er5
  mov   dx,MSG4
  jmp   @Aff_Error
  @Er5:
  cmp   ax,05
  jne   @Er6
  mov   dx,MSG5
  jmp   @Aff_Error
  @Er6:
  cmp   ax,06
  jne   @Er12
  mov   dx,MSG6
  jmp   @Aff_Error
  @Er12:
  cmp   ax,012
  jne   @Aff_Error
  mov   dx,MSG12
  jmp   @Aff_Error
@Erreur_Fichier_Attri:
  mov   dx,AMSG1
  jmp   @Er2


@Aff_Error:
  push  ax
  call  AffStr
  mov   dx,Entree
  call  AffStr
  pop   ax
 ret

LireAttribut:                  ; On lit les attributs du fichier
  mov   ax,04300h
  mov   dx,Nom_File
  int   021h
  jc    @Erreur_Fichier_Attri
  mov   [Attribut],cx
  ret

EcrireAttributs:               ; On ‚crit les attributs du fichier
  mov   ax,04301h
  mov   cx,[Attribut]
  mov   dx,Nom_File
  int   021h
  jc    @Erreur_Fichier_Attri
  ret

Exist:                  ; On regarde si le fichier existe
  mov   ax,04300h         ; Carry = pas de fichier
  mov   dx,Nom_File
  int   021h
  ret

Sauvegarder:
 mov  [Registres],ax
 mov  [Registres+2],bx
 mov  [Registres+4],cx
 mov  [Registres+6],dx
 mov  [Registres+8],si
 mov  [Registres+10],di
 call Creer_File
 call Write_File
 call Close_File
ret

Charger:
 call Open_File
 call Read_File
 call Close_File
 mov  ax,[Registres]
 mov  bx,[Registres+2]
 mov  cx,[Registres+4]
 mov  dx,[Registres+6]
 mov  si,[Registres+8]
 mov  di,[Registres+10]
ret



   ;;;Le fichier
Nom_File       db 'magic0.sav',0  ;; Nom du fichier de sauvegarde
Handle         dw 0               ;; Le handle du fichier
Attribut       dw 0               ;; Attribut du fichier

   ;;; Messages d'erreurs de manipulation de fichier
Entree db 13,10,36
;Ouverture / Fermeture / Cr‚ation / Lecture / Ecriture
MSG1  db 'Pas de logiciel File Sharing$'
MSG2  db 'Fichier non trouv‚$'
MSG3  db 'Chemin non trouv‚ ou fichier n ','existe pas$'
MSG4  db 'Plus de Handle Libre$'
MSG5  db 'AccŠs Refus‚$'
MSG6  db 'Handle non autoris‚ ou fichier non ouvert$'
MSG12 db 'Mode d',' accŠs non autoris‚$'
;D‚placement
DMSG1 db 'Code de distance non autoris‚$'
;Lire/Ecrire attribut
AMSG1 db 'Code de fonction inconnu$'

;Û-Û;;;;;;;;;; þ ;; + ;;; * ; ;-; Les Donn‚es 
miniN      db 0              ;; Pour avoir la taille
Prob       db 01h            ;; 0=Cavalier  1=Magic   2=...
liberte    times NMAX*NMAX*9 db 0  ;; les aretes existantes Graphe A
chemin     times NMAX*NMAX*2 dw 0  ;; le chemin parcouru
tab        times NMAX*NMAX   db 0  ;; l'‚chiquier
nb         db 0		     ;; nombre de sommets parcourus
soluces    db 0,0,0,0        ;; nombre de solutions
solu2      db 0,0            ;; pour augmenter le nombre de solutions possible !
Registres  db 'AXBXCXDXSIDI' ;; Sauvegarde des Registres

Pos_Locate dw 0              ;; La position du curseur

hex   db '0123456789'
      db 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
      db 'abcdefghijklmnopqrstuvwxyz'

Fin db 'FIN'
