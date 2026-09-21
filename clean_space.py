"""
clean_space.py
Asteroids-like game where you clean garbage in space

Controls:
- W: Move forward
- A/D: Turn left / right
- ESC: Quit
"""

import pygame
import sys
from pygame.locals import *
import random

# Initialize pygame
pygame.init()

# ==================================
# Constants
# ==================================

# screen constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60
BACKGROUND_COLOR = (0, 0, 0)
WORLD_WIDTH = 6000
WORLD_HEIGHT = 4500
WORLD_STAR_COUNT = 2000

# ship constants
SHIP_SIZE = 40
SHIP_COLOR = (0, 200, 255)
RESPAWN_PROTECTION_TIME = 2.0

# asteroid constants
ASTEROID_MIN_SIZE = 20
ASTEROID_MAX_SIZE = 60
ASTEROID_MIN_SPEED = 80
ASTEROID_MAX_SPEED = 110
ASTEROID_SPAWN_TIME = 1.5
ASTEROID_COLOR = (130, 130, 130)

# garbage constants
GARBAGE_RADIUS = 15
GARBAGE_MIN_SPEED = 50
GARBAGE_MAX_SPEED = 120
GARBAGE_SPAWN_TIME = 2.0
GARBAGE_COLOR = (80, 220, 100)
GARBAGE_SCORE = 100
COLLECTIBLE_OFFSCREEN_TIME = 5.0

# Physics constants
SHIP_ACCEL = 600
SHIP_DRAG = .98
MAX_SPEED = 1000
ROTATION_SPEED = 195

class Camera:
    """camera that follows player around the world"""

    def __init__(self):
        self.pos = pygame.Vector2(0, 0)

    def update(self, target_pos):
        # trying to center camera on target
        self.pos.x = target_pos.x - SCREEN_WIDTH / 2
        self.pos.y = target_pos.y - SCREEN_HEIGHT / 2

        # preventing camera from showing anything outside its view
        self.pos.x = max(0, min(self.pos.x, WORLD_WIDTH - SCREEN_WIDTH))
        self.pos.y = max(0, min(self.pos.y, WORLD_HEIGHT - SCREEN_HEIGHT))

    def apply(self, world_pos):
        """converting world position to screen position"""

        return world_pos - self.pos

def spawn_outside_camera(camera, radius):
    """reate a position just outside a random camera edge"""

    spawn_distance = radius * 1.25
    edge = random.choice(["top", "bottom", "left", "right"])

    left = camera.pos.x
    right = camera.pos.x + SCREEN_WIDTH
    top = camera.pos.y
    bottom = camera.pos.y + SCREEN_HEIGHT

    if edge == "top":
        pos = pygame.Vector2(
            random.uniform(left, right),
            top - spawn_distance
        )

        direction = pygame.Vector2(
            random.uniform(-0.5, 0.5),
            1
        )

    elif edge == "bottom":
        pos = pygame.Vector2(
            random.uniform(left, right),
            bottom + spawn_distance
        )

        direction = pygame.Vector2(
            random.uniform(-0.5, 0.5),
            -1
        )

    elif edge == "left":
        pos = pygame.Vector2(
            left - spawn_distance,
            random.uniform(top, bottom)
        )

        direction = pygame.Vector2(
            1,
            random.uniform(-0.5, 0.5)
        )

    else:
        pos = pygame.Vector2(
            right + spawn_distance,
            random.uniform(top, bottom)
        )

        direction = pygame.Vector2(
            -1,
            random.uniform(-0.5, 0.5)
        )

    direction.normalize_ip()

    return pos, direction

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
        self.angle = 0

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

    def update(self, dt, keys):
        """Update physics simulation"""

        # start each frame with zero acceleration
        self.acc = pygame.Vector2(0, 0)

        # player input for turning let and right
        if keys[K_a]:
            self.angle -= ROTATION_SPEED * dt
        if keys[K_d]:
            self.angle += ROTATION_SPEED * dt

        # direction ship is facing
        forward = pygame.Vector2(0, -1).rotate(self.angle)

        # forward acceleration
        if keys[K_w]:
            self.acc = forward * SHIP_ACCEL

        self.vel += self.acc * dt

        # limit max speed
        if self.vel.length() > MAX_SPEED:
            self.vel.scale_to_length(MAX_SPEED)

        # save current trail position
        self.trail.append((self.pos.copy(), self.angle))

        # limit trail length
        if len(self.trail) > self.max_trail_length:
            self.trail.pop(0)

        # update velocity and position
        self.pos += self.vel * dt

        # wrap around screen
        self.keep_inside_world()
        
        # apply drag to ship to slow it
        self.vel *= SHIP_DRAG ** (dt * FPS)

        # keep ship position synced with Vector2 pos
        self.rect.center = (round(self.pos.x), round(self.pos.y))

    def reset(self):
        """reset ship to starting position"""
        self.pos = pygame.Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.trail = []
        self.angle = 0
        self.rect.center = self.pos

    def draw(self, screen, camera):
        """draw ship and trail"""

        # draw trail
        for i, (pos, angle) in enumerate(self.trail):
            progress = (i + 1) / len(self.trail)

            brightness = int(50 * progress)

            color = (
                min(255, self.color[0] + brightness),
                min(255, self.color[1] + brightness),
                min(255, self.color[2] + brightness)
            )

            # Older trail shapes are smaller
            size = self.size * (0.3 + 0.7 * progress)
            half_size = size / 2

            # Use the angle stored with this trail position
            forward = pygame.Vector2(0, -1).rotate(angle)
            right = forward.rotate(90)

            # convert trail world position to screen position
            screen_pos = camera.apply(pos)

            nose = screen_pos + forward * half_size
            back_center = screen_pos - forward * half_size
            back_left = back_center - right * half_size
            back_right = back_center + right * half_size

            pygame.draw.polygon(
                screen,
                color,
                [nose, back_left, back_right]
            )

        # calculate triangle points
        forward = pygame.Vector2(0, -1).rotate(self.angle)
        right = forward.rotate(90)

        half_size = self.size / 2
        screen_pos = camera.apply(self.pos)

        nose = screen_pos + forward * half_size
        back_center = screen_pos - forward * half_size
        back_left = back_center - right * half_size
        back_right = back_center + right * half_size

        # draw ship
        pygame.draw.polygon(
            screen,
            self.color,
            [nose, back_left, back_right]
        )


    def keep_inside_world(self):
        """preventing ship from leaving world"""

        half_size = self.size / 2

        if self.pos.x < half_size:
            self.pos.x = half_size
            self.vel.x = max(0, self.vel.x)

        elif self.pos.x > WORLD_WIDTH - half_size:
            self.pos.x = WORLD_WIDTH - half_size
            self.vel.x = min(0, self.vel.x)

        if self.pos.y < half_size:
            self.pos.y = half_size
            self.vel.y = max(0, self.vel.y)

        elif self.pos.y > WORLD_HEIGHT - half_size:
            self.pos.y = WORLD_HEIGHT - half_size
            self.vel.y = min(0, self.vel.y)

class Asteroid:
    """defining asteroids"""

    def __init__(self, camera):
        # setting asteroid size, color, and spin
        self.radius = random.randint(
            ASTEROID_MIN_SIZE,
            ASTEROID_MAX_SIZE
        )

        self.color = ASTEROID_COLOR
        self.angle = 0
        self.rotation_speed = random.uniform(-90, 90)

        # creating random polygon shapes to be the asteroids
        self.shape = []
        number_of_points = random.randint(7, 12)

        for i in range(number_of_points):
            point_angle = (360 / number_of_points) * i
            point_radius = self.radius * random.uniform(0.7, 1.15)

            point = pygame.Vector2(point_radius, 0)
            point.rotate_ip(point_angle)

            self.shape.append(point)

        self.pos, direction = spawn_outside_camera(camera, self.radius)

        speed = random.uniform(
            ASTEROID_MIN_SPEED,
            ASTEROID_MAX_SPEED
        )

        self.vel = direction * speed

        # approximating collision rectangle

        self.rect = pygame.Rect(
            0,
            0,
            self.radius * 2,
            self.radius * 2
        )
        self.rect.center = self.pos

    def update(self, dt):
        """moving and rotating asteroids"""

        self.pos += self.vel * dt
        self.angle += self.rotation_speed * dt

        self.rect.center = (
            round(self.pos.x),
            round(self.pos.y)
        )

    def draw(self, screen, camera):
        """drawing asteroids"""

        rotated_points = []
        screen_pos = camera.apply(self.pos)

        for point in self.shape:
            rotated_point = point.rotate(self.angle)
            rotated_points.append(screen_pos + rotated_point)

        pygame.draw.polygon(
            screen,
            self.color,
            rotated_points
        )

    def is_offscreen(self, camera):
        """ return True after asteroid leaves camera area"""

        margin = self.radius * 3

        return(
            self.pos.x < camera.pos.x - margin
            or self.pos.x > camera.pos.x + SCREEN_WIDTH + margin
            or self.pos.y < camera.pos.y - margin 
            or self.pos.y > camera.pos.y + SCREEN_HEIGHT + margin
            )

class Garbage:
    """defining garbage collectible"""

    def __init__(self, camera):
        self.radius = GARBAGE_RADIUS

        self.color = GARBAGE_COLOR

        self.pos, direction = spawn_outside_camera(camera, self.radius)

        speed = random.uniform(
            GARBAGE_MIN_SPEED,
            GARBAGE_MAX_SPEED
        )

        self.vel = direction * speed

        self.rect = pygame.Rect(
            0,
            0,
            self.radius * 2,
            self.radius * 2
        )

        self.rect.center = self.pos

        self.offscreen_timer = 0

    def update(self, dt, camera):
        """move garbage across the screen"""

        self.pos += self.vel * dt

        self.rect.center = (
            round(self.pos.x),
            round(self.pos.y)
        )

        if self.is_offscreen(camera):
            self.offscreen_timer += dt
        else:
            self.offscreen_timer = 0

    def draw(self, screen, camera):
        """draw garbage as a circle, relative to the camera"""

        screen_pos = camera.apply(self.pos)

        pygame.draw.circle(
            screen,
            self.color,
            (round(screen_pos.x), round(screen_pos.y)),
            self.radius
        )

    def is_offscreen(self, camera):
        """return True after garbage leaves the camera view"""

        margin = self.radius * 3

        return (
            self.pos.x + self.radius < camera.pos.x
            or self.pos.x - self.radius > camera.pos.x + SCREEN_WIDTH 
            or self.pos.y + self.radius < camera.pos.y
            or self.pos.y - self.radius > camera.pos.y + SCREEN_HEIGHT
        )

    def should_delete(self):
        '''returns true after off screen time is longer than five seconds'''

        return self.offscreen_timer >= COLLECTIBLE_OFFSCREEN_TIME

def main():
    """main game loop"""

    # set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Clean Space')
    clock = pygame.time.Clock()
    hud_font = pygame.font.Font(None, 36)
    game_over_font = pygame.font.Font(None, 80)
    restart_font = pygame.font.Font(None, 36)

    # defining ship, setting spawn
    ship = Spaceship(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

    # defining camera
    camera = Camera()
    camera.update(ship.pos)

    # setting up for asteroids
    asteroids = []
    asteroid_spawn_timer = 0

    # setting up for garbage
    garbage_bags = []
    garbage_spawn_timer = 0

    score = 0

    # setting up star field
    stars = []

    for i in range(WORLD_STAR_COUNT):
        pos = pygame.Vector2(
            random.randint(0, WORLD_WIDTH),
            random.randint(0, WORLD_HEIGHT)
        )

        brightness = random.randint(100, 255)
        size = random.randint(1, 2)

        stars.append((pos, brightness, size))

    # ===============
    # MAIN GAME LOOP
    # ===============
    running = True
    game_over = False

    lives = 3
    invuln_timer = 0

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
                    if game_over:
                        # reset game
                        lives = 3
                        game_over = False
                        asteroids.clear()
                        asteroid_spawn_timer = 0
                        invuln_timer = 0
                        garbage_bags.clear()
                        garbage_spawn_timer = 0
                        score = 0

                    ship.reset()

        # event handling for held keys
        keys = pygame.key.get_pressed()

        # physics update
        if not game_over:
            # updating ship physics
            ship.update(dt, keys)

            # update camera position
            camera.update(ship.pos)

            asteroid_spawn_timer += dt
            garbage_spawn_timer += dt

            # spawning asteroids
            if asteroid_spawn_timer >= ASTEROID_SPAWN_TIME:
                asteroids.append(Asteroid(camera))
                asteroid_spawn_timer = 0

            for asteroid in asteroids:
                asteroid.update(dt)

            # removing asteroids off screen
            asteroids = [
                asteroid
                for asteroid in asteroids
                if not asteroid.is_offscreen(camera)
            ]

            # reduce respawn protection
            if invuln_timer > 0:
                invuln_timer -= dt

            # check ship and asteroid collision
            if invuln_timer <= 0:
                for asteroid in asteroids[:]:
                    if ship.rect.colliderect(asteroid.rect):
                        lives -= 1
                        asteroids.remove(asteroid)

                        if lives <= 0:
                            game_over = True
                            ship.vel = pygame.Vector2(0, 0)
                        else:
                            ship.reset()
                            invuln_timer = RESPAWN_PROTECTION_TIME
                        break

            # spawn garbage
            if garbage_spawn_timer >= GARBAGE_SPAWN_TIME:
                garbage_bags.append(Garbage(camera))
                garbage_spawn_timer = 0

            # update garbage
            for garbage in garbage_bags:
                garbage.update(dt, camera)

            # remove off-screen garbage
            garbage_bags = [
                garbage
                for garbage in garbage_bags
                if not garbage.should_delete()
            ]

            for garbage in garbage_bags[:]:
                distance = ship.pos.distance_to(garbage.pos)

                if distance <= (ship.size / 2) + garbage.radius:
                    score += GARBAGE_SCORE
                    garbage_bags.remove(garbage)

            # update camera in case collision reset the ship 
            camera.update(ship.pos)
            
        # rendering

        # draw background
        screen.fill(BACKGROUND_COLOR)

        # draw stars
        for world_pos, brightness, size in stars:
            screen_pos = camera.apply(world_pos)

            if (0 <= screen_pos.x <= SCREEN_WIDTH and 0 <= screen_pos.y <= SCREEN_HEIGHT):
                color = (brightness, brightness, brightness)

                pygame.draw.circle(
                    screen,
                    color,
                    (round(screen_pos.x), round(screen_pos.y)),
                    size
                )

        # draw asteroids
        for asteroid in asteroids:
            asteroid.draw(screen, camera)

        # draw garbage
        for garbage in garbage_bags:
            garbage.draw(screen, camera)

        # draw lives counter
        lives_text = hud_font.render(
            f"Lives: {lives}",
            True,
            (255, 255, 255)
        )

        # draw score
        score_text = hud_font.render(
            f"Score: {score}",
            True,
            (255, 255, 255)
        )

        score_rect = score_text.get_rect(topright = (SCREEN_WIDTH - 20, 20))

        screen.blit(score_text, score_rect)
        screen.blit(lives_text, (20, 20))

        # draw ship
        if not game_over:
            ship.draw(screen, camera)

        # draw game over screen
        if game_over:
            # dark transparent overlay
            overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            game_over_text = game_over_font.render(
                "GAME OVER",
                True,
                (255, 80, 80)
            )

            restart_text = restart_font.render(
                "Press R to restart",
                True,
                (255, 80, 80)
            )

            game_over_rect = game_over_text.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
            restart_rect = restart_text.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))

            screen.blit(game_over_text, game_over_rect)
            screen.blit(restart_text, restart_rect)

        # update display
        pygame.display.flip()

    # cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
