import pygame
import pygame.locals as pl
import sys
import random
import time
import os
from sprites import Player, Balloon, Arrow, INITIAL_SPEED_Y, AUDIO_PATH

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
GOLD = (255, 215, 0)

BALLOON_BOUNDS = {'min_x':0, 'max_x': SCREEN_WIDTH, 'min_y': 0, 'max_y': STAGE_HEIGHT}

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
DISPLAYSURF.fill(WHITE)
pygame.display.set_caption("SuperPang!")

# Events
ADD_BALLOON_EVENT = pygame.USEREVENT+1
EXPLODE_EVENT = pygame.USEREVENT+2
UNFREEZE_EVENT = pygame.USEREVENT+3
FLASH_EVENT = pygame.USEREVENT+4
FRESH_BALLOON_WAIT_EVENT = pygame.USEREVENT+5
INITIAL_BALLOON_INTERVAL = 10000 
FLASH_INTERVAL = 500
FIRE_RATE = 30 # frames between shots

LABEL_FONT = pygame.font.SysFont('Comic Sans MS', 30)
LEVEL_TEXT_POS = (10, STAGE_HEIGHT+10)
BIG_FONT = pygame.font.SysFont('Comic Sans MS', 1000)
BALLOON_COUNT_TEXT_POS = (SCREEN_WIDTH-200, STAGE_HEIGHT+10)

FREEZE_TIME_STAR = 4000
FREEZE_TIME_BALLOON = 2000
EXPLODE_INTERVAL = 1000
FRESH_BALLOON_INTERVAL = 2000

pygame.mixer.music.load(os.path.join(AUDIO_PATH, "theme.ogg"))
AUDIO_POP = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "pop.ogg"))
TOTAL_BALLOONS = 100

class SuperPang:

    def __init__(self):
        px, py = SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80
        self.player = Player(initial_x=px, initial_y=py, min_x=0, max_x=SCREEN_WIDTH)
        self.make_freezer = True
        b1 = self.fresh_balloon(level_balloon=False)
        # Creating sprites collections
        self.balloons = pygame.sprite.Group()
        self.balloons.add(b1)
        self.arrows = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(b1)
        self.all_sprites.add(self.player)
        self.is_firing = False
        self.frozen = False
        # ten seconds from first balloon to second one, the interval decreases after that.
        self.balloon_interval = INITIAL_BALLOON_INTERVAL
        pygame.time.set_timer(ADD_BALLOON_EVENT, self.balloon_interval)
        pygame.time.set_timer(FLASH_EVENT, FLASH_INTERVAL)

    def fresh_balloon(self, level_balloon=False):
        """ Make a new, full-size balloon. It appears in either the upper-right or
        upper-left corner.
        """
        self.make_freezer = not self.make_freezer
        x_dir = random.choice([-1, 1]) # Random left or right
        initial_x = 0 if x_dir == 1 else SCREEN_WIDTH - 40
        initial_y, initial_vy = 0, 0
        pygame.time.set_timer(FRESH_BALLOON_WAIT_EVENT, FRESH_BALLOON_INTERVAL)
        return Balloon(size=4,
                       initial_x=initial_x,
                       initial_y=initial_y,
                       x_dir=x_dir,
                       vy=initial_vy,
                       bounds=BALLOON_BOUNDS,
                       level_balloon=level_balloon,
                       freezer=self.make_freezer)

    def explode_balloons(self):
        """ Explode all ballons on a timer."""
        self.frozen = True
        pygame.time.set_timer(EXPLODE_EVENT, EXPLODE_INTERVAL)

    def freeze(self, time):
        """ Freeze balloons."""
        self.frozen = True
        pygame.time.set_timer(UNFREEZE_EVENT, time)

    def play(self):
        pygame.mixer.music.play(-1)
        # Initialize score variables
        balloon_count = 1
        level = 1
        playing = True
        frames_since_shot = 0
        paused = False
        firing = False
    
        while playing:
            DISPLAYSURF.fill(WHITE)
        
            # Draw the ground line
            pygame.draw.line(DISPLAYSURF, BLACK, (0, STAGE_HEIGHT), (SCREEN_WIDTH, STAGE_HEIGHT), 2)
        
            frames_since_shot += 1
            end_of_level = False

            events = pygame.event.get()
            for event in events:
                if event.type == pl.KEYDOWN and event.key == pl.K_SPACE:
                    paused = not paused
            if not paused:
                for event in events:          
                    if event.type == pl.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pl.MOUSEBUTTONDOWN:
                        firing = True
                        self.player.firing(is_firing=firing)
                        # shoot straight away
                        frames_since_shot = FIRE_RATE + 1
                    elif event.type == pl.MOUSEBUTTONUP:
                        firing = False
                        self.player.firing(is_firing=firing)
                        frames_since_shot = 0
                    elif event.type == ADD_BALLOON_EVENT:
                        balloon_count += 1
                        new_level_target = int((balloon_count - 1) / 10) + 1
                        if new_level_target > level:
                            end_of_level = True
                            print(f"Level {new_level_target-1} completed!")
                        b = self.fresh_balloon(level_balloon=end_of_level)
                        self.balloons.add(b)
                        self.all_sprites.add(b)
                        if balloon_count == TOTAL_BALLOONS:
                            pygame.time.set_timer(ADD_BALLOON_EVENT, 0)
                        elif end_of_level:
                            self.balloon_interval = INITIAL_BALLOON_INTERVAL - (new_level_target * 100)
                            pygame.time.set_timer(ADD_BALLOON_EVENT, max(800, self.balloon_interval))
                    elif event.type == EXPLODE_EVENT:
                        if len(self.balloons) > 0:
                            new_balloons = []
                            for b in self.balloons:
                                if b.size > 1:
                                    vy = -INITIAL_SPEED_Y / 2
                                    size = b.size - 1
                                    initial_y = b.rect.centery
                                    offset = (b.rect.centerx - b.rect.left) / 2 
                                    c1 = Balloon(size=size,
                                                 initial_x=b.rect.centerx - offset,
                                                 initial_y=initial_y,
                                                 x_dir=-1,
                                                 vy=vy,
                                                 bounds=BALLOON_BOUNDS)
                                    c2 = Balloon(size=size,
                                                 initial_x=b.rect.centerx + offset,
                                                 initial_y=initial_y,
                                                 x_dir=1,
                                                 vy=vy,
                                                 bounds=BALLOON_BOUNDS)
                                    new_balloons.append(c1)
                                    new_balloons.append(c2)
                                b.kill()
                            pygame.mixer.Sound.play(AUDIO_POP)
                            for b in new_balloons:
                                self.balloons.add(b)
                                self.all_sprites.add(b)
                        else:
                            self.frozen = False
                            pygame.time.set_timer(EXPLODE_EVENT, 0)
                    elif event.type == FLASH_EVENT:
                        for b in self.balloons:
                            if b.size == 1 and b.freezer:
                                b.flash()
                    elif event.type == UNFREEZE_EVENT:
                        self.frozen = False
                    elif event.type == FRESH_BALLOON_WAIT_EVENT:
                        for b in self.balloons:
                            b.waiting = False

                if firing and frames_since_shot > FIRE_RATE:
                    a_x = self.player.rect.centerx
                    a_y = SCREEN_HEIGHT - 100
                    a = Arrow(initial_x=a_x, initial_y=a_y, speed=INITIAL_SPEED_Y)
                    self.arrows.add(a)
                    self.all_sprites.add(a)
                    frames_since_shot = 0

                # Update sprites (movement and physics)
                if not self.frozen:
                    for entity in self.all_sprites:
                        # entity is not a waiting balloon
                        if not hasattr(entity, 'waiting') or not entity.waiting:
                            entity.move()
                else:
                    self.player.move()
                    for arrow in self.arrows:
                        arrow.move()

                # collision detection
                if pygame.sprite.spritecollideany(self.player, self.balloons):
                    DISPLAYSURF.fill(RED)
                    game_over = LABEL_FONT.render("GAME OVER", True, BLACK)
                    DISPLAYSURF.blit(game_over, (200, SCREEN_HEIGHT / 2))
                    pygame.display.update()
                    playing = False
            
                for b in self.balloons:
                    hit_list = pygame.sprite.spritecollide(b, self.arrows, dokill=True)
                    if len(hit_list) > 0:
                        # Explosion logic (splitting balloons)
                        if b.level_balloon:
                            if b.star:
                                self.explode_balloons()
                            else:
                                self.freeze(FREEZE_TIME_STAR)
                        elif b.size > 1 and not b.waiting:
                            # replace the balloon with two smaller ones
                            vy = 0 if b.rect.top < 20 else -INITIAL_SPEED_Y / 2
                            size = b.size - 1
                            initial_y = b.rect.centery
                            offset = (b.rect.centerx - b.rect.left) / 2 
                            c1 = Balloon(size=size,
                                         initial_x=b.rect.centerx - offset,
                                         initial_y=initial_y,
                                         x_dir=-1,
                                         vy=vy,
                                         bounds=BALLOON_BOUNDS,
                                         freezer=b.freezer)
                            c2 = Balloon(size=size,
                                         initial_x=b.rect.centerx + offset,
                                         initial_y=initial_y,
                                         x_dir=1,
                                         vy=vy,
                                         bounds=BALLOON_BOUNDS,
                                         freezer=False)
                            self.balloons.add(c1, c2)
                            self.all_sprites.add(c1, c2)
                        elif b.size == 1 and b.freezer:
                            # it is a size 1 freezer
                            self.freeze(FREEZE_TIME_BALLOON)
                        pygame.mixer.Sound.play(AUDIO_POP)
                        b.kill()
                # player won the game
                if len(self.balloons) == 0 and balloon_count == TOTAL_BALLOONS:
                    DISPLAYSURF.fill(GOLD)
                    win = LABEL_FONT.render("YOU WIN!", True, BLACK)
                    DISPLAYSURF.blit(win, (200, SCREEN_HEIGHT / 2))
                    pygame.display.update()
                    playing = False
                    
                # Draw labels
                new_level = int((balloon_count - 1) / 10) + 1
                if new_level > level:
                    level = new_level
                balloon_count_text = LABEL_FONT.render(f"Balloons: {balloon_count}", True, BLACK)
                level_text = LABEL_FONT.render(f"Level: {level}", True, BLACK)
                DISPLAYSURF.blit(level_text, LEVEL_TEXT_POS)
                DISPLAYSURF.blit(balloon_count_text, BALLOON_COUNT_TEXT_POS)

            # draw all sprites
            self.all_sprites.draw(DISPLAYSURF) 
            # Finalize Frame ---
            pygame.display.update()
            clock.tick(FPS)
        time.sleep(3)
        pygame.quit()
        sys.exit() 

if __name__ == '__main__':
    game = SuperPang()
    game.play()
