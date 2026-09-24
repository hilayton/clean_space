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
import math

# initialize pygame
pygame.init()

# ==================================
# CONSTANTS
# ==================================

# screen constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60
BACKGROUND_COLOR = (0, 0, 0)

# world constants
WORLD_WIDTH = 100000
WORLD_HEIGHT = 100000

# star constants
CAMERA_STAR_COUNT = 150
STAR_MIN_PARALLAX = 0.15
STAR_MAX_PARALLAX = 0.55

# station constants
STATION_X = WORLD_WIDTH // 2
STATION_Y = WORLD_HEIGHT // 2
STATION_RADIUS = 100
DOCKING_RADIUS = 175

STATION_COLOR = (90, 110, 150)
STATION_OUTLINE_COLOR = (180, 210, 255)
DOCKING_COLOR = (60, 130, 200)

STATION_BARRIER_BOUNCE = 0.9

# ship constants
SHIP_SIZE = 40
SHIP_COLOR = (0, 200, 255)
RESPAWN_PROTECTION_TIME = 2.0
# ship heath constants
STARTING_MAX_HEALTH = 100
ASTEROID_COLLISION_DAMAGE = 25
HIT_INVULN_TIME = 0.75
# starting ship above station, facing away from it
SHIP_START_X = STATION_X
SHIP_START_Y = STATION_Y - DOCKING_RADIUS + 25

# fuel constants
STARTING_MAX_FUEL = 100
STARTING_FUEL_BURN_RATE = 5.0
FUEL_PRICE_PER_UNIT = 1

# repair constants
REPAIR_COST = 5

# recovery constants
RESCUE_PENALTY_RATE = 0.05
EMERGENCY_FUEL = 10

# recovery screen constants
RECOVERY_MESSAGE_TIME = 3.0
RECOVERY_FADE_TIME = 0.5

# minimap constants
MINIMAP_RADIUS = 100
MINIMAP_MARGIN = 20
MINIMAP_WORLD_RANGE = 1500

MINIMAP_BACKGROUND = (10, 115, 30)
MINIMAP_BORDER = (180, 210, 255)
MINIMAP_RING_COLOR = (50, 65, 90)

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
GARBAGE_VALUE = 100
GARBAGE_CARGO_SPACE = 1

# collectible constants
STARTING_CARGO_CAPACITY = 5
COLLECTIBLE_OFFSCREEN_TIME = 5.0

# Physics constants
SHIP_ACCEL = 350
SHIP_DRAG = .98
STARTING_MAX_SPEED = 600
STARTING_ROTATION_SPEED = 120

# collision physics
SHIP_MASS = 2.0
COLLISION_BOUNCE = 0.8

# ship upgrade constants
UPGRADE_COSTS = (500, 1200, 2500)
MAX_UPGRADE_LEVEL = len(UPGRADE_COSTS)

UPGRADE_ORDER = (
    "fuel_efficiency",
    "fuel_capacity",
    "cargo_capacity",
    "armor",
    "turning",
    "acceleration",
    "top_speed"
)

UPGRADE_LABELS = {
    "fuel_efficiency": "Fuel Efficiency",
    "fuel_capacity": "Fuel Capacity",
    "cargo_capacity": "Cargo Capacity",
    "armor": "Armor",
    "turning": "Turning",
    "acceleration": "Acceleration",
    "top_speed": "Top Speed"
}

UPGRADE_VALUES = {
    "fuel_efficiency": (5.0, 4.0, 3.0, 2.25),
    "fuel_capacity": (100, 140, 180, 240),
    "cargo_capacity": (5, 7, 10, 14),
    "armor": (100, 125, 160, 200),
    "turning": (120, 145, 170, 195),
    "acceleration": (350, 450, 525, 600),
    "top_speed": (600, 750, 875, 1000)
}

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

class Station:
    """station used for cargo delivery and ship upgrades"""

    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.radius = STATION_RADIUS
        self.docking_radius = DOCKING_RADIUS

    def ship_in_docking_range(self, ship):
        """returns true when ship is in range to dock"""

        distance = self.pos.distance_to(ship.pos)
        return distance <= self.docking_radius

    def reflect_asteroid(self, asteroid):
        """reflect an asteroid off the station docking zone."""

        offset = asteroid.pos - self.pos
        distance = offset.length()

        # include the asteroid radius so its surface,
        # rather than its center, touches the barrier.
        minimum_distance = (
            self.docking_radius
            + asteroid.radius
        )

        if distance >= minimum_distance:
            return

        # prevent division by zero if an asteroid is
        # somehow directly on the station center.
        if distance == 0:
            collision_normal = pygame.Vector2(1, 0)
        else:
            collision_normal = offset / distance

        # move the asteroid outside the barrier.
        asteroid.pos = (
            self.pos
            + collision_normal * minimum_distance
        )

        velocity_toward_barrier = (
            asteroid.vel.dot(collision_normal)
        )

        # negative means the asteroid is moving inward.
        if velocity_toward_barrier < 0:
            asteroid.vel -= (
                (1 + STATION_BARRIER_BOUNCE)
                * velocity_toward_barrier
                * collision_normal
            )

        asteroid.rect.center = (
            round(asteroid.pos.x),
            round(asteroid.pos.y)
        )

    def draw(self, screen, camera):
        """draw station relative to camera"""

        screen_pos = camera.apply(self.pos)
        center = (round(screen_pos.x), round(screen_pos.y))

        # draw docking range
        pygame.draw.circle(screen, DOCKING_COLOR, center, self.docking_radius, 2)

        # draw four station arms
        arm_length = self.radius + 35

        pygame.draw.line(
            screen, 
            STATION_OUTLINE_COLOR, 
            (center[0] - arm_length, center[1]),
            (center[0] + arm_length, center[1]),
            22
            )

        pygame.draw.line(
            screen,
            STATION_OUTLINE_COLOR,
            (center[0], center[1] - arm_length),
            (center[0], center[1] + arm_length),
            22
        )

        # draw main station body
        pygame.draw.circle(
            screen,
            STATION_COLOR, 
            center,
            self.radius
        )

        pygame.draw.circle(
            screen,
            STATION_OUTLINE_COLOR,
            center,
            self.radius,
            5
        )

        # draw center section of station
        pygame.draw.circle(
            screen,
            (35, 45, 70),
            center,
            35
        )

        pygame.draw.circle(
            screen,
            STATION_OUTLINE_COLOR,
            center,
            35,
            4
        )

class StarField:
    """camera-centered starfield with wrapping stars."""

    def __init__(self, camera):
        self.stars = []
        self.last_camera_pos = camera.pos.copy()

        for i in range(CAMERA_STAR_COUNT):
            pos = pygame.Vector2(
                random.uniform(0, SCREEN_WIDTH),
                random.uniform(0, SCREEN_HEIGHT)
            )

            parallax = random.uniform(
                STAR_MIN_PARALLAX,
                STAR_MAX_PARALLAX
            )

            # closer stars appear brighter and slightly larger.
            brightness = round(
                100 + 155 * parallax
            )

            if parallax > 0.4:
                size = 2
            else:
                size = 1

            self.stars.append(
                [pos, brightness, size, parallax]
            )

    def draw(self, screen, camera):
        """move and draw stars relative to camera movement."""

        camera_movement = (
            camera.pos - self.last_camera_pos
        )

        for star in self.stars:
            pos = star[0]
            brightness = star[1]
            size = star[2]
            parallax = star[3]

            # Move stars opposite the camera.
            pos -= camera_movement * parallax

            # Wrap stars around the screen edges.
            pos.x %= SCREEN_WIDTH
            pos.y %= SCREEN_HEIGHT

            color = (
                brightness,
                brightness,
                brightness
            )

            pygame.draw.circle(
                screen,
                color,
                (
                    round(pos.x),
                    round(pos.y)
                ),
                size
            )

        self.last_camera_pos = camera.pos.copy()

class StationMenu:
    """mouse-operated menu for station services and upgrades."""

    def __init__(self):
        self.is_open = False
        self.page = "services"

        self.panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 400,
            SCREEN_HEIGHT // 2 - 400,
            800,
            800
        )

        button_x = self.panel_rect.x + 60
        button_width = self.panel_rect.width - 120
        button_height = 55

        # Station-services buttons
        self.sell_button = pygame.Rect(
            button_x,
            self.panel_rect.y + 280,
            button_width,
            button_height
        )

        self.fuel_button = pygame.Rect(
            button_x,
            self.panel_rect.y + 350,
            button_width,
            button_height
        )

        self.upgrade_button = pygame.Rect(
            button_x,
            self.panel_rect.y + 420,
            button_width,
            button_height
        )

        self.repair_button = pygame.Rect(
            button_x,
            self.panel_rect.y + 490,
            button_width,
            button_height
        )

        self.close_button = pygame.Rect(
            button_x,
            self.panel_rect.y + 570,
            button_width,
            button_height
        )

        # Upgrade-page buttons
        self.upgrade_buttons = {}

        upgrade_y = self.panel_rect.y + 150

        for upgrade_name in UPGRADE_ORDER:
            self.upgrade_buttons[upgrade_name] = pygame.Rect(
                button_x,
                upgrade_y,
                button_width,
                button_height
            )

            upgrade_y += 70

        self.back_button = pygame.Rect(
            button_x,
            self.panel_rect.bottom - 70,
            button_width,
            button_height
        )

    def open_menu(self, ship):
        """open the station menu and stop the ship."""

        self.is_open = True
        self.page = "services"

        ship.vel = pygame.Vector2(0, 0)
        ship.acc = pygame.Vector2(0, 0)

    def close_menu(self):
        """close the station menu."""

        self.is_open = False
        self.page = "services"

    def buy_fuel(self, ship, credits):
        """purchase as much missing fuel as the player can afford."""

        missing_fuel = math.ceil(
            ship.max_fuel - ship.fuel
        )

        affordable_fuel = (
            credits // FUEL_PRICE_PER_UNIT
        )

        fuel_purchased = min(
            missing_fuel,
            affordable_fuel
        )

        fuel_cost = (
            fuel_purchased
            * FUEL_PRICE_PER_UNIT
        )

        ship.fuel += fuel_purchased
        ship.fuel = min(
            ship.fuel,
            ship.max_fuel
        )

        return credits - fuel_cost

    def repair_ship(self, ship, credits):
        """repair ship while docked"""

        missing_health = math.ceil(ship.max_health - ship.health)
        affordable_health = credits // REPAIR_COST
        amount_repiared = min(missing_health, affordable_health)

        ship.health = min(ship.max_health, ship.health + amount_repiared)

        repair_cost = amount_repiared * REPAIR_COST
        return credits - repair_cost

    def handle_click(self, mouse_pos, ship, credits):
        """Handle mouse clicks on the current menu page."""

        if self.page == "services":
            if self.sell_button.collidepoint(mouse_pos):
                if ship.cargo:
                    credits += ship.unload_cargo()

            elif self.fuel_button.collidepoint(mouse_pos):
                if ship.fuel < ship.max_fuel and credits > 0:
                    credits = self.buy_fuel(
                        ship,
                        credits
                    )

            elif self.upgrade_button.collidepoint(mouse_pos):
                self.page = "upgrades"

            elif self.repair_button.collidepoint(mouse_pos):
                if ship.health < ship.max_health and credits >= REPAIR_COST:
                    credits = self.repair_ship(
                        ship,
                        credits
                    )

            elif self.close_button.collidepoint(mouse_pos):
                self.close_menu()

        elif self.page == "upgrades":
            for upgrade_name, button in self.upgrade_buttons.items():
                if button.collidepoint(mouse_pos):
                    credits = ship.purchase_upgrade(
                        upgrade_name,
                        credits
                    )

                    break

            if self.back_button.collidepoint(mouse_pos):
                self.page = "services"

        return credits

    def draw_button(
        self,
        screen,
        rect,
        text,
        font,
        enabled=True
    ):
        """draw a button with mouse-hover highlighting."""

        mouse_pos = pygame.mouse.get_pos()
        hovered = rect.collidepoint(mouse_pos)

        if not enabled:
            color = (55, 55, 65)
            text_color = (130, 130, 140)

        elif hovered:
            color = (75, 130, 190)
            text_color = (255, 255, 255)

        else:
            color = (45, 75, 115)
            text_color = (220, 235, 255)

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            STATION_OUTLINE_COLOR,
            rect,
            2,
            border_radius=8
        )

        text_surface = font.render(
            text,
            True,
            text_color
        )

        text_rect = text_surface.get_rect(
            center=rect.center
        )

        screen.blit(text_surface, text_rect)

    def format_upgrade_value(
        self,
        upgrade_name,
        value
    ):
        """format an upgrade value for display."""

        if upgrade_name == "fuel_efficiency":
            return f"{value:.2f} fuel/sec"

        if upgrade_name == "turning":
            return f"{value} deg/sec"

        return str(value)

    def draw_services_page(
        self,
        screen,
        ship,
        credits,
        menu_font,
        small_font
    ):
        """draw cargo, fuel, and navigation services."""

        cargo_status = menu_font.render(
            (
                f"Cargo: {ship.get_used_cargo_space()}"
                f"/{ship.cargo_capacity}"
                f"   Value: {ship.get_cargo_value()}"
            ),
            True,
            (255, 255, 255)
        )

        fuel_status = menu_font.render(
            (
                f"Fuel: {math.ceil(ship.fuel)}"
                f"/{ship.max_fuel}"
            ),
            True,
            (255, 255, 255)
        )

        health_status = menu_font.render(
            (
                f"Health: {ship.health}"
                f"/{ship.max_health}"
            ),
            True,
            (255, 255, 255)
        )

        credit_status = menu_font.render(
            f"Credits: {credits}",
            True,
            (255, 255, 255)
        )

        screen.blit(
            cargo_status,
            (
                self.panel_rect.x + 45,
                self.panel_rect.y + 100
            )
        )

        screen.blit(
            fuel_status,
            (
                self.panel_rect.x + 45,
                self.panel_rect.y + 145
            )
        )

        screen.blit(
            health_status,
            (
                self.panel_rect.x + 45,
                self.panel_rect.y + 190
            )
        )

        screen.blit(
            credit_status,
            (
                self.panel_rect.x + 45,
                self.panel_rect.y + 235
            )
        )

        missing_fuel = math.ceil(
            ship.max_fuel - ship.fuel
        )

        full_refuel_cost = (
            missing_fuel
            * FUEL_PRICE_PER_UNIT
        )

        self.draw_button(
            screen,
            self.sell_button,
            (
                "Sell Cargo "
                f"(+{ship.get_cargo_value()} credits)"
            ),
            small_font,
            enabled = bool(ship.cargo)
        )

        self.draw_button(
            screen,
            self.fuel_button,
            (
                "Buy Fuel "
                f"({full_refuel_cost} credits)"
            ),
            small_font,
            enabled = (
                missing_fuel > 0
                and credits >= FUEL_PRICE_PER_UNIT
            )
        )

        self.draw_button(
            screen,
            self.upgrade_button,
            "Ship Upgrades",
            small_font
        )

        self.draw_button(
            screen,
            self.repair_button,
            "Repair Ship",
            small_font,
            enabled = (
                ship.health <= ship.max_health
                and credits >= REPAIR_COST
            )
        )

        self.draw_button(
            screen,
            self.close_button,
            "Undock",
            small_font
        )

    def draw_upgrades_page(
        self,
        screen,
        ship,
        credits,
        menu_font,
        small_font
    ):
        """draw all purchasable ship upgrades."""

        credit_status = menu_font.render(
            f"Available Credits: {credits}",
            True,
            (255, 255, 255)
        )

        credit_rect = credit_status.get_rect(
            center=(
                self.panel_rect.centerx,
                self.panel_rect.y + 105
            )
        )

        screen.blit(
            credit_status,
            credit_rect
        )

        for upgrade_name in UPGRADE_ORDER:
            button = self.upgrade_buttons[
                upgrade_name
            ]

            level = ship.upgrade_levels[
                upgrade_name
            ]

            label = UPGRADE_LABELS[
                upgrade_name
            ]

            current_value = UPGRADE_VALUES[
                upgrade_name
            ][level]

            current_text = self.format_upgrade_value(
                upgrade_name,
                current_value
            )

            if level >= MAX_UPGRADE_LEVEL:
                button_text = (
                    f"{label}  Lv {level}/{MAX_UPGRADE_LEVEL}"
                    f"  |  {current_text}  |  MAX"
                )

                enabled = False

            else:
                next_value = UPGRADE_VALUES[
                    upgrade_name
                ][level + 1]

                next_text = self.format_upgrade_value(
                    upgrade_name,
                    next_value
                )

                cost = UPGRADE_COSTS[level]

                button_text = (
                    f"{label}  Lv {level}/{MAX_UPGRADE_LEVEL}"
                    f"  |  {current_text} -> {next_text}"
                    f"  |  {cost} cr"
                )

                enabled = credits >= cost

            self.draw_button(
                screen,
                button,
                button_text,
                small_font,
                enabled=enabled
            )

        self.draw_button(
            screen,
            self.back_button,
            "Back to Station Services",
            small_font
        )

    def draw(
        self,
        screen,
        ship,
        credits,
        title_font,
        menu_font,
        small_font
    ):
        """draw the current station-menu page."""

        if not self.is_open:
            return

        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen,
            (20, 30, 50),
            self.panel_rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            STATION_OUTLINE_COLOR,
            self.panel_rect,
            3,
            border_radius=12
        )

        if self.page == "services":
            title_text = "STATION SERVICES"
        else:
            title_text = "SHIP UPGRADES"

        title = title_font.render(
            title_text,
            True,
            STATION_OUTLINE_COLOR
        )

        title_rect = title.get_rect(
            center=(
                self.panel_rect.centerx,
                self.panel_rect.y + 45
            )
        )

        screen.blit(title, title_rect)

        if self.page == "services":
            self.draw_services_page(
                screen,
                ship,
                credits,
                menu_font,
                small_font
            )

        else:
            self.draw_upgrades_page(
                screen,
                ship,
                credits,
                menu_font,
                small_font
            )

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

class Collectible:
    """parent class for all collectibles"""

    def __init__(
            self,
            camera,
            radius,
            color,
            min_speed,
            max_speed,
            value,
            cargo_space
    ):

        self.radius = radius
        self.color = color
        self.value = value
        self.cargo_space = cargo_space

        self.offscreen_timer = 0

        self.pos, direction = spawn_outside_camera(
            camera,
            self.radius
        )

        speed = random.uniform(min_speed, max_speed)

        self.vel = direction * speed

        self.rect = pygame.Rect(
            0,
            0,
            self.radius * 2,
            self.radius * 2
        )

        self.rect.center = self.pos

    def update(self, dt, camera):
        """move collectible and update off-screen time"""

        self.pos += self.vel * dt

        self.rect.center = (round(self.pos.x), round(self.pos.y))

        if self.is_offscreen(camera):
            self.offscreen_timer += dt
        else:
            self.offscreen_timer = 0

    def is_offscreen(self, camera):
        """returns True when collectible fully offscreen"""

        return(
            self.pos.x + self.radius < camera.pos.x
            or self.pos.x - self.radius > camera.pos.x + SCREEN_WIDTH
            or self.pos.y + self.radius < camera.pos.y
            or self.pos.y - self.radius > camera.pos.y + SCREEN_HEIGHT
        )

    def should_delete(self):
        """returns True one off-screen timer is met"""

        return(self.offscreen_timer >= COLLECTIBLE_OFFSCREEN_TIME)

    def draw(self, screen, camera):
        """subclasses to provide their own draw method"""

        raise NotImplementedError

class Minimap:
    """player centered radar that shows nearby objects"""

    def __init__(self):
        self.center = pygame.Vector2(
            MINIMAP_RADIUS + MINIMAP_MARGIN,
            SCREEN_HEIGHT - MINIMAP_RADIUS - MINIMAP_MARGIN
        )

    def world_to_map(self, world_pos, ship_pos):
        """convert world position to radar position"""

        offset = world_pos - ship_pos
        scale = MINIMAP_RADIUS / MINIMAP_WORLD_RANGE

        return self.center + offset * scale

    def object_in_range(self, world_pos, ship_pos):
        """ return True when an object is withing radar range"""

        distance = world_pos.distance_to(ship_pos)

        return distance <= MINIMAP_WORLD_RANGE

    def draw_station_indicator(self, screen, ship, station):
        """draw station dor or directional arrow"""

        station_offset = station.pos - ship.pos
        station_distance = station_offset.length()

        if station_distance <= MINIMAP_WORLD_RANGE:
            station_map_pos = self.world_to_map(station.pos, ship.pos)

            pygame.draw.circle(
                screen,
                STATION_OUTLINE_COLOR,
                (
                    round(station_map_pos.x),
                    round(station_map_pos.y)
                ),
                5
            )

        elif station_distance > 0:
            # arrow pointing from player to station
            direction = station_offset.normalize()

            arrow_center = (self.center + direction * (MINIMAP_RADIUS - 12))

            perpendicular = direction.rotate(90)

            tip = arrow_center + direction * 8
            back_center = arrow_center - direction * 6
            back_left = back_center + perpendicular * 5
            back_right = back_center - perpendicular * 5

            pygame.draw.polygon(
                screen,
                STATION_OUTLINE_COLOR,
                [tip, back_left, back_right]
            )

    def draw(
            self,
            screen,
            ship,
            station,
            asteroids,
            collectibles
    ):
        """draw player centered radar"""
        center = (round(self.center.x), round(self.center.y))

        # radar background
        pygame.draw.circle(
            screen,
            MINIMAP_BACKGROUND,
            center,
            MINIMAP_RADIUS
        )

        # distance rings
        pygame.draw.circle(
            screen,
            MINIMAP_RING_COLOR,
            center,
            MINIMAP_RADIUS * 3 // 4,
            1
        )

        pygame.draw.circle(
            screen,
            MINIMAP_RING_COLOR,
            center,
            MINIMAP_RADIUS * 3 // 4,
            1
        )

        # nearby collectibles shown
        for collectible in collectibles:
            if self.object_in_range(collectible.pos, ship.pos):
                map_pos = self.world_to_map(collectible.pos, ship.pos)

                pygame.draw.circle(
                    screen,
                    collectible.color,
                    (
                        round(map_pos.x),
                        round(map_pos.y)
                    ),
                    3
                )

        # nearby asteroids shown
        for asteroid in asteroids:
            if self.object_in_range(asteroid.pos, ship.pos):
                map_pos = self.world_to_map(asteroid.pos, ship.pos)

                pygame.draw.circle(
                    screen,
                    ASTEROID_COLOR,
                    (
                        round(map_pos.x),
                        round(map_pos.y)
                    ),
                    2
                )

        # station dot or arrow
        self.draw_station_indicator(screen, ship, station)

        # ship remains in center and shows current direction
        forward = pygame.Vector2(0, -1).rotate(ship.angle)

        right = forward.rotate(90)

        nose = self.center + forward * 8
        back_center = self.center - forward * 5
        back_left = back_center - right * 5
        back_riight = back_center + right * 5

        pygame.draw.polygon(
            screen,
            SHIP_COLOR,
            [nose, back_left, back_riight]
        )

        # radar border
        pygame.draw.circle(
            screen,
            MINIMAP_BORDER,
            center,
            MINIMAP_RADIUS,
            2
        )
                
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

        # cargo storage
        self.cargo = []

        # ship mass for collision physics
        self.mass = SHIP_MASS
        
        # upgrade levels and starting stats
        self.reset_upgrades()

    def reset_upgrades(self):
        """restore every ship upgrade to its starting level."""

        self.upgrade_levels = {
            upgrade_name: 0
            for upgrade_name in UPGRADE_ORDER
        }

        self.fuel_burn_rate = UPGRADE_VALUES["fuel_efficiency"][0]

        self.max_fuel = UPGRADE_VALUES["fuel_capacity"][0]

        self.cargo_capacity = UPGRADE_VALUES["cargo_capacity"][0]

        self.max_health = UPGRADE_VALUES["armor"][0]

        self.turn_speed = UPGRADE_VALUES["turning"][0]

        self.ship_accel = UPGRADE_VALUES["acceleration"][0]

        self.max_speed = UPGRADE_VALUES["top_speed"][0]

        self.fuel = self.max_fuel
        self.health = self.max_health

    def purchase_upgrade(self, upgrade_name, credits):
        """purchase one level of a ship upgrade."""

        current_level = self.upgrade_levels[upgrade_name]

        if current_level >= MAX_UPGRADE_LEVEL:
            return credits

        cost = UPGRADE_COSTS[current_level]

        if credits < cost:
            return credits

        new_level = current_level + 1

        old_max_fuel = self.max_fuel
        old_max_health = self.max_health

        self.upgrade_levels[upgrade_name] = new_level

        if upgrade_name == "fuel_efficiency":
            self.fuel_burn_rate = UPGRADE_VALUES[upgrade_name][new_level]

        elif upgrade_name == "fuel_capacity":
            self.max_fuel = UPGRADE_VALUES[upgrade_name][new_level]

            added_capacity = (self.max_fuel - old_max_fuel)

            self.fuel += added_capacity

        elif upgrade_name == "cargo_capacity":
            self.cargo_capacity = UPGRADE_VALUES[upgrade_name][new_level]

        elif upgrade_name == "armor":
            self.max_health = UPGRADE_VALUES[upgrade_name][new_level]

            added_health = (self.max_health - old_max_health)

            self.health += added_health

        elif upgrade_name == "turning":
            self.turn_speed = UPGRADE_VALUES[upgrade_name][new_level]

        elif upgrade_name == "acceleration":
            self.ship_accel = UPGRADE_VALUES[upgrade_name][new_level]

        elif upgrade_name == "top_speed":
            self.max_speed = UPGRADE_VALUES[upgrade_name][new_level]

        return credits - cost

    def apply_force(self, force):
        """Apply force to ship"""
        self.acc += force

    def apply_impulse(self, impulse):
        """For sudden velocity changes.
        Might not be used, but likely for when colliding with asteroids"""        

        self.vel += impulse / self.mass

    def get_used_cargo_space(self):
        """returns total cargo space being used"""

        total_space = 0

        for collectible in self.cargo:
            total_space += collectible.cargo_space

        return total_space

    def can_collect(self, collectible):
        """returns True if the ship can collect cargo"""

        new_total = (self.get_used_cargo_space() + collectible.cargo_space)

        return new_total <= self.cargo_capacity

    def collect(self, collectible):
        """add collectible to cargo if there is enough space"""

        if self.can_collect(collectible):
            self.cargo.append(collectible)
            return True

        return False

    def get_cargo_value(self):
        """returns total value of all cargo on ship"""

        total_value = 0

        for collectible in self.cargo:
            total_value += collectible.value

        return total_value

    def unload_cargo(self):
        """sell all collectibles in cargo for credits"""

        credits_earned = self.get_cargo_value()
        self.cargo.clear()

        return credits_earned

    def update(self, dt, keys):
        """Update physics simulation"""

        # start each frame with zero acceleration
        self.acc = pygame.Vector2(0, 0)

        # player input for turning let and right
        if keys[K_a]:
            self.angle -= self.turn_speed * dt
        if keys[K_d]:
            self.angle += self.turn_speed * dt

        # direction ship is facing
        forward = pygame.Vector2(0, -1).rotate(self.angle)

        # forward acceleration
        if keys[K_w] and self.fuel > 0:
            self.acc = forward * self.ship_accel

            self.fuel -= self.fuel_burn_rate * dt
            self.fuel = max(0, self.fuel)

        self.vel += self.acc * dt

        # limit max speed
        if self.vel.length() > self.max_speed:
            self.vel.scale_to_length(self.max_speed)

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
        self.pos = pygame.Vector2(SHIP_START_X, SHIP_START_Y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.trail = []
        self.angle = 0
        self.rect.center = self.pos
        self.health = self.max_health

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
        """prevent ship from leaving world"""

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

        self.mass = (self.radius / ASTEROID_MIN_SIZE) ** 2

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

    def apply_impulse(self, impulse):
        """apply impusle ater collision"""

        self.vel += impulse / self.mass

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

class Garbage(Collectible):
    """defining garbage collectible"""

    def __init__(self, camera):
        super().__init__(
            camera = camera,
            radius = GARBAGE_RADIUS,
            color = GARBAGE_COLOR,
            min_speed = GARBAGE_MIN_SPEED,
            max_speed = GARBAGE_MAX_SPEED,
            value = GARBAGE_VALUE,
            cargo_space = GARBAGE_CARGO_SPACE
        )

    def draw(self, screen, camera):
        """draws garbage as circle"""

        screen_pos = camera.apply(self.pos)

        pygame.draw.circle(
            screen,
            self.color,
            (round(screen_pos.x), round(screen_pos.y)),
            self.radius
        )

def resolve_ship_asteroid_collision(ship, asteroid):
    """bounce the ship and asteroid away from each other."""

    # direction pointing from the asteroid toward the ship
    collision_offset = ship.pos - asteroid.pos
    distance = collision_offset.length()

    # prevent division by zero if their centers exactly overlap
    if distance == 0:
        collision_normal = pygame.Vector2(1, 0)
    else:
        collision_normal = collision_offset / distance

    minimum_distance = ship.size / 2 + asteroid.radius
    overlap = minimum_distance - distance

    # move the objects apart so they are no longer overlapping
    if overlap > 0:
        combined_mass = ship.mass + asteroid.mass

        ship.pos += (
            collision_normal
            * overlap
            * asteroid.mass
            / combined_mass
        )

        asteroid.pos -= (
            collision_normal
            * overlap
            * ship.mass
            / combined_mass
        )

    # calculate their movement relative to each other
    relative_velocity = ship.vel - asteroid.vel
    velocity_along_normal = relative_velocity.dot(collision_normal)

    # positive value means they are already moving apart
    if velocity_along_normal < 0:
        impulse_strength = (
            -(1 + COLLISION_BOUNCE)
            * velocity_along_normal
            / ((1 / ship.mass) + (1 / asteroid.mass))
        )

        impulse = collision_normal * impulse_strength

        ship.apply_impulse(impulse)
        asteroid.apply_impulse(-impulse)

    # sync collision rectangles after separating them
    ship.rect.center = (
        round(ship.pos.x),
        round(ship.pos.y)
    )

    asteroid.rect.center = (
        round(asteroid.pos.x),
        round(asteroid.pos.y)
    )

class RecoverySequence:
    """control the recovery message and screen fade."""

    def __init__(self):
        self.active = False
        self.elapsed = 0

        self.title = ""
        self.status = ""
        self.cargo_lost = 0
        self.credits_lost = 0

        self.open_station_after = False
        self.snapshot = None

    def begin(
        self,
        screen,
        title,
        status,
        cargo_lost,
        credits_lost,
        open_station_after
    ):
        """start a new recovery sequence."""

        self.active = True
        self.elapsed = 0

        self.title = title
        self.status = status
        self.cargo_lost = cargo_lost
        self.credits_lost = credits_lost

        self.open_station_after = open_station_after

        # preserve the last gameplay frame for the fade-out.
        self.snapshot = screen.copy()

    def update(self, dt):
        """advance the recovery timer and report when it finishes."""

        if not self.active:
            return False

        self.elapsed += dt

        if self.elapsed >= RECOVERY_MESSAGE_TIME:
            self.active = False
            self.snapshot = None

            return True

        return False

    def get_fade_alpha(self):
        """calculate the current darkness of the fade overlay."""

        # fade out during the first half second.
        if self.elapsed < RECOVERY_FADE_TIME:
            fade_progress = (
                self.elapsed
                / RECOVERY_FADE_TIME
            )

            return round(255 * fade_progress)

        fade_in_start = (
            RECOVERY_MESSAGE_TIME
            - RECOVERY_FADE_TIME
        )

        # fade back in during the final half second.
        if self.elapsed >= fade_in_start:
            remaining_time = (
                RECOVERY_MESSAGE_TIME
                - self.elapsed
            )

            fade_progress = (
                remaining_time
                / RECOVERY_FADE_TIME
            )

            return round(
                255 * max(0, fade_progress)
            )

        # remain fully black between the two fades.
        return 255

    def draw(
        self,
        screen,
        title_font,
        message_font
    ):
        """draw the fade and recovery information."""

        if not self.active:
            return

        # during fade-out, keep showing the frame from before
        # the ship was moved back to the station.
        if (
            self.elapsed < RECOVERY_FADE_TIME
            and self.snapshot is not None
        ):
            screen.blit(self.snapshot, (0, 0))

        fade_overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        fade_alpha = self.get_fade_alpha()

        fade_overlay.fill(
            (0, 0, 0, fade_alpha)
        )

        screen.blit(fade_overlay, (0, 0))

        # the message is drawn after the fade so it remains visible.
        title_surface = title_font.render(
            self.title,
            True,
            (255, 90, 90)
        )

        status_surface = message_font.render(
            self.status,
            True,
            (220, 235, 255)
        )

        cargo_surface = message_font.render(
            f"Cargo lost: {self.cargo_lost}",
            True,
            (255, 255, 255)
        )

        credits_surface = message_font.render(
            f"Credits lost: {self.credits_lost}",
            True,
            (255, 215, 80)
        )

        title_rect = title_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 90
            )
        )

        status_rect = status_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 30
            )
        )

        cargo_rect = cargo_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 25
            )
        )

        credits_rect = credits_surface.get_rect(
            center=(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + 65
            )
        )

        screen.blit(title_surface, title_rect)
        screen.blit(status_surface, status_rect)
        screen.blit(cargo_surface, cargo_rect)
        screen.blit(credits_surface, credits_rect)

def draw_health_gauge(screen, ship, font):
    """draw the ship health bar beneath the lives counter."""

    health_ratio = ship.health / ship.max_health
    health_ratio = max(0, min(1, health_ratio))

    bar_rect = pygame.Rect(20, 85, 220, 22)

    fill_rect = pygame.Rect(
        bar_rect.x,
        bar_rect.y,
        round(bar_rect.width * health_ratio),
        bar_rect.height
    )

    if health_ratio > 0.5:
        health_color = (70, 210, 100)

    elif health_ratio > 0.25:
        health_color = (240, 190, 60)

    else:
        health_color = (230, 70, 70)

    label = font.render(
        f"Health: {ship.health}/{ship.max_health}",
        True,
        (255, 255, 255)
    )

    screen.blit(label, (20, 52))

    pygame.draw.rect(
        screen,
        (35, 35, 45),
        bar_rect
    )

    pygame.draw.rect(
        screen,
        health_color,
        fill_rect
    )

    pygame.draw.rect(
        screen,
        (255, 255, 255),
        bar_rect,
        2
    )

def draw_fuel_gauge(screen, ship, font):
    """draw the ship fuel level beneath the lives counter"""

    fuel_ratio = ship.fuel / ship.max_fuel
    fuel_ratio = max(0, min(1, fuel_ratio))

    bar_rect = pygame.Rect(20, 148, 220, 22)

    fill_rect = pygame.Rect(
        bar_rect.x,
        bar_rect.y,
        round(bar_rect.width * fuel_ratio),
        bar_rect.height
    )

    if fuel_ratio > 0.5:
        fuel_color = (70, 210, 100)

    elif fuel_ratio > 0.2:
        fuel_color = (240, 190, 60)

    else:
        fuel_color = (230, 70, 70)

    label = font.render(
        f"Fuel: {math.ceil(ship.fuel)}/{ship.max_fuel}",
        True,
        (255, 255, 255)
    )

    screen.blit(label, (20, 115))

    pygame.draw.rect(
        screen,
        (35, 35, 45),
        bar_rect
    )

    pygame.draw.rect(
        screen,
        fuel_color,
        fill_rect
    )

    pygame.draw.rect(
        screen,
        (255, 255, 255),
        bar_rect,
        2
    )

def main():
    """main game loop"""

    # set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Clean Space')

    # setting up clock
    clock = pygame.time.Clock()

    # font setup
    hud_font = pygame.font.Font(None, 36)
    game_over_font = pygame.font.Font(None, 80)
    restart_font = pygame.font.Font(None, 36)
    station_title_font = pygame.font.Font(None, 54)
    station_menu_font = pygame.font.Font(None, 30)
    station_small_font = pygame.font.Font(None, 26)

    # intializing station and station spawn location
    station = Station(STATION_X, STATION_Y)

    # initializing station menu
    station_menu = StationMenu()

    # initialzing recovery screen
    recovery = RecoverySequence()

    # initializing ship, setting spawn
    ship = Spaceship(SHIP_START_X, SHIP_START_Y)

    # initializing camera
    camera = Camera()
    camera.update(ship.pos)

    # initializing minimap
    minimap = Minimap()

    # setting up for asteroids
    asteroids = []
    asteroid_spawn_timer = 0

    # setting up collectibles
    collectibles = []
    garbage_spawn_timer = 0

    credits = 0

    # setting up camera-centered star field
    star_field = StarField(camera)

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

        # update recovery-screen timing
        recovery_finished = recovery.update(dt)

        if (
            recovery_finished
            and recovery.open_station_after
            and not game_over
            ):
            station_menu.open_menu(ship)

        # event handling for key presses
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if station_menu.is_open:
                        station_menu.close_menu()
                    else:
                        running = False

                elif event.key == K_e and not game_over and not recovery.active:
                        if station_menu.is_open:
                            station_menu.close_menu()

                        elif station.ship_in_docking_range(ship):
                            station_menu.open_menu(ship)
                            
                elif event.key == K_r and game_over and not recovery.active:
                    lives = 3
                    credits = 0
                    game_over = False

                    asteroids.clear()
                    collectibles.clear()

                    asteroid_spawn_timer = 0
                    garbage_spawn_timer = 0
                    invuln_timer = 0

                    ship.cargo.clear()
                    ship.reset_upgrades()

                    ship.reset()
                    camera.update(ship.pos)

                    station_menu.close_menu()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1 and station_menu.is_open and not recovery.active:
                    credits = station_menu.handle_click(
                        event.pos,
                        ship,
                        credits
                    )

        # event handling for held keys
        keys = pygame.key.get_pressed()

        # ===============================================================================
        # PYHSICS UPDATE
        # ===============================================================================
        if not game_over and not station_menu.is_open and not recovery.active:
            # updating ship physics
            ship.update(dt, keys)

            # rescue/ reset after running out of fuel
            if ship.fuel <= 0:
                # record losses before clearing cargo
                lost_cargo = ship.get_used_cargo_space()

                rescue_fee = math.ceil(credits * RESCUE_PENALTY_RATE)

                recovery.begin(
                    screen,
                    "EMERGENCY: OUT OF FUEL",
                    "RECOVERING BACK TO STATION",
                    lost_cargo,
                    rescue_fee,
                    True
                )

                ship.cargo.clear()
                credits -= rescue_fee

                ship.reset()

                # small allowance of fuel to prevent soft-lock
                ship.fuel = EMERGENCY_FUEL

                camera.update(ship.pos)
                invuln_timer = RESPAWN_PROTECTION_TIME

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

                # relect asteroids away from docking zone
                station.reflect_asteroid(asteroid)

            # removing asteroids off screen
            asteroids = [
                asteroid
                for asteroid in asteroids
                if not asteroid.is_offscreen(camera)
            ]

            # reduce respawn protection
            if (invuln_timer > 0 and not station.ship_in_docking_range(ship)):
                invuln_timer -= dt

            # check ship and asteroid collision
            if invuln_timer <= 0:
                for asteroid in asteroids:
                    collision_offset = ship.pos - asteroid.pos
                    collision_distance = ship.size / 2 + asteroid.radius

                    if collision_offset.length_squared() <= collision_distance ** 2:
                        # bounce both objects away from the collision
                        resolve_ship_asteroid_collision(ship, asteroid)

                        # damage the ship
                        ship.health -= ASTEROID_COLLISION_DAMAGE
                        ship.health = max(0, ship.health)

                        # prevent the same collision from causing damage every frame
                        invuln_timer = HIT_INVULN_TIME

                        # losing all health costs one life
                        if ship.health <= 0:
                            lives -= 1

                            # record losses before clearing cargo.
                            lost_cargo = ship.get_used_cargo_space()

                            rescue_fee = math.ceil(
                                credits * RESCUE_PENALTY_RATE
                            )

                            credits -= rescue_fee
                            ship.cargo.clear()

                            if lives <= 0:
                                recovery.begin(
                                    screen,
                                    "EMERGENCY: SHIP DESTROYED",
                                    "NO RECOVERY AVAILABLE",
                                    lost_cargo,
                                    rescue_fee,
                                    False
                                )

                                game_over = True
                                ship.vel = pygame.Vector2(0, 0)

                            else:
                                recovery.begin(
                                    screen,
                                    "EMERGENCY: SHIP DESTROYED",
                                    "RECOVERING BACK TO STATION...",
                                    lost_cargo,
                                    rescue_fee,
                                    True
                                )

                                ship.reset()
                                camera.update(ship.pos)
                                invuln_timer = RESPAWN_PROTECTION_TIME

                        break

            # spawn garbage
            if garbage_spawn_timer >= GARBAGE_SPAWN_TIME:
                collectibles.append(Garbage(camera))
                garbage_spawn_timer = 0

            # update garbage
            for collectible in collectibles:
                collectible.update(dt, camera)

            # remove off-screen garbage
            collectibles = [
                collectible
                for collectible in collectibles
                if not collectible.should_delete()
            ]

            for collectible in collectibles[:]:
                distance = ship.pos.distance_to(collectible.pos)

                collision_distance = (ship.size / 2 + collectible.radius)

                if distance <= collision_distance:
                    if ship.collect(collectible):
                        collectibles.remove(collectible)

            # update camera in case collision reset the ship 
            camera.update(ship.pos)

        # =======================================================================================
        # RENDERING
        # =======================================================================================

        # draw background
        screen.fill(BACKGROUND_COLOR)

        # draw stars
        star_field.draw(screen, camera)

        # draw station
        station.draw(screen, camera)

        # draw asteroids
        for asteroid in asteroids:
            asteroid.draw(screen, camera)

        # draw garbage
        for collectible in collectibles:
            collectible.draw(screen, camera)

        # drawing minimap
        minimap.draw(
            screen,
            ship,
            station,
            asteroids,
            collectibles
        )

        # draw lives counter
        lives_text = hud_font.render(
            f"Lives: {lives}",
            True,
            (255, 255, 255)
        )

        # draw health gauge
        draw_health_gauge(screen, ship, hud_font)
        
        # draw fuel gauge
        draw_fuel_gauge(screen, ship, hud_font)

        # draw credits
        credits_text = hud_font.render(
            f"Credits: {credits}",
            True,
            (255, 255, 255)
        )
        cargo_text = hud_font.render(
            (
                f"Cargo: {ship.get_used_cargo_space()}"
                f"/{ship.cargo_capacity}"
            ),
            True,
            (255, 255, 255)
        )

        credits_rect = credits_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        cargo_rect = cargo_text.get_rect(topright=(SCREEN_WIDTH - 20, 55))

        screen.blit(credits_text, credits_rect)
        screen.blit(cargo_text, cargo_rect)
        screen.blit(lives_text, (20, 20))

        # draw ship
        if not game_over:
            ship.draw(screen, camera)

            # display docking message
            if (not station_menu.is_open and station.ship_in_docking_range(ship)):
                docking_text = hud_font.render(
                    "Press E to dock",
                    True,
                    (100, 200, 255)
                )

                docking_rect = docking_text.get_rect(center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40))

                screen.blit(docking_text, docking_rect)

            station_menu.draw(
                screen,
                ship,
                credits,
                station_title_font,
                station_menu_font,
                station_small_font
            )

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

        # drawing recovery screen last to cover all other UI
        recovery.draw(
            screen,
            station_title_font,
            station_menu_font
        )

        # update display
        pygame.display.flip()

    # cleanup
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()