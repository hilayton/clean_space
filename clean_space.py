"""
clean_space.py
Asteroids-like game where you clean garbage in space

Controls:
- W/A/S/D: Movement
- ESC: Quit
"""

import pygame
import sys
from pygame.locals import *
import random

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60
BACKGROUND_COLOR = (0, 0, 0)
SHIP_SIZE = 40
SHIP_COLOR = (0, 200, 255)

# Physics constants
SHIP_ACCEL = 600
SHIP_DRAG = .99
MAX_SPEED = 1000

class Spaceship:
    """Defining spaceship and physical properties"""

    def __init__(self, x, y):
        # Position and motion vectors
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)

        # Properties
        self.size = SHIP_SIZE
        self.color = SHIP_COLOR
        self.rect = pygame.Rect(0, 0, SHIP_SIZE, SHIP_SIZE)
        self.rect.center = self.pos

        # Trail effect
        self.trail = []
        self.max_trail_length = 5

    def apply_force(self, force):
        """Apply force to ship"""
        self.acc += force

    def apply_impulse(self, impulse):
        """For sudden velocity changes.
        Might not be used, but likely for when colliding with asteroids"""        

        self.vel += impulse

    def move(self):
        """Defining how ship can move"""


    def update(self, dt, keys):
        """Update physics simulation"""

        # start each frame with zero acceleration
        self.acc = pygame.Vector2(0, 0)

        # player input for directional movement
        if keys[K_w]:
            self.acc.y -= SHIP_ACCEL
        if keys[K_s]:
            self.acc.y += SHIP_ACCEL
        if keys[K_a]:
            self.acc.x -= SHIP_ACCEL
        if keys[K_d]:
            self.acc.x += SHIP_ACCEL

        # prevent diagonal movement from increasing acceleration
        if self.acc.length_squared() > 0:
            self.acc.scale_to_length(SHIP_ACCEL)

        # save current trail position
        self.trail.append(self.pos.copy())

        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        

        # limit max speed
        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

        # update velocity and position
        self.pos += self.vel * dt

        self.screen_wrap()
        
        self.vel +=self.acc * dt

        # apply drag to ship to slow it
        self.vel *= SHIP_DRAG ** (dt * FPS)

        # keep ship position synced with Vector2 pos
        self.rect.center = (round(self.pos.x), round(self.pos.y))


    def reset(self):
        """reset ship to starting position"""
        self.pos = pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT //2)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.trail = []

    def draw(self, screen):
        """draw ship and trail"""

        # draw trail
        for i, pos in enumerate(self.trail):
            progress = i / len(self.trail)
            alpha = int(50 * progress)
            color = (min(255, self.color[0] + alpha),
                    min(255, self.color[1] + alpha),
                    min(255, self.color[2] + alpha))
            size = int(self.size * (0.3 + 0.7 * progress))
            trail_rect = pygame.Rect(0, 0, size, size)
            trail_rect.center = (round(pos.x), round(pos.y))
            pygame.draw.rect(screen, color, trail_rect)

        pygame.draw.rect(screen, self.color, self.rect)

    def screen_wrap(self):
        """move ship to opposite side when it leave screen"""

        half_size = self.size / 2

        if self.pos.x < -half_size:
            self.pos.x = SCREEN_WIDTH + half_size
        elif self.pos.x > SCREEN_WIDTH + half_size:
            self.pos.x = -half_size

        if self.pos.y < -half_size:
            self.pos.y = SCREEN_HEIGHT + half_size
        elif self.pos.y > SCREEN_HEIGHT + half_size:
            self.pos.y = -half_size

class Asteroid:
    """defining asteroids"""

    def __init__(self, x, y):
        # Position and motion vectors
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)


def main():
    """main game loop"""

    # set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Clean Space')
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 18)

    # create ship in middle of screen
    ship = Spaceship(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

    # setting up star field
    stars = []

    for i in range(150):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        brightness = random.randint(100, 255)
        size = random.randint(1, 2)

        stars.append((x, y, brightness, size))

    # ===============
    # MAIN GAME LOOP
    # ===============
    running = True
    game_over = False

    while running:
        # setting detla time
        dt = clock.tick(FPS) / 1000.0

        # event handling for key presses
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_r:
                    # reset game
                    ship.reset()

        # event handling for held keys
        keys = pygame.key.get_pressed()

        # physics update
        if not game_over:
            ship.update(dt, keys)

        # rendering

        # draw background
        screen.fill(BACKGROUND_COLOR)

        # draw stars
        for x, y, brightness, size in stars:
            color = (brightness, brightness, brightness)
            pygame.draw.circle(screen, color, (x, y), size)

        # draw ship
        ship.draw(screen)

        # update display
        pygame.display.flip()

    # cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
