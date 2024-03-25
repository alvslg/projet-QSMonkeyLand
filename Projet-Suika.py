import sys#Ce module est particulièrement intéressant pour récupérer les arguments
           #passés à un script Python lorsque celui-ci est appelé en ligne de commande.

import numpy as np#très utile pour effectuer des calculs logiques et mathématiques
                   #sur des tableaux et des matrices
import pygame
import pymunk#une bibliothèque Python pour la simulation de la physique 2D 

pygame.init()
rng = np.random.default_rng() #Initialise un générateur de nombres aléatoires à partir de NumPy.

# Définit la taille de la fenêtre du jeu en utilisant NumPy.
SIZE = WIDTH, HEIGHT = np.array([570, 770])
# Définit un décalage pour le contenu à l'intérieur de la fenêtre.
PAD = (24, 160)

# Définit les coordonnées de quatre points pour définir un cadre à l'intérieur de la fenêtre.
A = (PAD[0], PAD[1])
B = (PAD[0], HEIGHT - PAD[0])
C = (WIDTH - PAD[0], HEIGHT - PAD[0])
D = (WIDTH - PAD[0], PAD[1])

# Définit différentes couleurs utilisées dans le jeu.
BG_COLOR = (250, 240, 148)
W_COLOR = (250, 190, 58)
COLORS = [
    (245, 0, 0),
    (250, 100, 100),
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
# Définit une liste de rayons pour les fruits du jeu
RADII = [17, 25, 32, 38, 50, 63, 75, 87, 100, 115, 135]
#Définit l'épaisseur des objets du jeu

#Définit diverses constantes utilisées dans la simulation physique.
THICKNESS = 14
DENSITY = 0.001
ELASTICITY = 0.1
IMPULSE = 10000
GRAVITY = 2000
DAMPING = 0.8
NEXT_DELAY = FPS
BIAS = 0.00001
POINTS = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66]
shape_to_particle = dict()


class Particle: # Représente un fruit dans le jeu, avec des propriétés comme la position, le rayon, etc.
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
        if self.alive:x
            c1 = np.array(COLORS[self.n])
            c2 = (c1 * 0.8).astype(int)
            pygame.draw.circle(screen, tuple(c2), self.body.position, self.radius)
            pygame.draw.circle(screen, tuple(c1), self.body.position, self.radius * 0.9)

    def kill(self, space):
        space.remove(self.body, self.shape)
        self.alive = False
        print(f"Particle {id(self)} killed")

    @property
    def pos(self):
        return np.array(self.body.position)


class PreParticle: #Représente un fruit avant qu'il ne soit lancé dans le jeu.
    def __init__(self, x, n):
        self.n = n % 11
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


class Wall: #Représente les murs du jeu
    thickness = THICKNESS

    def __init__(self, a, b, space):
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.shape = pymunk.Segment(self.body, a, b, self.thickness // 2)
        self.shape.friction = 10
        space.add(self.body, self.shape)
        print(f"wall {self.shape.friction=}")

    def draw(self, screen):
        pygame.draw.line(screen, W_COLOR, self.shape.a, self.shape.b, self.thickness)


def resolve_collision(p1, p2, space, particles, mapper):
    if p1.n == p2.n:
        distance = np.linalg.norm(p1.pos - p2.pos)
        if distance < 2 * p1.radius:
            p1.kill(space)
            p2.kill(space)
            pn = Particle(np.mean([p1.pos, p2.pos], axis=0), p1.n+1, space, mapper)
            for p in particles:
                if p.alive:
                    vector = p.pos - pn.pos
                    distance = np.linalg.norm(vector)
                    if distance < pn.radius + p.radius:
                        impulse = IMPULSE * vector / (distance ** 2)
                        p.body.apply_impulse_at_local_point(tuple(impulse))
                        print(f"{impulse=} was applied to {id(p)}")
            return pn
    return None


# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT)) #surface de jeu
pygame.display.set_caption("PySuika") #titre de la fenêtre
clock = pygame.time.Clock() #Utilisé pour controler la vitesse de rafraichissement du jeu
pygame.font.init() #police de caractere
scorefont = pygame.font.SysFont("monospace", 32) #score 
overfont = pygame.font.SysFont("monospace", 72) #police pour le 'Game Over'

space = pymunk.Space() #Nouvel espace qui sera utilisé pour simuler la physique des objets dans le jeu.
space.gravity = (0, GRAVITY) #Définit gravité dans espace
space.damping = DAMPING #amortissement physique
space.collision_bias = BIAS #biais de collision dans l'espace (correction ajoutée a la resolution pour éviter les bugs)
print(f"{space.damping=}")  # // Cela imprime la valeur du coefficient d'amortissement de l'espace physique. C'est utile pour le débogage et la vérification des paramètres physiques du jeu
print(f"{space.collision_bias=}")
print(f"{space.collision_slop=}")

# créent les murs
pad = 20
left = Wall(A, B, space)
bottom = Wall(B, C, space)
right = Wall(C, D, space)
walls = [left, bottom, right]


# Liste stock fruit
wait_for_next = 0
next_particle = PreParticle(WIDTH//2, rng.integers(0, 5))
particles = []

# Verification de colision
handler = space.add_collision_handler(1, 1)


def collide(arbiter, space, data): #Gestionnaire de collisions appelée lorsque deux fruits seront en contact
    sh1, sh2 = arbiter.shapes #recupere les deux forme en collision
    _mapper = data["mapper"] #récupere le mappage correspondant aux fruits
    pa1 = _mapper[sh1] 
    pa2 = _mapper[sh2] #récupere les deux fruits dans des variables
    cond = bool(pa1.n != pa2.n)
    pa1.has_collided = cond
    pa2.has_collided = cond
    if not cond:
        new_particle = resolve_collision(pa1, pa2, space, data["particles"], _mapper) #Appele resolve_collision pour adapter les résolutions des fruits
        data["particles"].append(new_particle)
        data["score"] += POINTS[pa1.n]
    return cond
