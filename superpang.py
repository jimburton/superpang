import pygame
import pygame.locals as pl
import sys
import random
import time

pygame.init()

FPS = 60
clock = pygame.time.Clock()

# Screen information
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
STAGE_HEIGHT = 560
SPEED = 5

# Predefine some colors
BLUE  = (0, 0, 255)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# --- Physics Constants ---
# Vertical acceleration due to gravity. The higher this value, the faster the arc.
GRAVITY = 0.5 
# Initial horizontal speed (constant).
INITIAL_SPEED_X = 5
# Initial vertical speed (upwards) when the balloon is created or bounces.
INITIAL_SPEED_Y = 20 
# Bounce Damping: 1.0 is a perfect bounce (no energy lost, constant height). 
# Use 0.95 to simulate slight energy loss (the balloon bounces slightly lower each time).
DAMPING_FACTOR = 1.0 

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("SuperPang!")

bullets = []
balloons = []

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__() 
        self.image = pygame.image.load("player.png")
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80)
 
    def move(self):
        pressed_keys = pygame.key.get_pressed()

        if self.rect.left > 0:
              if pressed_keys[pl.K_LEFT]:
                  self.rect.move_ip(-5, 0)
        if self.rect.right < SCREEN_WIDTH:        
              if pressed_keys[pl.K_RIGHT]:
                  self.rect.move_ip(5, 0)

class Balloon(pygame.sprite.Sprite):
      def __init__(self):
        super().__init__() 
        self.image = pygame.image.load("balloon.png")
        self.rect = self.image.get_rect()
        self.rect.center=(random.randint(40,SCREEN_WIDTH-40),0)
        # Velocities (float for smooth movement)
        self.vx = INITIAL_SPEED_X * random.choice([-1, 1]) # Random left or right
        self.vy = 0 # Starts with 0 vertical velocity        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
 
      def move(self):
          # Apply Gravity (Acceleration): This creates the arc motion.
          # Vertical velocity is constantly increasing (downwards)
          self.vy += GRAVITY
        
          # Update Position: Use float positions, then sync with rect
          self.x += self.vx
          self.y += self.vy
        
          # Handle Wall Collisions (Horizontal Bounce)
          if self.rect.left <= 0:
              self.vx *= -1 # Reverse horizontal direction
              self.x = 1 # Prevent sticking to the wall
          elif self.rect.right >= SCREEN_WIDTH:
              self.vx *= -1 # Reverse horizontal direction
              self.x = SCREEN_WIDTH - self.rect.width - 1 # Prevent sticking
          # 4. Handle Floor Collision (Vertical Bounce)
          if self.y >= STAGE_HEIGHT:
              self.vy = -INITIAL_SPEED_Y * DAMPING_FACTOR 
              self.y = STAGE_HEIGHT - self.rect.height # Prevent falling through the floor
            
        
          # 5. Sync Rect position with float position
          self.rect.x = int(self.x)
          self.rect.y = int(self.y)

class Arrow(pygame.sprite.Sprite):
      def __init__(self, x):
        super().__init__() 
        self.image = pygame.image.load("arrow.png")
        self.rect = self.image.get_rect()
        self.rect.center=(x, SCREEN_HEIGHT - 100) 
 
      def move(self):
        if self.rect.top > 0:
            self.rect.move_ip(0,-SPEED)
        else:
            self.kill()

# Setting up sprites
p = Player()
b1 = Balloon()

# Creating sprites collections
balloons = pygame.sprite.Group()
balloons.add(b1)
arrows = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
all_sprites.add(b1)
all_sprites.add(p)

FIRING = False
FIRE_RATE = 30 # frames between shots
frames_since_shot = 0

while True:
    frames_since_shot += 1 
    for event in pygame.event.get():              
        if event.type == pl.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pl.MOUSEBUTTONDOWN:
            FIRING = True
            # shoot straight away
            frames_since_shot = FIRE_RATE + 1
        elif event.type == pl.MOUSEBUTTONUP:
            FIRING = False
            frames_since_shot = 0
     
    DISPLAYSURF.fill(WHITE)
    #print(f"time since last arrow: {time_since_last_arrow}. FIRING: {FIRING}")
    if FIRING and frames_since_shot > FIRE_RATE:
        p_x = p.rect.centerx
        a = Arrow(p_x)
        arrows.add(a)
        all_sprites.add(a)
        frames_since_shot = 0

    # Move and redraw all sprites
    for entity in all_sprites:
        DISPLAYSURF.blit(entity.image, entity.rect)
        entity.move()

    # collision detection
    if pygame.sprite.spritecollideany(p, balloons):
        DISPLAYSURF.fill(RED)
        pygame.display.update()
        for entity in all_sprites:
            entity.kill()
        time.sleep(2)
        pygame.quit()
        sys.exit()
        
    pygame.display.update()
    clock.tick(FPS)
