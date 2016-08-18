ASTEROIDS TOO:
This is a game I made in the last month heavily inspired by old school arcade games like 
asteroids. I spent about 60 hours on it, and it is around 2000 lines of code.

Execution:
python spacegame.py

-=4 enemies=-
-asteroid:		breaks into smaller peices upon destruction
-alien:			flies around and shoots at you
-basher:		does not spawn til late - fairly tough, will charge at you and self destruct on collision
-mothercow:		does not spawn at beginning - extremely tough, fires projectiles in all directions and spawns aliens

-=7 powerups=-
-spread gun: 		(S)weapon - 5 low damage projectiles fired at a fairly fast rate
-rapid fire: 		(R)weapon - bullets extremely rapidly with slightly less accuracy
-ion cannon: 		(I)weapon - an extremely powerful fast traveling continuous beam but is used up quickly
-missile launcher: 	(M)weapon - powerful heat-seeking missiles that lock on to a nearby enemy at a slightly slower pace
-quad shooter: 		(Q)fires your current weapon to your left, right and directly behind you
-overshield: 		(O)protects you from any damage that would normally kill you - single use
-deflector shield: 	(D)projects a matrix 6 of shields that surround you, each deflecting a single projectile 

scoreboard is local, try to beat your previous highs and see if your buddies can outdo yours. Somewhat embarassingly,
one of my friends can get a much higher score than myself.

Have fun!

|♦|--Controls--|♦|
in-game:
Arrow keys to move, c to shoot.
------
menus:
use the arrow keys to change selection and space/enter to select
------
press escape at any time to exit the game


NOTE:
I have compiled it to work as a standalone executable with pyinstaller. The way it works is, 
the python script and all the necesary files and dlls are compressed into the executable file
and extracted when the executable is run. The python script is then run using the included 
utilities.
I have not had much chance to test this on different machines yet so if it does not work on
your machine it would be extremely helpful if you could let me know by leaving a comment at:
http:\\www.soundlessdev.itch.io\asteroids-too