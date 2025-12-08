import pygame
import pygame.locals as pl
import sys
import random
import time
from sprites import Player, Balloon, Arrow, INITIAL_SPEED_Y

pygame.init()

FPS = 30
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

def fresh_balloon(level_balloon=False):
    """ Make a new, full-size balloon. It appears in either the upper-right or
    upper-left corner.
    """
    x_dir = random.choice([-1, 1]) # Random left or right
    initial_x = 0 if x_dir == 1 else SCREEN_WIDTH - 40
    initial_y, initial_vy = 0, 0
    
    return Balloon(size=3,
                   initial_x=initial_x,
                   initial_y=initial_y,
                   x_dir=x_dir,
                   vy=initial_vy,
                   bounds=BALLOON_BOUNDS,
                   level_balloon=level_balloon)

b1 = fresh_balloon()
# Creating sprites collections
balloons = pygame.sprite.Group()
balloons.add(b1)
arrows = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
all_sprites.add(b1)
all_sprites.add(p)

ADD_BALLOON_EVENT = pygame.USEREVENT+1
EXPLODE_EVENT = pygame.USEREVENT+2
UNFREEZE_EVENT = pygame.USEREVENT+2
INITIAL_BALLOON_INTERVAL = 10000 # ten seconds from first balloon to second one, the interval decreases after that.
balloon_interval = INITIAL_BALLOON_INTERVAL
pygame.time.set_timer(ADD_BALLOON_EVENT, balloon_interval)

isFiring = False
FIRE_RATE = 30 # frames between shots
frames_since_shot = 0

my_font = pygame.font.SysFont('Comic Sans MS', 30)

level_text_pos = (10, STAGE_HEIGHT+10)
balloon_count_text_pos = (SCREEN_WIDTH-200, STAGE_HEIGHT+10)

frozen = False
FREEZE_TIME = 5000

def explode_balloons():
    """ Explode all ballons on a timer."""
    global frozen
    frozen = True
    pygame.time.set_timer(EXPLODE_EVENT, 300)

def freeze():
    """ Freeze balloons."""
    global frozen
    frozen = True
    pygame.time.set_timer(UNFREEZE_EVENT, FREEZE_TIME)

def play_game():
    global frames_since_shot, isFiring, balloon_count, balloon_interval, frozen
    
    # Initialize score variables
    balloon_count = 1
    level = 1
    
    while True:
        DISPLAYSURF.fill(WHITE)
        
        # Draw the ground line
        pygame.draw.line(DISPLAYSURF, BLACK, (0, STAGE_HEIGHT), (SCREEN_WIDTH, STAGE_HEIGHT), 2)
        
        frames_since_shot += 1
        end_of_level = False

        for event in pygame.event.get():          
            if event.type == pl.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pl.MOUSEBUTTONDOWN:
                isFiring = True
                # shoot straight away
                frames_since_shot = FIRE_RATE + 1
            elif event.type == pl.MOUSEBUTTONUP:
                isFiring = False
                frames_since_shot = 0
            elif event.type == ADD_BALLOON_EVENT:
                balloon_count += 1
                new_level_target = int((balloon_count - 1) / 10) + 1
                if new_level_target > level:
                    end_of_level = True
                    print(f"Level {new_level_target-1} completed!")
                b = fresh_balloon(level_balloon=end_of_level)
                balloons.add(b)
                all_sprites.add(b)
                if end_of_level:
                    balloon_interval = INITIAL_BALLOON_INTERVAL - (new_level_target * 100)
                    pygame.time.set_timer(ADD_BALLOON_EVENT, max(800, balloon_interval))
            elif event.type == EXPLODE_EVENT:
                new_balloons = []
                for b in balloons:
                    if b.size > 1:
                        vy = -INITIAL_SPEED_Y / 2
                        size = b.size - 1
                        initial_y = b.rect.centery
                        c1 = Balloon(size=size, initial_x=b.rect.left, initial_y=initial_y, x_dir=-1, vy=vy, bounds=BALLOON_BOUNDS)
                        c2 = Balloon(size=size, initial_x=b.rect.right, initial_y=initial_y, x_dir=1, vy=vy, bounds=BALLOON_BOUNDS)
                        new_balloons.append(c1)
                        new_balloons.append(c2)
                    b.kill()
                for b in new_balloons:
                    balloons.add(b)
                    all_sprites.add(b)
                frozen = False
                pygame.time.set_timer(EXPLODE_EVENT, 0)
                    

        if isFiring and frames_since_shot > FIRE_RATE:
            a_x = p.rect.centerx
            a_y = SCREEN_HEIGHT - 100
            a = Arrow(initial_x=a_x, initial_y=a_y, speed=INITIAL_SPEED_Y)
            arrows.add(a)
            all_sprites.add(a)
            frames_since_shot = 0

        # Update sprites (movement and physics)
        if not frozen:
            for entity in all_sprites:
                entity.move()

        # collision detection
        if pygame.sprite.spritecollideany(p, balloons):
            DISPLAYSURF.fill(RED)
            pygame.display.update()
            time.sleep(2)
            pygame.quit()
            sys.exit()
            
        for b in balloons:
            hit_list = pygame.sprite.spritecollide(b, arrows, dokill=True)
            if len(hit_list) > 0:
                # Explosion logic (splitting balloons)
                if b.level_balloon:
                    if b.star:
                        explode_balloons()
                    else:
                        freeze()
                elif b.size > 1:
                    vy = -INITIAL_SPEED_Y / 2
                    size = b.size - 1
                    initial_y = b.rect.centery
                    c1 = Balloon(size=size, initial_x=b.rect.left, initial_y=initial_y, x_dir=-1, vy=vy, bounds=BALLOON_BOUNDS)
                    c2 = Balloon(size=size, initial_x=b.rect.right, initial_y=initial_y, x_dir=1, vy=vy, bounds=BALLOON_BOUNDS)
                    balloons.add(c1, c2)
                    all_sprites.add(c1, c2)
                b.kill()
        
        # Draw all sprites and text
        
        all_sprites.draw(DISPLAYSURF) 

        new_level = int((balloon_count - 1) / 10) + 1
        if new_level > level:
            level = new_level
            
        balloon_count_text = my_font.render(f"Balloons: {balloon_count}", True, BLACK)
        level_text = my_font.render(f"Level: {level}", True, BLACK)
        
        DISPLAYSURF.blit(level_text, level_text_pos)
        DISPLAYSURF.blit(balloon_count_text, balloon_count_text_pos)
            
        # --- 4. Finalize Frame ---
        pygame.display.update()
        clock.tick(FPS)

if __name__ == '__main__':
    play_game()
