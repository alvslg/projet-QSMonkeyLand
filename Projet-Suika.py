import sys #Ce module est particulièrement intéressant pour récupérer les arguments
           #passés à un script Python lorsque celui-ci est appelé en ligne de commande.

import numpy as np #très utile pour effectuer des calculs logiques et mathématiques
                   #sur des tableaux et des matrices 
import pygame

import pymunk #une bibliothèque Python pour la simulation de la physique 2D 

pygame.init()
rng = np.random.default_rng() #Initialise un générateur de nombres aléatoires à partir de NumPy.

#constantes du jeu

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
FPS = 240

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

# Crée un dictionnaire vide qui sera utilisé pour mapper les formes des particules aux
#objets Particle correspondants.
shape_to_particle = dict()

class Particle:
    """Définit une classe Particle qui représente un fruit dans le jeu Suika."""
    def __init__(self, pos, n, space, mapper):
        self.n = n % 11
        self.radius = RADII[self.n]
        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = tuple(pos)
        self.shape = pymunk.Circle(body=self.body, radius=self.radius)
        self.shape.density = DENSITY
        self.shape.elasticity = ELASTICITY
        self.shape.collision_type = 1
        self.shape.friction = 0.2
        self.has_collided = False
        mapper[self.shape] = self
        print(f"part {self.shape.friction=}")

        space.add(self.body, self.shape)
        self.alive = True
        print(f"Particle {id(self)} created {self.shape.elasticity}")

    def draw(self, screen):
        if self.alive:
            c1 = np.array(COLORS[self.n])
            c2 = (c1 * 0.8).astype(int)
            pygame.draw.circle(screen, tuple(c2), self.body.position, self.radius)
            pygame.draw.circle(screen, tuple(c1), self.body.position, self.radius * 0.9)

    def kill(self, space):
        space.remove(self.body, self.shape)
        self.alive = False
        print(f"Particle {id(self)} killed")

    @property #permet de définir une méthode comme une propriété de l'objet
    def pos(self):
        return np.array(self.body.position)


class PreParticle:
    """ Cette classe représente un fruit préliminaire, affichée avant que
        le fruit ne soit relâchée. En gros elle est sur la ligne invisible en haut
        de l'écran pour choisir l'endroit où le lacher"""
    def __init__(self, x, n):
        self.n = n % 11 #choisis la bonne couleur
        self.radius = RADII[self.n]
        self.x = x
        print(f"PreParticle {id(self)} created")

    def draw(self, screen):
        c1 = np.array(COLORS[self.n])
        c2 = (c1 * 0.8).astype(int)
        pygame.draw.circle(screen, tuple(c2), (self.x, PAD[1] // 2), self.radius)
        pygame.draw.circle(screen, tuple(c1), (self.x, PAD[1] // 2), self.radius * 0.9)

    def set_x(self, x):
        lim = PAD[0] + self.radius + THICKNESS // 2
        self.x = np.clip(x, lim, WIDTH - lim)

    def release(self, space, mapper):
        return Particle((self.x, PAD[1] // 2), self.n, space, mapper)


class Wall:
    """ Cette classe représente un mur dans le jeu. Les murs sont statiques et ne
        peuvent pas être déplacés. Ils sont utilisés pour délimiter l'espace de jeu
        et peuvent servir d'obstacles pour les fruits."""
    thickness = THICKNESS

    def __init__(self, a, b, space): #Crée un corps physique à l'aide de la classe pymunk.Body
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.shape = pymunk.Segment(self.body, a, b, self.thickness // 2)
        self.shape.friction = 10
        space.add(self.body, self.shape) #Add le corps et la forme du mur à l'espace physique
        print(f"wall {self.shape.friction=}")

    def draw(self, screen):
        pygame.draw.line(screen, W_COLOR, self.shape.a, self.shape.b, self.thickness)


def resolve_collision(p1, p2, space, particles, mapper):
    """ appelée pour résoudre une collision entre deux particules """
    if p1.n == p2.n:
        distance = np.linalg.norm(p1.pos - p2.pos)
        if distance < 2 * p1.radius:
            p1.kill(space)
            p2.kill(space) #Détruit les 2 fruits si ils sont du même type
            pn = Particle(np.mean([p1.pos, p2.pos], axis=0), p1.n+1, space, mapper)
            for p in particles:
                if p.alive:
                    vector = p.pos - pn.pos #verifie la distance entre 2 fruits grâce aux vecteurs
                    distance = np.linalg.norm(vector)
                    if distance < pn.radius + p.radius:
                        impulse = IMPULSE * vector / (distance ** 2) #calcule l'impulsion a donenr lorsque deux fruits vont collisioner
                        p.body.apply_impulse_at_local_point(tuple(impulse))
                        print(f"{impulse=} was applied to {id(p)}") #affiche l'impulsion qui a été appliqué au fruit p
            return pn
    return None #Si les deux fruits ne sont pas du même type et ne se chevauchent pas

screen = pygame.display.set_mode((WIDTH, HEIGHT)) #Défini la taille de la fenêtre grâce aux viariables WIDTH et HEIGHT précisées au début
pygame.display.set_caption("PySuika") #Définit le titre de la fenêtre de jeu
clock = pygame.time.Clock() #lance le rafraichissement de jeu
pygame.font.init() #Initialise le systeme de police d'écriture
scorefont = pygame.font.SysFont("monospace", 32) #Initialise la police du score
overfont = pygame.font.SysFont("monospace", 72)#Initialise la police du GAME OVER

space = pymunk.Space() #Création de l'espace dans lequel tout va interagir
space.gravity = (0, GRAVITY) #mise en place de la gravité dans l'espace pymunk
space.damping = DAMPING #Définit l'unité d'amortissement des fruits lorsqu'ils tomberont
space.collision_bias = BIAS #Biais de collision (pour gérer les problèmes de stabilité dans les collision)
print(f"{space.damping=}")
print(f"{space.collision_bias=}")
print(f"{space.collision_slop=}")

pad = 20 #épaisseur des murs de 20pixels
left = Wall(A, B, space) #mur gauche
bottom = Wall(B, C, space) #mur du bas
right = Wall(C, D, space) #mur droit
walls = [left, bottom, right] #liste des 3 murs du jeu

wait_for_next = 0 #Délai avant qu'un nouveau fruit apparaisse apres que le précédent fruit ait touché le fond
next_particle = PreParticle(WIDTH//2, rng.integers(0, 5)) #prepare le prochain fruit entre le plus petit et le 5eme plus petit
particles = [] #liste qui garde les fruits encore présent dans le jeu
# Cela permet  remplacer des espaces réservés dans une chaîne par les valeurs correspondantes des variables ou des expressions des variables ou des expressions Python directement dans une chaîne.
