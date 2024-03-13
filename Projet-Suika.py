import sys #Ce module est particulièrement intéressant pour récupérer les arguments
           #passés à un script Python lorsque celui-ci est appelé en ligne de commande.

import numpy as np #très utile pour effectuer des calculs logiques et mathématiques
                   #sur des tableaux et des matrices 
import pygame

import pymunk #une bibliothèque Python pour la simulation de la physique 2D 

pygame.init()
rng = np.random.default_rng() #Initialise un générateur de nombres aléatoires à partir de NumPy.

# Définit la taille de la fenêtre du jeu en utilisant NumPy.
SIZE = WIDTH, HEIGHT = np.array([570, 770])

# Définit un décalage pour le contenu à l'intérieur de la fenêtre.
PAD = (24, 160)

# Définit les coordonnées de quatre points pour définir un cadre à l'intérieur de la fenêtre.
A = (PAD[0], PAD[1])
B = (PAD[0] - HEIGHT - PAD[0])
C = (WIDTH - PAD[0], HEIGHT - PAD[0])
D = (WIDTH - PAD[0], PAD[1])

# Définit différentes couleurs utilisées dans le jeu.
BG_COLOR = (250, 240, 148)
W_COLOR = (250, 190, 58)
COLORS = [
    (245, 0, 0),
    (245, 100, 100),
    (150, 20, 250),
    (250, 210, 10),
    (250, 150, 0),
    (245, 0, 0),
    (250, 250, 100),
    (255, 180, 180),
    (255, 255, 0),
    (100, 235, 10),
    (0, 185, 0),
]

#Nombre d'images par seconde du jeu
FPS = 60

# Définit une liste de rayons pour les objets du jeu
RADII = [17, 25, 32, 38, 50, 63, 75, 87, 100, 115, 135] 

#Définit l'épaisseur des objets du jeu
THICKNESS = 14

#Définit diverses constantes utilisées dans la simulation physique.
DENSITY= 0.001
ELASTICITY = 0.1
IMPULSE = 10000
GRAVITY = 2000
DAMPING = 0.8
NEXT_DELAY = FPS
NEXT_STEPS = 20
BIAS = 0.00001
POINTS = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66]
