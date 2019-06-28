# Pi_Eyes Module

### By :  Camila ARIAS
### *P20 : Tête interactive Kompaï*
**Contact** : @camila-ud 

## Module des yeux animées pour Raspberry Pi 3

Ce projet fait partie du Projet 20 à l'IMT Atlantique. Le projet a pris comme point de partie le projet [Adafruit- PiEyes](https://github.com/adafruit/Pi_Eyes). Les yeux sont génerés en utilisant une animation par la librerie *pi3d* , la relation qui existe entre le code et la visualization est : 

![image](/dimension.png) 

**Raspberry pi 3**

Le controller pour les écran OLED est [eye.py](../master/eye.py), la classe principal est Eyes et chaque oeil est representé par un objet de la classe Eye : 

`python eye.py`

La connexion physique se trouve dans ![hard](/hard.png) 

**Ordinateur**

Si on veut travailler seulement dans l'animation on peut executer
`python main_eyes.py`

