import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_RED = (139, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PURPLE = (180, 0, 255)
DARK_BLUE = (20, 20, 60)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Strike - FPS Game")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 72)
title_font = pygame.font.Font(None, 96)


# ─── Sound Generation (no external files needed) ────────────────────────────

def generate_sound(frequency=440, duration_ms=100, volume=0.3, wave_type="square"):
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    buf = bytearray(n_samples * 2)
    max_amp = int(32767 * volume)
    for i in range(n_samples):
        t = i / sample_rate
        if wave_type == "square":
            val = max_amp if math.sin(2 * math.pi * frequency * t) >= 0 else -max_amp
        elif wave_type == "sine":
            val = int(max_amp * math.sin(2 * math.pi * frequency * t))
        elif wave_type == "noise":
            val = random.randint(-max_amp, max_amp)
        else:
            val = int(max_amp * math.sin(2 * math.pi * frequency * t))
        fade = max(0, 1 - (i / n_samples) ** 0.5)
        val = int(val * fade)
        buf[i * 2] = val & 0xFF
        buf[i * 2 + 1] = (val >> 8) & 0xFF
    sound = pygame.mixer.Sound(buffer=bytes(buf))
    return sound


try:
    snd_shoot = generate_sound(600, 50, 0.15, "square")
    snd_hit = generate_sound(200, 80, 0.2, "noise")
    snd_enemy_die = generate_sound(300, 150, 0.2, "square")
    snd_player_hit = generate_sound(150, 200, 0.25, "noise")
    snd_reload = generate_sound(800, 200, 0.1, "sine")
    snd_powerup = generate_sound(1000, 300, 0.15, "sine")
    snd_wave = generate_sound(500, 400, 0.2, "sine")
    sound_enabled = True
except Exception:
    sound_enabled = False


def play_sound(sound):
    if sound_enabled:
        try:
            sound.play()
        except Exception:
            pass


# ─── Particle System ─────────────────────────────────────────────────────────

class Particle:
    def __init__(self, x, y, color, dx=None, dy=None, lifetime=30, size=3, gravity=0):
        self.x = x
        self.y = y
        self.color = color
        self.dx = dx if dx is not None else random.uniform(-3, 3)
        self.dy = dy if dy is not None else random.uniform(-3, 3)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += self.gravity
        self.lifetime -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        alpha = max(0, self.lifetime / self.max_lifetime)
        r = max(1, int(self.size * alpha))
        color = tuple(max(0, min(255, int(c * alpha))) for c in self.color)
        pygame.draw.circle(surface, color, (int(self.x + offset_x), int(self.y + offset_y)), r)

    def is_dead(self):
        return self.lifetime <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=10, spread=3, lifetime=30, size=3, gravity=0):
        for _ in range(count):
            dx = random.uniform(-spread, spread)
            dy = random.uniform(-spread, spread)
            self.particles.append(Particle(x, y, color, dx, dy, lifetime, size, gravity))

    def emit_muzzle_flash(self, x, y):
        colors = [YELLOW, ORANGE, WHITE, (255, 200, 50)]
        for _ in range(8):
            color = random.choice(colors)
            self.particles.append(Particle(x, y, color, random.uniform(-4, 4), random.uniform(-6, -1), 10, random.randint(2, 5)))

    def emit_blood(self, x, y):
        colors = [RED, DARK_RED, (200, 0, 0)]
        for _ in range(15):
            color = random.choice(colors)
            self.particles.append(Particle(x, y, color, random.uniform(-4, 4), random.uniform(-5, 2), random.randint(20, 40), random.randint(2, 4), gravity=0.15))

    def emit_explosion(self, x, y):
        colors = [RED, ORANGE, YELLOW, WHITE, (255, 100, 0)]
        for _ in range(30):
            color = random.choice(colors)
            speed = random.uniform(1, 6)
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle) * speed
            dy = math.sin(angle) * speed
            self.particles.append(Particle(x, y, color, dx, dy, random.randint(20, 50), random.randint(2, 6), gravity=0.05))

    def emit_spark(self, x, y):
        colors = [YELLOW, WHITE, CYAN]
        for _ in range(5):
            color = random.choice(colors)
            self.particles.append(Particle(x, y, color, random.uniform(-2, 2), random.uniform(-2, 2), 15, 2))

    def update(self):
        self.particles = [p for p in self.particles if not p.is_dead()]
        for p in self.particles:
            p.update()

    def draw(self, surface, offset_x=0, offset_y=0):
        for p in self.particles:
            p.draw(surface, offset_x, offset_y)


# ─── Screen Shake ─────────────────────────────────────────────────────────────

class ScreenShake:
    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.offset_x = 0
        self.offset_y = 0

    def shake(self, intensity=5, duration=10):
        self.intensity = intensity
        self.duration = duration

    def update(self):
        if self.duration > 0:
            self.offset_x = random.randint(-int(self.intensity), int(self.intensity))
            self.offset_y = random.randint(-int(self.intensity), int(self.intensity))
            self.duration -= 1
            self.intensity *= 0.9
        else:
            self.offset_x = 0
            self.offset_y = 0


# ─── PowerUp ──────────────────────────────────────────────────────────────────

class PowerUp:
    HEALTH = "health"
    AMMO = "ammo"
    SPEED = "speed"
    DAMAGE = "damage"

    def __init__(self, x, y, kind=None):
        self.x = x
        self.y = y
        self.kind = kind or random.choice([self.HEALTH, self.AMMO, self.SPEED, self.DAMAGE])
        self.width = 24
        self.height = 24
        self.lifetime = 600
        self.bob_offset = random.uniform(0, math.pi * 2)

        if self.kind == self.HEALTH:
            self.color = GREEN
        elif self.kind == self.AMMO:
            self.color = YELLOW
        elif self.kind == self.SPEED:
            self.color = CYAN
        elif self.kind == self.DAMAGE:
            self.color = PURPLE

    def update(self):
        self.lifetime -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        bob = math.sin(pygame.time.get_ticks() / 300 + self.bob_offset) * 4
        x = int(self.x + offset_x)
        y = int(self.y + bob + offset_y)

        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        alpha = int(80 + 40 * math.sin(pygame.time.get_ticks() / 200))
        pygame.draw.circle(glow_surf, (*self.color, alpha), (20, 20), 18)
        surface.blit(glow_surf, (x - 8, y - 8))

        pygame.draw.rect(surface, self.color, (x, y, self.width, self.height), border_radius=4)
        pygame.draw.rect(surface, WHITE, (x, y, self.width, self.height), 2, border_radius=4)

        icons = {self.HEALTH: "+", self.AMMO: "A", self.SPEED: "S", self.DAMAGE: "D"}
        icon_text = small_font.render(icons[self.kind], True, BLACK)
        surface.blit(icon_text, (x + self.width // 2 - icon_text.get_width() // 2,
                                  y + self.height // 2 - icon_text.get_height() // 2))

    def is_dead(self):
        return self.lifetime <= 0

    def collides_with(self, player):
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)


# ─── Drawing Helpers ──────────────────────────────────────────────────────────

def draw_polygon_offset(surface, color, points, offset_x=0, offset_y=0):
    shifted = [(p[0] + offset_x, p[1] + offset_y) for p in points]
    pygame.draw.polygon(surface, color, shifted)

def draw_polygon_offset_outline(surface, color, points, width=1, offset_x=0, offset_y=0):
    shifted = [(p[0] + offset_x, p[1] + offset_y) for p in points]
    pygame.draw.polygon(surface, color, shifted, width)

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def shade_color(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


# ─── Player ───────────────────────────────────────────────────────────────────

class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT - 100
        self.width = 40
        self.height = 60
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.ammo = 30
        self.max_ammo = 30
        self.reload_time = 0
        self.score = 0
        self.damage_multiplier = 1.0
        self.damage_timer = 0
        self.speed_multiplier = 1.0
        self.speed_timer = 0
        self.invincible_timer = 0
        self.combo = 0
        self.combo_timer = 0
        self.walk_cycle = 0.0
        self.facing = 1  # 1=right, -1=left

    def move(self, keys):
        spd = self.speed * self.speed_multiplier
        moved = False
        if keys[pygame.K_a] and self.x > 0:
            self.x -= spd
            self.facing = -1
            moved = True
        if keys[pygame.K_d] and self.x < WIDTH - self.width:
            self.x += spd
            self.facing = 1
            moved = True
        if keys[pygame.K_w] and self.y > HEIGHT // 2:
            self.y -= spd
            moved = True
        if keys[pygame.K_s] and self.y < HEIGHT - self.height:
            self.y += spd
            moved = True
        if moved:
            self.walk_cycle += 0.15
        else:
            self.walk_cycle *= 0.8

    def reload(self):
        if self.reload_time == 0 and self.ammo < self.max_ammo:
            self.reload_time = 60
            play_sound(snd_reload)

    def update(self):
        if self.reload_time > 0:
            self.reload_time -= 1
            if self.reload_time == 0:
                self.ammo = self.max_ammo
        if self.damage_timer > 0:
            self.damage_timer -= 1
        if self.speed_timer > 0:
            self.speed_timer -= 1
            if self.speed_timer == 0:
                self.speed_multiplier = 1.0
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0

    def apply_powerup(self, powerup):
        play_sound(snd_powerup)
        if powerup.kind == PowerUp.HEALTH:
            self.health = min(self.max_health, self.health + 30)
        elif powerup.kind == PowerUp.AMMO:
            self.ammo = self.max_ammo
        elif powerup.kind == PowerUp.SPEED:
            self.speed_multiplier = 1.8
            self.speed_timer = 300
        elif powerup.kind == PowerUp.DAMAGE:
            self.damage_multiplier = 2.0
            self.damage_timer = 300

    def draw(self, surface, offset_x=0, offset_y=0):
        x = int(self.x + offset_x)
        y = int(self.y + offset_y)

        if self.invincible_timer > 0 and (self.invincible_timer // 3) % 2 == 0:
            return

        # Speed trail
        if self.speed_multiplier > 1.0:
            trail_surf = pygame.Surface((self.width + 10, self.height + 20), pygame.SRCALPHA)
            trail_surf.fill((*CYAN, 30))
            surface.blit(trail_surf, (x - 5, y - 10))

        # Damage glow
        if self.damage_multiplier > 1.0:
            glow_surf = pygame.Surface((self.width + 16, self.height + 26), pygame.SRCALPHA)
            glow_surf.fill((*PURPLE, 35))
            surface.blit(glow_surf, (x - 8, y - 13))

        cx = x + self.width // 2  # center x
        mouse_pos = pygame.mouse.get_pos()
        aim_angle = math.atan2(mouse_pos[1] - (y + 15), mouse_pos[0] - cx)
        walk_bob = math.sin(self.walk_cycle) * 3
        leg_swing = math.sin(self.walk_cycle) * 6

        # ── Shadow ──
        shadow_surf = pygame.Surface((44, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, 44, 12))
        surface.blit(shadow_surf, (cx - 22, y + self.height - 2))

        # ── Legs ──
        boot_color = (50, 35, 25)
        pants_color = (45, 45, 80)
        pants_highlight = (60, 60, 100)

        # Left leg
        ll_x = cx - 8
        ll_y = y + 32 + walk_bob * 0.5
        draw_polygon_offset(surface, pants_color, [
            (ll_x - 5, ll_y), (ll_x + 5, ll_y), (ll_x + 6, ll_y + 22 + leg_swing * 0.5), (ll_x - 4, ll_y + 22 + leg_swing * 0.5)
        ], 0, 0)
        # Left boot
        draw_polygon_offset(surface, boot_color, [
            (ll_x - 6, ll_y + 20 + leg_swing * 0.5),
            (ll_x + 7, ll_y + 20 + leg_swing * 0.5),
            (ll_x + 8, ll_y + 28 + leg_swing * 0.3),
            (ll_x - 7, ll_y + 28 + leg_swing * 0.3)
        ], 0, 0)

        # Right leg
        rl_x = cx + 8
        rl_y = y + 32 + walk_bob * 0.5
        draw_polygon_offset(surface, pants_color, [
            (rl_x - 5, rl_y), (rl_x + 5, rl_y), (rl_x + 6, rl_y + 22 - leg_swing * 0.5), (rl_x - 4, rl_y + 22 - leg_swing * 0.5)
        ], 0, 0)
        # Right boot
        draw_polygon_offset(surface, boot_color, [
            (rl_x - 6, rl_y + 20 - leg_swing * 0.5),
            (rl_x + 7, rl_y + 20 - leg_swing * 0.5),
            (rl_x + 8, rl_y + 28 - leg_swing * 0.3),
            (rl_x - 7, rl_y + 28 - leg_swing * 0.3)
        ], 0, 0)

        # ── Torso / Body ──
        torso_top = y + 10 + walk_bob
        torso_bottom = y + 34 + walk_bob
        vest_color = (30, 80, 50)   # military green vest
        vest_dark = (20, 60, 35)
        vest_light = (40, 100, 60)
        shirt_color = (50, 50, 70)

        # Main torso shape
        draw_polygon_offset(surface, shirt_color, [
            (cx - 14, torso_top + 2),
            (cx + 14, torso_top + 2),
            (cx + 12, torso_bottom),
            (cx - 12, torso_bottom)
        ])

        # Tactical vest
        draw_polygon_offset(surface, vest_color, [
            (cx - 12, torso_top + 4),
            (cx + 12, torso_top + 4),
            (cx + 11, torso_bottom - 2),
            (cx - 11, torso_bottom - 2)
        ])
        # Vest collar
        draw_polygon_offset(surface, vest_dark, [
            (cx - 8, torso_top + 2),
            (cx + 8, torso_top + 2),
            (cx + 6, torso_top + 8),
            (cx - 6, torso_top + 8)
        ])
        # Vest center line
        pygame.draw.line(surface, vest_dark, (cx, torso_top + 8), (cx, torso_bottom - 4), 1)
        # Vest pockets
        pygame.draw.rect(surface, vest_dark, (cx - 9, torso_top + 10, 7, 5), border_radius=1)
        pygame.draw.rect(surface, vest_dark, (cx + 2, torso_top + 10, 7, 5), border_radius=1)
        pygame.draw.rect(surface, vest_dark, (cx - 9, torso_top + 18, 7, 4), border_radius=1)
        pygame.draw.rect(surface, vest_dark, (cx + 2, torso_top + 18, 7, 4), border_radius=1)
        # Vest buckle
        pygame.draw.rect(surface, (180, 160, 60), (cx - 2, torso_top + 15, 4, 3))

        # Belt
        belt_y = torso_bottom - 3
        pygame.draw.rect(surface, (70, 50, 30), (cx - 13, belt_y, 26, 4))
        pygame.draw.rect(surface, (180, 160, 60), (cx - 2, belt_y, 4, 4))

        # ── Arms ──
        skin_color = (220, 180, 140)
        skin_shadow = (190, 150, 110)
        arm_color = shirt_color

        # Back arm (slightly behind body)
        back_arm_x = cx - 14
        arm_angle_back = aim_angle + 0.15
        shoulder_by = torso_top + 6
        elbow_bx = back_arm_x - 4 + math.cos(arm_angle_back) * 8
        elbow_by = shoulder_by + math.sin(arm_angle_back) * 8 + 6
        hand_bx = back_arm_x - 2 + math.cos(arm_angle_back) * 6
        hand_by = shoulder_by + math.sin(arm_angle_back) * 6 + 14
        pygame.draw.line(surface, arm_color, (back_arm_x, shoulder_by), (int(elbow_bx), int(elbow_by)), 5)
        pygame.draw.line(surface, skin_color, (int(elbow_bx), int(elbow_by)), (int(hand_bx), int(hand_by)), 4)

        # Front arm + weapon
        front_arm_x = cx + 14
        shoulder_fy = torso_top + 6
        gun_len = 22
        gun_end_x = cx + math.cos(aim_angle) * gun_len
        gun_end_y = shoulder_fy + math.sin(aim_angle) * gun_len
        elbow_fx = front_arm_x + 2 + math.cos(aim_angle) * 8
        elbow_fy = shoulder_fy + math.sin(aim_angle) * 8 + 4
        hand_fx = cx + math.cos(aim_angle) * 10
        hand_fy = shoulder_fy + math.sin(aim_angle) * 10 + 2

        # Arm
        pygame.draw.line(surface, arm_color, (front_arm_x, shoulder_fy), (int(elbow_fx), int(elbow_fy)), 5)
        pygame.draw.line(surface, skin_color, (int(elbow_fx), int(elbow_fy)), (int(hand_fx), int(hand_fy)), 4)

        # Weapon (assault rifle)
        perp_x = -math.sin(aim_angle)
        perp_y = math.cos(aim_angle)
        barrel_w = 3
        # Gun body
        gun_body_pts = [
            (hand_fx + perp_x * barrel_w, hand_fy + perp_y * barrel_w),
            (hand_fx - perp_x * barrel_w, hand_fy - perp_y * barrel_w),
            (gun_end_x - perp_x * 2, gun_end_y - perp_y * 2),
            (gun_end_x + perp_x * 2, gun_end_y + perp_y * 2),
        ]
        draw_polygon_offset(surface, (60, 60, 60), gun_body_pts)
        # Gun barrel
        barrel_end_x = cx + math.cos(aim_angle) * (gun_len + 8)
        barrel_end_y = shoulder_fy + math.sin(aim_angle) * (gun_len + 8)
        pygame.draw.line(surface, (80, 80, 80), (int(gun_end_x), int(gun_end_y)),
                         (int(barrel_end_x), int(barrel_end_y)), 3)
        # Muzzle
        pygame.draw.circle(surface, (40, 40, 40), (int(barrel_end_x), int(barrel_end_y)), 3)
        # Stock
        stock_x = hand_fx - math.cos(aim_angle) * 6
        stock_y = hand_fy - math.sin(aim_angle) * 6
        pygame.draw.line(surface, (80, 60, 40), (int(hand_fx), int(hand_fy)), (int(stock_x), int(stock_y)), 5)

        # Magazine
        mag_x = hand_fx + math.cos(aim_angle) * 4
        mag_y = hand_fy + math.sin(aim_angle) * 4
        mag_pts = [
            (mag_x + perp_x * 4, mag_y + perp_y * 4),
            (mag_x - perp_x * 1, mag_y - perp_y * 1),
            (mag_x - perp_x * 1 + math.cos(aim_angle + 1.2) * 8, mag_y - perp_y * 1 + math.sin(aim_angle + 1.2) * 8),
            (mag_x + perp_x * 4 + math.cos(aim_angle + 1.2) * 8, mag_y + perp_y * 4 + math.sin(aim_angle + 1.2) * 8),
        ]
        draw_polygon_offset(surface, (50, 50, 50), mag_pts)

        # ── Neck ──
        neck_y = torso_top - 2
        pygame.draw.rect(surface, skin_shadow, (cx - 4, neck_y, 8, 6))

        # ── Head ──
        head_cx = cx
        head_cy = y - 2 + walk_bob
        head_r = 13

        # Helmet
        helmet_color = (50, 60, 45)
        helmet_dark = (35, 45, 30)
        helmet_light = (65, 80, 55)
        # Helmet dome
        draw_polygon_offset(surface, helmet_color, [
            (head_cx - 14, head_cy - 2),
            (head_cx - 12, head_cy - 16),
            (head_cx - 4, head_cy - 20),
            (head_cx + 4, head_cy - 20),
            (head_cx + 12, head_cy - 16),
            (head_cx + 14, head_cy - 2),
        ])
        # Helmet brim
        draw_polygon_offset(surface, helmet_dark, [
            (head_cx - 16, head_cy - 3),
            (head_cx + 16, head_cy - 3),
            (head_cx + 14, head_cy + 1),
            (head_cx - 14, head_cy + 1),
        ])
        # Helmet highlight
        draw_polygon_offset(surface, helmet_light, [
            (head_cx - 6, head_cy - 18),
            (head_cx + 2, head_cy - 19),
            (head_cx + 6, head_cy - 15),
            (head_cx - 2, head_cy - 14),
        ])

        # Face
        pygame.draw.rect(surface, skin_color, (head_cx - 10, head_cy - 2, 20, 14), border_radius=3)

        # Eyes (look toward mouse)
        look_dx = mouse_pos[0] - head_cx
        look_dy = mouse_pos[1] - head_cy
        look_dist = max(1, math.sqrt(look_dx**2 + look_dy**2))
        eye_shift_x = (look_dx / look_dist) * 2
        eye_shift_y = (look_dy / look_dist) * 1

        # Eye whites
        pygame.draw.ellipse(surface, WHITE, (head_cx - 8, head_cy + 1, 7, 5))
        pygame.draw.ellipse(surface, WHITE, (head_cx + 1, head_cy + 1, 7, 5))
        # Pupils
        pygame.draw.circle(surface, (30, 80, 30), (int(head_cx - 4 + eye_shift_x), int(head_cy + 3 + eye_shift_y)), 2)
        pygame.draw.circle(surface, (30, 80, 30), (int(head_cx + 5 + eye_shift_x), int(head_cy + 3 + eye_shift_y)), 2)

        # Mouth
        pygame.draw.line(surface, (160, 120, 100), (head_cx - 3, head_cy + 8), (head_cx + 3, head_cy + 8), 1)

        # ── Shoulder pads ──
        pad_color = (40, 70, 50)
        pygame.draw.ellipse(surface, pad_color, (cx - 19, torso_top + 1, 10, 8))
        pygame.draw.ellipse(surface, pad_color, (cx + 9, torso_top + 1, 10, 8))

        # ── Health bar above player ──
        bar_w = 50
        bar_h = 5
        bar_x = cx - bar_w // 2
        bar_y = y - 30 + walk_bob
        pygame.draw.rect(surface, (60, 60, 60), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_w, bar_h))
        hw = int(bar_w * (self.health / self.max_health))
        color = GREEN if self.health > 50 else YELLOW if self.health > 25 else RED
        pygame.draw.rect(surface, color, (bar_x, bar_y, hw, bar_h))


# ─── Bullet ───────────────────────────────────────────────────────────────────

class Bullet:
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        self.speed = 12
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance != 0:
            self.dx = (dx / distance) * self.speed
            self.dy = (dy / distance) * self.speed
        else:
            self.dx = 0
            self.dy = -self.speed
        self.radius = 4
        self.trail = []

    def update(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface, offset_x=0, offset_y=0):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / len(self.trail) * 0.5
            r = max(1, int(self.radius * alpha))
            color = (255, 255, int(100 * alpha))
            pygame.draw.circle(surface, color, (int(tx + offset_x), int(ty + offset_y)), r)
        pygame.draw.circle(surface, YELLOW, (int(self.x + offset_x), int(self.y + offset_y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x + offset_x), int(self.y + offset_y)), max(1, self.radius - 2))

    def is_off_screen(self):
        return self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10


# ─── Enemy Types ──────────────────────────────────────────────────────────────

class Enemy:
    NORMAL = "normal"
    FAST = "fast"
    TANK = "tank"
    SNIPER = "sniper"

    def __init__(self, kind=None, wave=1):
        self.kind = kind or random.choice([self.NORMAL, self.NORMAL, self.FAST, self.TANK, self.SNIPER])
        self.x = random.randint(50, WIDTH - 90)
        self.y = random.randint(50, 250)
        self.width = 40
        self.height = 50
        self.direction = random.choice([-1, 1])
        self.shoot_cooldown = 0
        self.flash_timer = 0
        self.walk_cycle = random.uniform(0, math.pi * 2)
        self.breathe = 0

        if self.kind == self.NORMAL:
            self.speed = random.uniform(0.5, 1.5) + wave * 0.05
            self.health = 50 + wave * 5
            self.max_health = self.health
            self.shoot_rate = 0.01
            self.color = RED
            self.body_color = (200, 30, 30)
        elif self.kind == self.FAST:
            self.speed = random.uniform(2.0, 3.5) + wave * 0.08
            self.health = 30 + wave * 3
            self.max_health = self.health
            self.shoot_rate = 0.015
            self.color = ORANGE
            self.body_color = (255, 140, 0)
            self.width = 30
            self.height = 40
        elif self.kind == self.TANK:
            self.speed = random.uniform(0.3, 0.8)
            self.health = 150 + wave * 15
            self.max_health = self.health
            self.shoot_rate = 0.008
            self.color = (100, 100, 100)
            self.body_color = DARK_GRAY
            self.width = 55
            self.height = 65
        elif self.kind == self.SNIPER:
            self.speed = random.uniform(0.5, 1.0)
            self.health = 40 + wave * 4
            self.max_health = self.health
            self.shoot_rate = 0.005
            self.color = PURPLE
            self.body_color = (140, 0, 200)
            self.width = 35
            self.height = 50

    def update(self, player):
        self.x += self.speed * self.direction
        self.walk_cycle += self.speed * 0.12
        self.breathe += 0.05

        if self.x <= 0 or self.x >= WIDTH - self.width:
            self.direction *= -1

        if random.random() < 0.008:
            if self.x < player.x:
                self.direction = 1
            else:
                self.direction = -1

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface, offset_x=0, offset_y=0):
        x = int(self.x + offset_x)
        y = int(self.y + offset_y)
        is_flash = self.flash_timer > 0

        cx = x + self.width // 2
        walk_bob = math.sin(self.walk_cycle) * 2
        leg_swing = math.sin(self.walk_cycle) * 5
        breath_offset = math.sin(self.breathe) * 1

        if self.kind == self.NORMAL:
            self._draw_normal(surface, x, y, cx, walk_bob, leg_swing, breath_offset, is_flash)
        elif self.kind == self.FAST:
            self._draw_fast(surface, x, y, cx, walk_bob, leg_swing, breath_offset, is_flash)
        elif self.kind == self.TANK:
            self._draw_tank(surface, x, y, cx, walk_bob, leg_swing, breath_offset, is_flash)
        elif self.kind == self.SNIPER:
            self._draw_sniper(surface, x, y, cx, walk_bob, leg_swing, breath_offset, is_flash)

        # ── Health bar (shared) ──
        bar_w = self.width + 4
        bar_h = 4
        bar_x = cx - bar_w // 2
        bar_y = y - 28 + walk_bob
        pygame.draw.rect(surface, (40, 40, 40), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2))
        hw = int(bar_w * (self.health / self.max_health))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, hw, bar_h))

    def _draw_normal(self, surface, x, y, cx, walk_bob, leg_swing, breath, flash):
        """Red soldier with beret"""
        skin = (255, 200, 160) if not flash else WHITE
        uniform = (180, 30, 30) if not flash else WHITE
        uniform_dk = (130, 20, 20) if not flash else (230, 230, 230)
        uniform_lt = (210, 50, 50) if not flash else (245, 245, 245)
        boot_c = (50, 30, 20) if not flash else (220, 220, 220)

        # Shadow
        shadow_s = pygame.Surface((36, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 40), (0, 0, 36, 10))
        surface.blit(shadow_s, (cx - 18, y + self.height - 2))

        # Legs
        for side, sign in [(-1, 1), (1, -1)]:
            lx = cx + side * 6
            ly = y + 28 + walk_bob * 0.5
            pts = [
                (lx - 4, ly), (lx + 4, ly),
                (lx + 5, ly + 18 + sign * leg_swing * 0.4),
                (lx - 3, ly + 18 + sign * leg_swing * 0.4)
            ]
            draw_polygon_offset(surface, uniform_dk, pts)
            # Boot
            draw_polygon_offset(surface, boot_c, [
                (lx - 5, ly + 16 + sign * leg_swing * 0.3),
                (lx + 6, ly + 16 + sign * leg_swing * 0.3),
                (lx + 7, ly + 24 + sign * leg_swing * 0.2),
                (lx - 6, ly + 24 + sign * leg_swing * 0.2)
            ])

        # Body
        bt = y + 8 + walk_bob + breath
        bb = y + 30 + walk_bob
        draw_polygon_offset(surface, uniform, [
            (cx - 12, bt + 2), (cx + 12, bt + 2),
            (cx + 11, bb), (cx - 11, bb)
        ])
        # Belt
        pygame.draw.rect(surface, (60, 40, 25), (cx - 12, bb - 4, 24, 3))
        pygame.draw.rect(surface, (160, 140, 50), (cx - 2, bb - 4, 4, 3))
        # Collar
        draw_polygon_offset(surface, uniform_dk, [
            (cx - 6, bt + 2), (cx + 6, bt + 2),
            (cx + 4, bt + 7), (cx - 4, bt + 7)
        ])
        # Pockets
        pygame.draw.rect(surface, uniform_dk, (cx - 8, bt + 10, 6, 4), border_radius=1)
        pygame.draw.rect(surface, uniform_dk, (cx + 2, bt + 10, 6, 4), border_radius=1)

        # Arms
        for side in [-1, 1]:
            ax = cx + side * 14
            ay = bt + 5
            pygame.draw.line(surface, uniform, (ax, ay), (ax + side * 3, ay + 12), 5)
            pygame.draw.line(surface, skin, (ax + side * 3, ay + 12), (ax + side * 2, ay + 18), 4)

        # Neck
        pygame.draw.rect(surface, skin, (cx - 3, bt - 1, 6, 5))

        # Head
        hcy = y - 4 + walk_bob
        pygame.draw.circle(surface, skin, (cx, int(hcy)), 11)

        # Beret
        draw_polygon_offset(surface, (200, 20, 20), [
            (cx - 13, hcy - 3), (cx + 13, hcy - 3),
            (cx + 10, hcy - 10), (cx, hcy - 14), (cx - 10, hcy - 10)
        ])
        draw_polygon_offset(surface, (220, 40, 40), [
            (cx - 10, hcy - 10), (cx, hcy - 14), (cx + 10, hcy - 10), (cx, hcy - 7)
        ])
        # Beret stem
        pygame.draw.circle(surface, (200, 20, 20), (cx + 2, int(hcy) - 13), 3)

        # Eyes
        eye_y = int(hcy) + 1
        pygame.draw.ellipse(surface, WHITE, (cx - 7, eye_y - 2, 6, 4))
        pygame.draw.ellipse(surface, WHITE, (cx + 1, eye_y - 2, 6, 4))
        look = self.direction
        pygame.draw.circle(surface, BLACK, (cx - 4 + look, eye_y), 2)
        pygame.draw.circle(surface, BLACK, (cx + 4 + look, eye_y), 2)

        # Eyebrows (angry)
        pygame.draw.line(surface, (80, 40, 20), (cx - 8, eye_y - 4), (cx - 2, eye_y - 3), 2)
        pygame.draw.line(surface, (80, 40, 20), (cx + 2, eye_y - 3), (cx + 8, eye_y - 4), 2)

        # Mouth (frown)
        pygame.draw.arc(surface, (120, 60, 40), (cx - 4, int(hcy) + 4, 8, 5), 3.14, 6.28, 1)

    def _draw_fast(self, surface, x, y, cx, walk_bob, leg_swing, breath, flash):
        """Lean orange scout with goggles"""
        skin = (240, 190, 150) if not flash else WHITE
        suit = (220, 120, 0) if not flash else WHITE
        suit_dk = (180, 90, 0) if not flash else (230, 230, 230)
        suit_lt = (255, 160, 30) if not flash else (245, 245, 245)
        boot_c = (60, 40, 30) if not flash else (220, 220, 220)

        # Shadow
        shadow_s = pygame.Surface((30, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 35), (0, 0, 30, 8))
        surface.blit(shadow_s, (cx - 15, y + self.height - 2))

        # Legs (thin)
        for side, sign in [(-1, 1), (1, -1)]:
            lx = cx + side * 5
            ly = y + 22 + walk_bob * 0.5
            pts = [
                (lx - 3, ly), (lx + 3, ly),
                (lx + 4, ly + 14 + sign * leg_swing * 0.6),
                (lx - 2, ly + 14 + sign * leg_swing * 0.6)
            ]
            draw_polygon_offset(surface, suit_dk, pts)
            draw_polygon_offset(surface, boot_c, [
                (lx - 4, ly + 12 + sign * leg_swing * 0.4),
                (lx + 5, ly + 12 + sign * leg_swing * 0.4),
                (lx + 6, ly + 20 + sign * leg_swing * 0.3),
                (lx - 5, ly + 20 + sign * leg_swing * 0.3)
            ])

        # Body (lean)
        bt = y + 5 + walk_bob + breath
        bb = y + 24 + walk_bob
        draw_polygon_offset(surface, suit, [
            (cx - 10, bt + 2), (cx + 10, bt + 2),
            (cx + 9, bb), (cx - 9, bb)
        ])
        # Stripe
        pygame.draw.line(surface, suit_lt, (cx, bt + 4), (cx, bb - 2), 2)
        # Belt
        pygame.draw.rect(surface, (80, 50, 20), (cx - 10, bb - 3, 20, 3))

        # Arms
        for side in [-1, 1]:
            ax = cx + side * 12
            ay = bt + 4
            pygame.draw.line(surface, suit, (ax, ay), (ax + side * 4, ay + 10), 4)
            pygame.draw.line(surface, skin, (ax + side * 4, ay + 10), (ax + side * 3, ay + 16), 3)

        # Neck
        pygame.draw.rect(surface, skin, (cx - 3, bt - 1, 6, 4))

        # Head
        hcy = y - 6 + walk_bob
        pygame.draw.circle(surface, skin, (cx, int(hcy)), 10)

        # Hair (spiky)
        for i in range(-3, 4):
            spike_h = random.Random(i * 42).randint(4, 8)
            draw_polygon_offset(surface, (60, 30, 0), [
                (cx + i * 3 - 2, hcy - 9),
                (cx + i * 3 + 2, hcy - 9),
                (cx + i * 3, hcy - 9 - spike_h)
            ])

        # Goggles strap
        pygame.draw.line(surface, (60, 60, 60), (cx - 12, int(hcy) - 2), (cx + 12, int(hcy) - 2), 2)
        # Goggles
        pygame.draw.ellipse(surface, (40, 40, 40), (cx - 9, int(hcy) - 5, 8, 6))
        pygame.draw.ellipse(surface, (40, 40, 40), (cx + 1, int(hcy) - 5, 8, 6))
        pygame.draw.ellipse(surface, (100, 200, 255), (cx - 8, int(hcy) - 4, 6, 4))
        pygame.draw.ellipse(surface, (100, 200, 255), (cx + 2, int(hcy) - 4, 6, 4))
        # Goggle reflection
        pygame.draw.line(surface, (200, 230, 255), (cx - 6, int(hcy) - 4), (cx - 5, int(hcy) - 3), 1)
        pygame.draw.line(surface, (200, 230, 255), (cx + 4, int(hcy) - 4), (cx + 5, int(hcy) - 3), 1)

        # Mouth (grin)
        pygame.draw.arc(surface, (120, 60, 30), (cx - 3, int(hcy) + 3, 6, 4), 3.14, 6.28, 1)

        # Speed lines
        if self.speed > 2:
            for i in range(3):
                lx = cx - self.direction * (18 + i * 6)
                ly = y + 10 + i * 8 + walk_bob
                alpha_s = pygame.Surface((12, 2), pygame.SRCALPHA)
                alpha_s.fill((255, 200, 100, 80 - i * 20))
                surface.blit(alpha_s, (lx, ly))

    def _draw_tank(self, surface, x, y, cx, walk_bob, leg_swing, breath, flash):
        """Big armored brute"""
        skin = (180, 150, 120) if not flash else WHITE
        armor = (90, 90, 100) if not flash else WHITE
        armor_dk = (60, 60, 70) if not flash else (230, 230, 230)
        armor_lt = (120, 120, 135) if not flash else (245, 245, 245)
        boot_c = (40, 35, 30) if not flash else (220, 220, 220)

        # Shadow
        shadow_s = pygame.Surface((50, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 50), (0, 0, 50, 12))
        surface.blit(shadow_s, (cx - 25, y + self.height - 2))

        # Legs (thick)
        for side, sign in [(-1, 1), (1, -1)]:
            lx = cx + side * 10
            ly = y + 40 + walk_bob * 0.3
            pts = [
                (lx - 8, ly), (lx + 8, ly),
                (lx + 9, ly + 22 + sign * leg_swing * 0.3),
                (lx - 7, ly + 22 + sign * leg_swing * 0.3)
            ]
            draw_polygon_offset(surface, armor_dk, pts)
            # Armored boots
            draw_polygon_offset(surface, boot_c, [
                (lx - 9, ly + 18 + sign * leg_swing * 0.2),
                (lx + 10, ly + 18 + sign * leg_swing * 0.2),
                (lx + 11, ly + 28 + sign * leg_swing * 0.1),
                (lx - 10, ly + 28 + sign * leg_swing * 0.1)
            ])
            # Knee pad
            pygame.draw.circle(surface, armor, (lx + 1, ly + 4), 5)
            pygame.draw.circle(surface, armor_lt, (lx, ly + 3), 3)

        # Body (wide)
        bt = y + 12 + walk_bob + breath
        bb = y + 42 + walk_bob
        draw_polygon_offset(surface, armor_dk, [
            (cx - 22, bt), (cx + 22, bt),
            (cx + 20, bb), (cx - 20, bb)
        ])
        # Chest plate
        draw_polygon_offset(surface, armor, [
            (cx - 18, bt + 2), (cx + 18, bt + 2),
            (cx + 16, bt + 22), (cx - 16, bt + 22)
        ])
        # Plate details
        pygame.draw.line(surface, armor_lt, (cx, bt + 2), (cx, bt + 22), 1)
        pygame.draw.rect(surface, armor_dk, (cx - 14, bt + 5, 12, 6), border_radius=1)
        pygame.draw.rect(surface, armor_dk, (cx + 2, bt + 5, 12, 6), border_radius=1)
        # Rivets
        for rx in [cx - 16, cx - 8, cx + 8, cx + 16]:
            pygame.draw.circle(surface, armor_lt, (rx, bt + 16), 2)
        # Belt
        pygame.draw.rect(surface, (70, 50, 30), (cx - 22, bb - 5, 44, 5))
        pygame.draw.rect(surface, (160, 140, 50), (cx - 3, bb - 5, 6, 5))

        # Arms (thick, armored)
        for side in [-1, 1]:
            ax = cx + side * 24
            ay = bt + 5
            # Shoulder pauldron
            pygame.draw.ellipse(surface, armor, (ax - 8, ay - 4, 16, 12))
            pygame.draw.ellipse(surface, armor_lt, (ax - 5, ay - 2, 10, 6))
            # Upper arm
            pygame.draw.line(surface, armor_dk, (ax, ay + 4), (ax + side * 2, ay + 16), 8)
            # Forearm
            pygame.draw.line(surface, armor, (ax + side * 2, ay + 16), (ax + side, ay + 26), 7)
            # Fist
            pygame.draw.circle(surface, skin, (ax + side, ay + 27), 5)

        # Neck
        pygame.draw.rect(surface, skin, (cx - 5, bt - 3, 10, 7))

        # Head
        hcy = y + 2 + walk_bob
        pygame.draw.circle(surface, skin, (cx, int(hcy)), 14)

        # Heavy helmet
        draw_polygon_offset(surface, armor_dk, [
            (cx - 16, hcy - 2), (cx + 16, hcy - 2),
            (cx + 14, hcy - 14), (cx, hcy - 20), (cx - 14, hcy - 14)
        ])
        draw_polygon_offset(surface, armor, [
            (cx - 14, hcy - 4), (cx + 14, hcy - 4),
            (cx + 12, hcy - 13), (cx, hcy - 18), (cx - 12, hcy - 13)
        ])
        # Helmet highlight
        draw_polygon_offset(surface, armor_lt, [
            (cx - 8, hcy - 15), (cx + 2, hcy - 17),
            (cx + 8, hcy - 12), (cx - 2, hcy - 10)
        ])
        # Face guard
        pygame.draw.rect(surface, armor_dk, (cx - 15, hcy - 3, 30, 4))
        # Visor slit
        pygame.draw.rect(surface, (20, 20, 20), (cx - 10, hcy - 3, 20, 3))

        # Red glowing eyes through visor
        pygame.draw.circle(surface, (255, 50, 30), (cx - 5, int(hcy) - 2), 2)
        pygame.draw.circle(surface, (255, 100, 60), (cx - 5, int(hcy) - 2), 1)
        pygame.draw.circle(surface, (255, 50, 30), (cx + 5, int(hcy) - 2), 2)
        pygame.draw.circle(surface, (255, 100, 60), (cx + 5, int(hcy) - 2), 1)

        # Jaw
        pygame.draw.rect(surface, skin, (cx - 10, int(hcy) + 2, 20, 8), border_radius=2)
        pygame.draw.line(surface, (140, 100, 70), (cx - 3, int(hcy) + 7), (cx + 3, int(hcy) + 7), 1)

    def _draw_sniper(self, surface, x, y, cx, walk_bob, leg_swing, breath, flash):
        """Purple stealth figure with hood and scope"""
        skin = (200, 170, 150) if not flash else WHITE
        cloak = (80, 0, 120) if not flash else WHITE
        cloak_dk = (50, 0, 80) if not flash else (230, 230, 230)
        cloak_lt = (110, 20, 160) if not flash else (245, 245, 245)
        boot_c = (30, 20, 35) if not flash else (220, 220, 220)

        # Shadow
        shadow_s = pygame.Surface((34, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_s, (0, 0, 0, 35), (0, 0, 34, 8))
        surface.blit(shadow_s, (cx - 17, y + self.height - 2))

        # Legs
        for side, sign in [(-1, 1), (1, -1)]:
            lx = cx + side * 5
            ly = y + 28 + walk_bob * 0.5
            pts = [
                (lx - 3, ly), (lx + 3, ly),
                (lx + 4, ly + 16 + sign * leg_swing * 0.5),
                (lx - 2, ly + 16 + sign * leg_swing * 0.5)
            ]
            draw_polygon_offset(surface, cloak_dk, pts)
            draw_polygon_offset(surface, boot_c, [
                (lx - 4, ly + 14 + sign * leg_swing * 0.3),
                (lx + 5, ly + 14 + sign * leg_swing * 0.3),
                (lx + 6, ly + 22 + sign * leg_swing * 0.2),
                (lx - 5, ly + 22 + sign * leg_swing * 0.2)
            ])

        # Body
        bt = y + 6 + walk_bob + breath
        bb = y + 30 + walk_bob
        draw_polygon_offset(surface, cloak_dk, [
            (cx - 12, bt), (cx + 12, bt),
            (cx + 10, bb), (cx - 10, bb)
        ])
        draw_polygon_offset(surface, cloak, [
            (cx - 10, bt + 2), (cx + 10, bt + 2),
            (cx + 9, bb - 2), (cx - 9, bb - 2)
        ])
        # Belt with pouches
        pygame.draw.rect(surface, (40, 25, 50), (cx - 11, bb - 4, 22, 4))
        pygame.draw.rect(surface, (60, 40, 70), (cx - 8, bb - 4, 5, 4), border_radius=1)
        pygame.draw.rect(surface, (60, 40, 70), (cx + 3, bb - 4, 5, 4), border_radius=1)

        # Arms
        for side in [-1, 1]:
            ax = cx + side * 14
            ay = bt + 4
            pygame.draw.line(surface, cloak, (ax, ay), (ax + side * 3, ay + 12), 5)
            pygame.draw.line(surface, skin, (ax + side * 3, ay + 12), (ax + side * 2, ay + 18), 4)

        # Weapon (long rifle)
        player_ref = None  # We'll just aim downward-ish
        gun_angle = math.pi / 2 + self.direction * 0.3
        gun_len = 28
        gun_start_x = cx + self.direction * 8
        gun_start_y = bt + 10
        gun_end_x = gun_start_x + math.cos(gun_angle) * gun_len
        gun_end_y = gun_start_y + math.sin(gun_angle) * gun_len
        # Barrel
        pygame.draw.line(surface, (50, 50, 55), (int(gun_start_x), int(gun_start_y)),
                         (int(gun_end_x), int(gun_end_y)), 3)
        # Scope on top
        scope_x = gun_start_x + math.cos(gun_angle) * 15
        scope_y = gun_start_y + math.sin(gun_angle) * 15
        perp_x = -math.sin(gun_angle)
        perp_y = math.cos(gun_angle)
        pygame.draw.circle(surface, (40, 40, 45), (int(scope_x + perp_x * 4), int(scope_y + perp_y * 4)), 4)
        pygame.draw.circle(surface, (60, 60, 70), (int(scope_x + perp_x * 4), int(scope_y + perp_y * 4)), 3)
        pygame.draw.circle(surface, (100, 200, 255), (int(scope_x + perp_x * 4), int(scope_y + perp_y * 4)), 2)

        # Neck
        pygame.draw.rect(surface, skin, (cx - 3, bt - 1, 6, 4))

        # Head
        hcy = y - 4 + walk_bob
        pygame.draw.circle(surface, skin, (cx, int(hcy)), 10)

        # Hood
        draw_polygon_offset(surface, cloak_dk, [
            (cx - 14, hcy + 2), (cx + 14, hcy + 2),
            (cx + 12, hcy - 8), (cx, hcy - 18), (cx - 12, hcy - 8)
        ])
        draw_polygon_offset(surface, cloak, [
            (cx - 12, hcy), (cx + 12, hcy),
            (cx + 10, hcy - 7), (cx, hcy - 15), (cx - 10, hcy - 7)
        ])
        # Hood shadow
        draw_polygon_offset(surface, cloak_dk, [
            (cx - 10, hcy - 2), (cx + 10, hcy - 2),
            (cx + 8, hcy - 6), (cx, hcy - 13), (cx - 8, hcy - 6)
        ])

        # Eyes (narrow, calculating)
        eye_y = int(hcy)
        # Narrow eyes
        pygame.draw.line(surface, WHITE, (cx - 7, eye_y), (cx - 2, eye_y), 2)
        pygame.draw.line(surface, WHITE, (cx + 2, eye_y), (cx + 7, eye_y), 2)
        pygame.draw.circle(surface, (180, 0, 255), (cx - 4 + self.direction, eye_y), 1)
        pygame.draw.circle(surface, (180, 0, 255), (cx + 5 + self.direction, eye_y), 1)

        # Type label
        label = small_font.render("S", True, cloak_lt)
        surface.blit(label, (cx - label.get_width() // 2, y - 30 + walk_bob - 8))

    def shoot(self, player):
        if self.shoot_cooldown == 0 and random.random() < self.shoot_rate:
            self.shoot_cooldown = random.randint(40, 100)
            bullet_speed = 4
            if self.kind == self.SNIPER:
                bullet_speed = 7
            elif self.kind == self.TANK:
                bullet_speed = 3
            return EnemyBullet(
                self.x + self.width // 2, self.y + self.height,
                player.x + player.width // 2, player.y + player.height // 2,
                bullet_speed
            )
        return None


class EnemyBullet:
    def __init__(self, x, y, target_x, target_y, speed=5):
        self.x = x
        self.y = y
        self.speed = speed
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance != 0:
            self.dx = (dx / distance) * self.speed
            self.dy = (dy / distance) * self.speed
        else:
            self.dx = 0
            self.dy = self.speed
        self.radius = 4

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, surface, offset_x=0, offset_y=0):
        px = int(self.x + offset_x)
        py = int(self.y + offset_y)
        pygame.draw.circle(surface, RED, (px, py), self.radius + 1)
        pygame.draw.circle(surface, ORANGE, (px, py), max(1, self.radius - 1))

    def is_off_screen(self):
        return self.x < -10 or self.x > WIDTH + 10 or self.y < -10 or self.y > HEIGHT + 10


# ─── Background Star/Debris ──────────────────────────────────────────────────

class BackgroundElement:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(1, 3)
        self.brightness = random.randint(80, 180)
        self.speed = random.uniform(0.1, 0.5)

    def update(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

    def draw(self, surface):
        color = (self.brightness, self.brightness, self.brightness + 40)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


# ─── Collision Helpers ────────────────────────────────────────────────────────

def check_collision(bullet, enemy):
    distance = math.sqrt((bullet.x - (enemy.x + enemy.width // 2)) ** 2 +
                          (bullet.y - (enemy.y + enemy.height // 2)) ** 2)
    return distance < bullet.radius + max(enemy.width, enemy.height) // 2


def check_player_collision(bullet, player):
    distance = math.sqrt((bullet.x - (player.x + player.width // 2)) ** 2 +
                          (bullet.y - (player.y + player.height // 2)) ** 2)
    return distance < bullet.radius + 20


# ─── Drawing Functions ────────────────────────────────────────────────────────

def draw_crosshair(surface, pos):
    x, y = pos
    size = 18
    gap = 5
    thickness = 2
    pygame.draw.line(surface, GREEN, (x - size, y), (x - gap, y), thickness)
    pygame.draw.line(surface, GREEN, (x + gap, y), (x + size, y), thickness)
    pygame.draw.line(surface, GREEN, (x, y - size), (x, y - gap), thickness)
    pygame.draw.line(surface, GREEN, (x, y + gap), (x, y + size), thickness)
    pygame.draw.circle(surface, GREEN, (x, y), 12, 1)
    pygame.draw.circle(surface, GREEN, (x, y), 2)


def draw_background(surface, bg_elements):
    for y in range(0, HEIGHT, 4):
        ratio = y / HEIGHT
        r = int(20 + 30 * ratio)
        g = int(20 + 25 * ratio)
        b = int(60 + 40 * ratio)
        pygame.draw.rect(surface, (r, g, b), (0, y, WIDTH, 4))

    for elem in bg_elements:
        elem.draw(surface)

    pygame.draw.line(surface, (100, 100, 120), (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 2)

    for i in range(0, WIDTH, 80):
        pygame.draw.line(surface, (40, 40, 70), (i, 0), (i, HEIGHT // 2), 1)


def draw_ui(surface, player, wave, wave_timer, kill_count):
    hud_rect = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
    hud_rect.fill((0, 0, 0, 180))
    surface.blit(hud_rect, (0, HEIGHT - 80))

    health_label = small_font.render("HP", True, WHITE)
    surface.blit(health_label, (10, HEIGHT - 75))

    bar_w = 150
    bar_h = 16
    bar_x = 35
    bar_y = HEIGHT - 75
    pygame.draw.rect(surface, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
    hw = int(bar_w * (player.health / player.max_health))
    color = GREEN if player.health > 50 else YELLOW if player.health > 25 else RED
    pygame.draw.rect(surface, color, (bar_x, bar_y, hw, bar_h), border_radius=3)
    hp_text = small_font.render(f"{player.health}/{player.max_health}", True, WHITE)
    surface.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y))

    ammo_color = RED if player.ammo == 0 else WHITE
    ammo_text = font.render(f"Ammo: {player.ammo}/{player.max_ammo}", True, ammo_color)
    surface.blit(ammo_text, (10, HEIGHT - 45))

    if player.reload_time > 0:
        progress = 1 - (player.reload_time / 60)
        reload_w = 120
        reload_h = 8
        rx = 200
        ry = HEIGHT - 38
        pygame.draw.rect(surface, GRAY, (rx, ry, reload_w, reload_h), border_radius=2)
        pygame.draw.rect(surface, YELLOW, (rx, ry, int(reload_w * progress), reload_h), border_radius=2)
        reload_text = small_font.render("RELOADING", True, YELLOW)
        surface.blit(reload_text, (rx, ry - 18))

    score_text = font.render(f"Score: {player.score}", True, WHITE)
    surface.blit(score_text, (WIDTH - 200, HEIGHT - 75))

    wave_text = small_font.render(f"Wave: {wave}", True, CYAN)
    surface.blit(wave_text, (WIDTH - 200, HEIGHT - 45))

    kill_text = small_font.render(f"Kills: {kill_count}", True, ORANGE)
    surface.blit(kill_text, (WIDTH - 120, HEIGHT - 45))

    if player.combo > 1:
        combo_text = font.render(f"x{player.combo} COMBO!", True, YELLOW)
        surface.blit(combo_text, (WIDTH // 2 - combo_text.get_width() // 2, 40))

    pu_y = HEIGHT - 45
    pu_x = WIDTH // 2 - 60
    if player.speed_timer > 0:
        t = small_font.render(f"SPD {player.speed_timer // 60 + 1}s", True, CYAN)
        surface.blit(t, (pu_x, pu_y))
        pu_x += 70
    if player.damage_timer > 0:
        t = small_font.render(f"DMG {player.damage_timer // 60 + 1}s", True, PURPLE)
        surface.blit(t, (pu_x, pu_y))

    if wave_timer > 0:
        alpha = min(255, wave_timer * 8)
        wave_announce = large_font.render(f"WAVE {wave}", True, CYAN)
        surface.blit(wave_announce, (WIDTH // 2 - wave_announce.get_width() // 2, HEIGHT // 2 - 100))

    if player.score == 0 and wave == 1:
        inst = small_font.render("WASD: Move | Mouse: Aim | Click: Shoot | R: Reload", True, (200, 200, 200))
        surface.blit(inst, (WIDTH // 2 - inst.get_width() // 2, 10))


def draw_menu(surface):
    surface.fill(DARK_BLUE)

    # Decorative soldier silhouette on menu
    t = pygame.time.get_ticks()
    # Draw a large player silhouette
    scx, scy = WIDTH // 2, 480
    # Helmet
    draw_polygon_offset(surface, (30, 40, 50), [
        (scx - 20, scy - 30), (scx + 20, scy - 30),
        (scx + 18, scy - 50), (scx, scy - 60), (scx - 18, scy - 50)
    ])
    # Face
    pygame.draw.rect(surface, (60, 70, 80), (scx - 15, scy - 30, 30, 20), border_radius=3)
    # Body
    draw_polygon_offset(surface, (30, 50, 40), [
        (scx - 18, scy - 12), (scx + 18, scy - 12),
        (scx + 16, scy + 20), (scx - 16, scy + 20)
    ])
    # Legs
    draw_polygon_offset(surface, (25, 25, 40), [
        (scx - 12, scy + 20), (scx - 2, scy + 20),
        (scx - 2, scy + 45), (scx - 14, scy + 45)
    ])
    draw_polygon_offset(surface, (25, 25, 40), [
        (scx + 2, scy + 20), (scx + 12, scy + 20),
        (scx + 14, scy + 45), (scx + 2, scy + 45)
    ])
    # Gun
    aim = math.sin(t / 1000) * 0.3
    gx = scx + 18
    gy = scy - 5
    gex = gx + math.cos(aim) * 30
    gey = gy + math.sin(aim) * 30
    pygame.draw.line(surface, (80, 80, 80), (gx, gy), (int(gex), int(gey)), 4)

    title = title_font.render("PYTHON", True, CYAN)
    title2 = title_font.render("STRIKE", True, YELLOW)
    surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))
    surface.blit(title2, (WIDTH // 2 - title2.get_width() // 2, 210))

    sub = font.render("A Top-Down FPS Experience", True, LIGHT_GRAY)
    surface.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 300))

    lines = [
        "WASD - Move",
        "Mouse - Aim",
        "Left Click - Shoot",
        "R - Reload",
        "",
        "Press ENTER to Start",
        "Press ESC to Quit",
    ]
    for i, line in enumerate(lines):
        color = YELLOW if "ENTER" in line else WHITE
        text = small_font.render(line, True, color)
        surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 350 + i * 28))

    ver = small_font.render("v3.0 - Enhanced Character Edition", True, GRAY)
    surface.blit(ver, (WIDTH // 2 - ver.get_width() // 2, HEIGHT - 30))


def game_over_screen(surface, score, wave, kill_count):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))

    go_text = large_font.render("GAME OVER", True, RED)
    surface.blit(go_text, (WIDTH // 2 - go_text.get_width() // 2, HEIGHT // 2 - 100))

    score_text = font.render(f"Final Score: {score}", True, WHITE)
    surface.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 20))

    wave_text = font.render(f"Wave Reached: {wave}", True, CYAN)
    surface.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, HEIGHT // 2 + 20))

    kill_text = font.render(f"Total Kills: {kill_count}", True, ORANGE)
    surface.blit(kill_text, (WIDTH // 2 - kill_text.get_width() // 2, HEIGHT // 2 + 60))

    restart_text = small_font.render("Press SPACE to Restart | ESC to Quit", True, WHITE)
    surface.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 120))


# ─── Main Game Loop ──────────────────────────────────────────────────────────

def main():
    state = "menu"

    player = Player()
    bullets = []
    enemies = []
    enemy_bullets = []
    powerups = []
    particles = ParticleSystem()
    shake = ScreenShake()
    bg_elements = [BackgroundElement() for _ in range(60)]

    spawn_timer = 0
    wave = 1
    wave_timer = 120
    enemies_spawned_this_wave = 0
    enemies_to_spawn_this_wave = 3
    kill_count = 0
    total_kills = 0

    pygame.mouse.set_visible(False)

    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == "menu":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        state = "playing"
                        player = Player()
                        bullets = []
                        enemies = []
                        enemy_bullets = []
                        powerups = []
                        particles = ParticleSystem()
                        shake = ScreenShake()
                        wave = 1
                        wave_timer = 120
                        enemies_spawned_this_wave = 0
                        enemies_to_spawn_this_wave = 3
                        kill_count = 0
                        total_kills = 0
                        spawn_timer = 0
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            elif state == "game_over":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        state = "playing"
                        player = Player()
                        bullets = []
                        enemies = []
                        enemy_bullets = []
                        powerups = []
                        particles = ParticleSystem()
                        shake = ScreenShake()
                        wave = 1
                        wave_timer = 120
                        enemies_spawned_this_wave = 0
                        enemies_to_spawn_this_wave = 3
                        kill_count = 0
                        total_kills = 0
                        spawn_timer = 0
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            elif state == "playing":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if player.ammo > 0 and player.reload_time == 0:
                        bx = player.x + player.width // 2
                        by = player.y
                        bullets.append(Bullet(bx, by, mouse_pos[0], mouse_pos[1]))
                        player.ammo -= 1
                        play_sound(snd_shoot)
                        particles.emit_muzzle_flash(bx, by)
                        shake.shake(2, 3)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        player.reload()

        # ── Update ──────────────────────────────────────────────────────────

        if state == "menu":
            for elem in bg_elements:
                elem.update()

        elif state == "playing":
            keys = pygame.key.get_pressed()
            player.move(keys)
            player.update()

            for elem in bg_elements:
                elem.update()

            if wave_timer > 0:
                wave_timer -= 1

            spawn_timer += 1
            spawn_interval = max(30, 120 - wave * 5)
            if spawn_timer >= spawn_interval and enemies_spawned_this_wave < enemies_to_spawn_this_wave:
                kinds = [Enemy.NORMAL]
                if wave >= 2:
                    kinds.append(Enemy.FAST)
                if wave >= 3:
                    kinds.append(Enemy.TANK)
                if wave >= 4:
                    kinds.append(Enemy.SNIPER)
                kind = random.choice(kinds)
                enemies.append(Enemy(kind, wave))
                enemies_spawned_this_wave += 1
                spawn_timer = 0

            if enemies_spawned_this_wave >= enemies_to_spawn_this_wave and len(enemies) == 0:
                wave += 1
                wave_timer = 120
                enemies_to_spawn_this_wave = 3 + wave * 2
                enemies_spawned_this_wave = 0
                kill_count = 0
                play_sound(snd_wave)

            for bullet in bullets[:]:
                bullet.update()
                if bullet.is_off_screen():
                    bullets.remove(bullet)

            for enemy in enemies:
                enemy.update(player)
                new_bullet = enemy.shoot(player)
                if new_bullet:
                    enemy_bullets.append(new_bullet)

            for bullet in enemy_bullets[:]:
                bullet.update()
                if bullet.is_off_screen():
                    enemy_bullets.remove(bullet)
                elif check_player_collision(bullet, player):
                    if player.invincible_timer == 0:
                        player.health -= 10
                        play_sound(snd_player_hit)
                        particles.emit_blood(player.x + player.width // 2, player.y + player.height // 2)
                        shake.shake(6, 12)
                        player.invincible_timer = 15
                    enemy_bullets.remove(bullet)
                    if player.health <= 0:
                        particles.emit_explosion(player.x + player.width // 2, player.y + player.height // 2)
                        state = "game_over"

            for bullet in bullets[:]:
                for enemy in enemies[:]:
                    if check_collision(bullet, enemy):
                        dmg = int(25 * player.damage_multiplier)
                        enemy.health -= dmg
                        enemy.flash_timer = 4
                        play_sound(snd_hit)
                        particles.emit_spark(bullet.x, bullet.y)

                        if bullet in bullets:
                            bullets.remove(bullet)

                        if enemy.health <= 0:
                            particles.emit_explosion(
                                enemy.x + enemy.width // 2,
                                enemy.y + enemy.height // 2
                            )
                            play_sound(snd_enemy_die)
                            shake.shake(4, 8)

                            player.combo += 1
                            player.combo_timer = 120

                            base_score = 100
                            if enemy.kind == Enemy.FAST:
                                base_score = 150
                            elif enemy.kind == Enemy.TANK:
                                base_score = 200
                            elif enemy.kind == Enemy.SNIPER:
                                base_score = 175
                            player.score += base_score * player.combo
                            total_kills += 1
                            kill_count += 1

                            drop_chance = 0.15 if enemy.kind == Enemy.TANK else 0.08
                            if random.random() < drop_chance:
                                powerups.append(PowerUp(
                                    enemy.x + enemy.width // 2 - 12,
                                    enemy.y + enemy.height // 2 - 12
                                ))

                            if enemy in enemies:
                                enemies.remove(enemy)
                        break

            for pu in powerups[:]:
                pu.update()
                if pu.is_dead():
                    powerups.remove(pu)
                elif pu.collides_with(player):
                    player.apply_powerup(pu)
                    powerups.remove(pu)

            particles.update()
            shake.update()

        # ── Draw ────────────────────────────────────────────────────────────

        if state == "menu":
            draw_menu(screen)
            draw_crosshair(screen, mouse_pos)

        elif state == "playing":
            draw_background(screen, bg_elements)

            ox = shake.offset_x
            oy = shake.offset_y

            for pu in powerups:
                pu.draw(screen, ox, oy)

            for enemy in enemies:
                enemy.draw(screen, ox, oy)

            for bullet in bullets:
                bullet.draw(screen, ox, oy)

            for bullet in enemy_bullets:
                bullet.draw(screen, ox, oy)

            player.draw(screen, ox, oy)
            particles.draw(screen, ox, oy)
            draw_ui(screen, player, wave, wave_timer, total_kills)
            draw_crosshair(screen, mouse_pos)

        elif state == "game_over":
            draw_background(screen, bg_elements)
            ox = shake.offset_x
            oy = shake.offset_y

            for enemy in enemies:
                enemy.draw(screen, ox, oy)
            for bullet in enemy_bullets:
                bullet.draw(screen, ox, oy)

            particles.draw(screen, ox, oy)
            game_over_screen(screen, player.score, wave, total_kills)
            draw_crosshair(screen, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
