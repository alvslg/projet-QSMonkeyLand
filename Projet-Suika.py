import sys#Ce module est particulièrement intéressant pour récupérer les arguments
           #passés à un script Python lorsque celui-ci est appelé en ligne de commande.

import numpy as np#très utile pour effectuer des calculs logiques et mathématiques
                   #sur des tableaux et des matrices 
import pygame
import pymunk #une bibliothèque Python pour la simulation de la physique 2D 

pygame.init()
rng = np.random.default_rng() #Initialise un générateur de nombres aléatoires à partir de NumPy.

# Constants
SIZE = WIDTH, HEIGHT = np.array([570, 770]) # Définit la taille de la fenêtre du jeu en utilisant NumPy.
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
    (138,43,226),
    (250, 0, 0),
    (50, 205, 50),
    (255, 215, 0),
    (250, 150, 0),
    (250, 0, 0),
    (250, 250, 100),
    (139, 69, 19),
    (0, 255, 0),
    (255, 255, 10),
    (0, 128, 0),
]

#Nombre d'images par seconde du jeu
FPS = 240

# Définit une liste de rayons pour les objets du jeu
RADII = [17, 25, 32, 38, 50, 63, 75, 87, 100, 115, 135]

#Définit l'épaisseur des objets du jeu
THICKNESS = 14

#Définit diverses constantes utilisées dans la simulation physique.
DENSITY = 0.001
ELASTICITY = 0.5
IMPULSE = 10000
GRAVITY = 2000
DAMPING = 0.8
NEXT_DELAY = FPS
BIAS = 0.00001
POINTS = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66]

# Crée un dictionnaire vide qui sera utilisé pour mapper les formes des particules aux
#objets Particle correspondants
shape_to_particle = dict()


class Particle:
        #Définit une classe Particle qui représente un fruit dans le jeu Suika.
    def __init__(self, pos, n, space, mapper):
        self.n = n % 11 #Définit sa couleur
        self.radius = RADII[self.n] #Détermine le rayon du fruit en fonction de la couleur attribuée
        self.body = pymunk.Body(body_type=pymunk.Body.DYNAMIC)
        self.body.position = tuple(pos)
        self.shape = pymunk.Circle(body=self.body, radius=self.radius) # Crée une forme de collision circulaire pour le fruit, associée au corps physique
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
    #Cette classe représente un fruit préliminaire, affichée avant que le fruit ne soit relâchée. En gros elle est sur la ligne invisible en haut de l'écran pour choisir l'endroit où le lacher
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
    #Cette classe représente un mur dans le jeu. Les murs sont statiques et ne peuvent pas être déplacés. Ils sont utilisés pour délimiter l'espace de jeu et peuvent servir d'obstacles pour les fruits."""
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

def display_next_fruit_right(screen, next_particle):
    fruit_index = next_particle.n+1 % 11
    fruit_color = COLORS[fruit_index]  # Obtenez la couleur correspondant au prochain fruit
    fruit_radius = RADII[fruit_index]  # Obtenez le rayon correspondant au prochain fruit

    # Dessiner un cercle représentant le prochain fruit
    pygame.draw.circle(screen, fruit_color, (WIDTH - 50, 50), fruit_radius)


# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT)) #Défini la taille de la fenêtre grâce aux viariables WIDTH et HEIGHT précisées au début
pygame.display.set_caption("PySuika") #Définit le titre de la fenêtre de jeu
clock = pygame.time.Clock() #lance le rafraichissement de jeu
pygame.font.init() #Initialise le systeme de police d'écriture
scorefont = pygame.font.SysFont("monospace", 32) #Initialise la police du score
overfont = pygame.font.SysFont("monospace", 72)#Initialise la police du GAME OVER

space = pymunk.Space() #création de l'espace dans lequel tout va interagir
space.gravity = (0, GRAVITY) #mise en place de la gravité dans l'espace pymunk
space.damping = DAMPING #Définit l'unité d'amortisement des fruits lorsqu'ils tomberont
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

# Collision Handler
# Collision Handler
handler = space.add_collision_handler(1, 1)

def collide(arbiter, space, data):
    """  fonction de gestion des collisions
    """
    sh1, sh2 = arbiter.shapes #les 2 fruits dans l'arbitre de collision 
    _mapper = data["mapper"]#Récupère le mapping des 2 fruits 
    pa1 = _mapper[sh1]
    pa2 = _mapper[sh2] #Obtient les fruit correspondants aux deux formes en collision impliquées dans l'arbitre de collision.
    cond = bool(pa1.n != pa2.n) #vérifie si ils sont du même type avec leur indice de couleur n
    pa1.has_collided = cond
    pa2.has_collided = cond
    if not cond: #si ils ne sont pas de meme type
        new_particle = resolve_collision(pa1, pa2, space, data["particles"], _mapper) #resolve colision pour traiter la colision entre les 2fruits
        data["particles"].append(new_particle) #ajoute le nouveau fruits a la liste de fruits actif
        data["score"] += POINTS[pa1.n]#Met à jour le score de point en ajoutant la valeur du fruit ajouté
    return cond #True si les 2 fruits sont diff et false si elle a été traitée


handler.begin = collide #associe le gestionnaire de collision a la fonction collide
handler.data["mapper"] = shape_to_particle #stocke le mapping entre les fruits / collisions
handler.data["particles"] = particles #stocke liste fruits actif au gestionnaire de collision
handler.data["score"] = 0 #stocke le score gestionnaire collision

#initiation du main
game_over = False

while not game_over:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:     
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                particles.append(next_particle.release(space, shape_to_particle))
                wait_for_next = NEXT_DELAY
            elif event.key in [pygame.K_q, pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and wait_for_next == 0:
            particles.append(next_particle.release(space, shape_to_particle))
            wait_for_next = NEXT_DELAY

    next_particle.set_x(pygame.mouse.get_pos()[0])

    if wait_for_next > 1:
        wait_for_next -= 1
    elif wait_for_next == 1:
        next_particle = PreParticle(next_particle.x, rng.integers(0, 5))
        wait_for_next -= 1

    # Draw background and particles
    screen.fill(BG_COLOR)
    if wait_for_next == 0:
        next_particle.draw(screen)
    for w in walls:
        w.draw(screen)
    for p in particles:
        p.draw(screen)
        if p.pos[1] < PAD[1] and p.has_collided:
            label = overfont.render("Game Over!", 1, (0, 0, 0))
            screen.blit(label, PAD)
            game_over = True
    label = scorefont.render(f"Score: {handler.data['score']}", 1, (0, 0, 0))
    screen.blit(label, (10, 10))
     # Afficher le prochain fruit à droite
    display_next_fruit_right(screen, next_particle)

    space.step(1/FPS)
    
    # Afficher le prochain fruit à droite
    display_next_fruit_right(screen, next_particle)

    pygame.display.update()
    clock.tick(FPS)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_q, pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()







# Cela permet  remplacer des espaces réservés dans une chaîne par les valeurs correspondantes des variables ou des expressions des variables ou des expressions Python directement dans une chaîne.
