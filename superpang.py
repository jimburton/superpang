import pygame
import pygame.locals as pl
import sys
import random
import time
from sprites import Player, Balloon, Arrow, INITIAL_SPEED_Y

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

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("SuperPang!")

bullets = []
balloons = []

# Setting up sprites
px, py = SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80
p = Player(initial_x=px, initial_y=py, min_x=0, max_x=SCREEN_WIDTH)

BALLOON_BOUNDS = {'min_x':0, 'max_x': SCREEN_WIDTH, 'min_y': 0, 'max_y': STAGE_HEIGHT}
def fresh_balloon():
    x_dir = random.choice([-1, 1]) # Random left or right
    initial_x = 0 if x_dir == 1 else SCREEN_WIDTH - 40
    initial_y, initial_vy = 0, 0
    
    return Balloon(size=3,
                   initial_x=initial_x,
                   initial_y=initial_y,
                   x_dir=x_dir,
                   vy=initial_vy,
                   bounds=BALLOON_BOUNDS)

b1 = fresh_balloon()
# Creating sprites collections
balloons = pygame.sprite.Group()
balloons.add(b1)
arrows = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
all_sprites.add(b1)
all_sprites.add(p)

ADD_BALLOON_EVENT = pygame.USEREVENT+1
BALLON_INTERVAL = 5000
pygame.time.set_timer(ADD_BALLOON_EVENT, BALLON_INTERVAL)

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
        elif event.type == ADD_BALLOON_EVENT:
            b = fresh_balloon()
            balloons.add(b)
            all_sprites.add(b)
            pass
     
    DISPLAYSURF.fill(WHITE)
    #print(f"time since last arrow: {time_since_last_arrow}. FIRING: {FIRING}")
    if FIRING and frames_since_shot > FIRE_RATE:
        a_x = p.rect.centerx
        a_y = SCREEN_HEIGHT - 100
        a = Arrow(initial_x=a_x, initial_y=a_y, speed=INITIAL_SPEED_Y)
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
    for b in balloons:
        hit_list = pygame.sprite.spritecollide(b, arrows, dokill=True)
        if len(hit_list) > 0:
            if b.size > 1:
                vy = -INITIAL_SPEED_Y / 2
                size = b.size-1
                initial_x,initial_y = b.rect.centerx, b.rect.centery
                c1 = Balloon(size=size,
                             initial_x=b.rect.left,
                             initial_y=initial_y,
                             x_dir=-1,
                             vy=vy,
                             bounds=BALLOON_BOUNDS)
                c2 = Balloon(size=size,
                             initial_x=b.rect.right,
                             initial_y=initial_y,
                             x_dir=1,
                             vy=vy,
                             bounds=BALLOON_BOUNDS)
                balloons.add(c1)
                balloons.add(c2)
                all_sprites.add(c1)
                all_sprites.add(c2)
            b.kill()
                
        
    pygame.display.update()
    clock.tick(FPS)
