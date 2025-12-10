"""
Superpang game using pygame.
"""
import pygame
import pygame.locals as pl
import sys
import random
import os
from sprites import Player, Balloon, Arrow, INITIAL_SPEED_Y, AUDIO_PATH, ASSETS_PATH, IMAGES_PATH

pygame.init()

FPS = 30
clock = pygame.time.Clock()

# Screen information
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
STAGE_HEIGHT = 560
SPEED = 5

# Predefine some colors
RED   = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption("SuperPang!")

NUM_LIVES = 3
IMAGE_PLAYER_LIFE = pygame.image.load(os.path.join(IMAGES_PATH, "player_life.png"))

# Events.
EVENT_ADD_BALLOON = pygame.USEREVENT+1 # Add a new balloon.
EVENT_EXPLODE = pygame.USEREVENT+2 # Explode one level of balloons.
EVENT_UNFREEZE = pygame.USEREVENT+3 # Unfreeze entities.
EVENT_FRESH_BALLOON_WAIT = pygame.USEREVENT+5 # End the waiting period of new balloons.
EVENT_PAUSE_LABEL_FLASH = pygame.USEREVENT+6 # Flash the "PAUSED" label.
EVENT_INVINCIBILITY = pygame.USEREVENT+7 # Player can't be harmed.
EVENT_BLINK_PLAYER = pygame.USEREVENT+8 # Flash Player icon.

# Intervals between events, in ms.
INTERVAL_FRESH_BALLOON = 20000
INTERVAL_FRESH_BALLOON_WAIT = 2000 
INTERVAL_FREEZE_CLOCK = 4000
INTERVAL_FREEZE_BALLOON = 2000
INTERVAL_FREEZE_LOST_LIFE = 1500
INTERVAL_EXPLODE = 500
INTERVAL_PAUSE_LABEL_FLASH = 800
INTERVAL_INVINCIBILITY = 5000
INTERVAL_BLINK_PLAYER = 300

# Labels for the HUD.
FONTS_PATH = os.path.join(ASSETS_PATH, "fonts")
FONT_FILE_REGULAR = os.path.join(FONTS_PATH, "BitcountPropSingle-Regular.ttf")
FONT_FILE_BOLD = os.path.join(FONTS_PATH, "BitcountPropSingle-Bold.ttf")
LABEL_FONT = pygame.font.Font(FONT_FILE_REGULAR, 30)
BIG_FONT = pygame.font.Font(FONT_FILE_REGULAR, 48)
MASSIVE_FONT = pygame.font.Font(FONT_FILE_BOLD, 62)

# Load the background music and balloon sound effects.
pygame.mixer.music.load(os.path.join(AUDIO_PATH, "theme.ogg"))
AUDIO_POP = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "pop.ogg"))
AUDIO_FIRE = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "fire.ogg"))
AUDIO_OW = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "ow.ogg"))
AUDIO_LEVEL = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "level.ogg"))
AUDIO_APPLAUSE = pygame.mixer.Sound(os.path.join(AUDIO_PATH, "applause.ogg"))

# Miscellaneous constants.
TOTAL_BALLOONS = 100
BALLOON_BOUNDS = {'min_x':0, 'max_x': SCREEN_WIDTH, 'min_y': 0, 'max_y': STAGE_HEIGHT}
# Background image for each level.
BACKGROUND_IMAGES = []
for i in range(1, 11):
    BACKGROUND_IMAGES.append(pygame.image.load(os.path.join(IMAGES_PATH, f"background_{i}.jpg")))

class SuperPang:
    """
    The game class.
    """
    def __init__(self, god_mode=False, fps=FPS):
        """
        Initialise the game.
        """
        self.god_mode = god_mode
        self.fps = fps
        self.set_up()

    def set_up(self):
        """Repeatable set up at the beginning of a game."""
        px, py = SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80
        self.player = Player(initial_x=px, initial_y=py, min_x=0, max_x=SCREEN_WIDTH)
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.make_freezer = True # whether the next balloon should be a freezer.
        b1 = self.fresh_balloon(level_balloon=False)
        # Create sprites collections
        self.balloons = pygame.sprite.Group()
        self.balloons.add(b1)
        # there's only ever one arrow on screen right now, but keeping the
        # group in case I add powerups.
        self.arrows = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(b1)
        self.all_sprites.add(self.player)
        self.is_firing = False # Whether the player is currently firing.
        self.frozen_balloons = False # Whether the balloons are frozen.
        self.frozen_all = False # Whether all sprites are frozen. 
        # ten seconds from first balloon to second one, the interval decreases after that.
        self.balloon_interval = INTERVAL_FRESH_BALLOON
        # Set the event to add the next balloon.
        pygame.time.set_timer(EVENT_ADD_BALLOON, self.balloon_interval)

    def fresh_balloon(self, level_balloon=False):
        """ Make a new, full-size balloon. It appears in either the upper-right or
        upper-left corner. Every other balloon is a freezer, which means that
        one of its size 1 balloons will create a short freeze event when popped.
        If level_balloon is True, create a special balloon that
        either clears the screen or creates a long freeze event when popped.
        """
        self.make_freezer = not self.make_freezer
        x_dir = random.choice([-1, 1]) # Random left or right
        initial_x = 0 if x_dir == 1 else SCREEN_WIDTH - 40
        initial_y, initial_vy = 0, 0
        pygame.time.set_timer(EVENT_FRESH_BALLOON_WAIT, INTERVAL_FRESH_BALLOON_WAIT)
        return Balloon(size=5,
                       initial_x=initial_x,
                       initial_y=initial_y,
                       x_dir=x_dir,
                       vy=initial_vy,
                       bounds=BALLOON_BOUNDS,
                       level_balloon=level_balloon,
                       freezer=self.make_freezer)

    def explode_balloons(self):
        """ Freeze balloons and explode them on a timer."""
        self.frozen_balloons = True
        pygame.time.set_timer(EVENT_EXPLODE, INTERVAL_EXPLODE)

    def explode_one_level(self):
        """
        Handle the explosion of balloons.
        """
        # Pop all balloons, replacing the ones whose size is greater
        # than one with two children.
        if len(self.balloons) > 0:
            new_balloons = []
            added_children = False
            for b in self.balloons:
                if not b.waiting:
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
                        added_children = True
                    b.kill()
                    pygame.mixer.Sound.play(AUDIO_POP)
            for b in new_balloons:
                self.balloons.add(b)
                self.all_sprites.add(b)
            if not added_children:
                # There may still be balloons in the group but they are waiting.
                self.frozen_balloons = False
                pygame.time.set_timer(EVENT_EXPLODE, 0)
        else:
            # We have popped all of the balloons, unfreeze and clear
            # the timer. 
            self.frozen_balloons = False
            pygame.time.set_timer(EVENT_EXPLODE, 0)

    def freeze_balloons(self, interval):
        """ Freeze balloons."""
        self.frozen_balloons = True
        pygame.time.set_timer(EVENT_UNFREEZE, interval)

    def freeze_all(self, interval):
        """ Freeze all entities."""
        self.frozen_all = True
        pygame.time.set_timer(EVENT_UNFREEZE, interval)

    def play(self):
        """
        The game loop.
        """
        pygame.mixer.music.play(-1) # Play the background music.
        # Initialize variables to keep track of the score, level etc.
        balloon_count = 1
        level = 1
        playing = True
        paused = False
        paused_label = True
        lives = NUM_LIVES
        invincible = False
        player_visible = True
    
        while playing:
            # Set background image.
            bg = BACKGROUND_IMAGES[level-1]
            DISPLAYSURF.blit(bg, (0, 0))
        
            end_of_level = False

            # is there an arrow on screen?
            firing = len(self.arrows) > 0

            events = pygame.event.get()
            # Check for pause/unpause before other events.
            for event in events:
                if event.type == pl.QUIT:
                        pygame.quit()
                        sys.exit()
                elif event.type == pl.KEYDOWN and event.key == pl.K_SPACE:
                    paused = not paused
                    if not paused:
                        # Clear the timer that flashes the label.
                        pygame.time.set_timer(EVENT_PAUSE_LABEL_FLASH, 0)
                    else:
                        # Set the timer.
                        pygame.time.set_timer(EVENT_PAUSE_LABEL_FLASH,
                                              INTERVAL_PAUSE_LABEL_FLASH)
                elif event.type == EVENT_PAUSE_LABEL_FLASH:
                    # Allow the "PAUSED" label to flash.
                    paused_label = not paused_label
                    
            if not paused:
                # Handle events.
                for event in events:          
                    if event.type == pl.MOUSEBUTTONDOWN and not firing:
                        firing = True
                        self.player.firing(is_firing=firing)
                        self.fire_arrow()
                        pygame.mixer.Sound.play(AUDIO_FIRE)
                    elif event.type == EVENT_ADD_BALLOON:
                        balloon_count += 1
                        new_level_target = int(balloon_count / 10) + 1
                        if new_level_target > 10:
                            # End of level 10, clear timer
                            pygame.time.set_timer(EVENT_ADD_BALLOON, 0)
                        else:
                            end_of_level = new_level_target > level
                            b = self.fresh_balloon(level_balloon=end_of_level)
                            self.balloons.add(b)
                            self.all_sprites.add(b)
                            if end_of_level:
                                # Decrement the time between balloons.
                                self.balloon_interval = INTERVAL_FRESH_BALLOON - (new_level_target * 100)
                                pygame.time.set_timer(EVENT_ADD_BALLOON, max(800, self.balloon_interval))
                    elif event.type == EVENT_EXPLODE:
                        self.explode_one_level()
                    elif event.type == EVENT_UNFREEZE:
                        self.frozen_balloons = False
                        if self.frozen_all:
                            # player lost a life, make them invincible for a time
                            invincible = True
                            pygame.time.set_timer(EVENT_INVINCIBILITY, INTERVAL_INVINCIBILITY)
                            self.frozen_all = False
                    elif event.type == EVENT_FRESH_BALLOON_WAIT:
                        # Allow new balloons to start moving and be popped.
                        for b in self.balloons:
                            b.waiting = False
                    elif event.type == EVENT_INVINCIBILITY:
                        invincible = False
                        player_visible = True
                        pygame.time.set_timer(EVENT_INVINCIBILITY, 0)
                        pygame.time.set_timer(EVENT_BLINK_PLAYER, 0)
                    elif event.type == EVENT_BLINK_PLAYER:
                        player_visible = not player_visible

                self.move_sprites()

                # Collision detection for player and balloons.
                if not invincible and not (self.frozen_all or self.frozen_balloons) and not self.god_mode:
                    if pygame.sprite.spritecollideany(self.player, self.balloons):
                        pygame.mixer.Sound.play(AUDIO_OW)
                        if lives < 2:
                            # end game
                            lives -= 1
                            self.display_game_over(DISPLAYSURF)
                            playing = False
                        else:
                            lives -= 1
                            self.frozen_all = True
                            pygame.time.set_timer(EVENT_UNFREEZE, INTERVAL_FREEZE_LOST_LIFE)
                            pygame.time.set_timer(EVENT_BLINK_PLAYER, INTERVAL_BLINK_PLAYER)

                if not self.frozen_all:
                    # Collision detection for arrows and balloons.
                    self.collide_arrows_balloons()
                    # Player won the game.
                if len(self.balloons) == 0 and balloon_count == TOTAL_BALLOONS:
                    self.display_won(DISPLAYSURF)
                    playing = False
                    
                new_level = int(balloon_count / 10) + 1
                if new_level > level and new_level <= 10:
                    level = new_level
            else: # is paused
                if paused_label:
                    label = MASSIVE_FONT.render("PAUSED", True, WHITE)
                    label_y = SCREEN_HEIGHT / 2
                    DISPLAYSURF.blit(label, (250, label_y))

            # Draw all sprites.
            self.balloons.draw(DISPLAYSURF)
            self.arrows.draw(DISPLAYSURF)
            if player_visible:
                self.player_group.draw(DISPLAYSURF)

            self.draw_hud(DISPLAYSURF, level, lives)
            
            # Finalize the frame.
            pygame.display.update()
            clock.tick(self.fps)
        # End of the game, wait to play another or end.
        play_again_loop = True
        while play_again_loop:
            for event in pygame.event.get():
                if event.type == pl.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pl.KEYDOWN and event.key == pl.K_SPACE:
                    play_again_loop = False
            clock.tick(self.fps)
        # If we didn't quit, start a new game
        self.set_up()
        self.play()

    def move_sprites(self):
        """ Move the sprites. """
        if not self.frozen_all and not self.frozen_balloons:
            # Move the sprites.
            for entity in self.all_sprites:
                # entity is not a waiting balloon
                if not hasattr(entity, 'waiting') or not entity.waiting:
                    entity.move()
        elif not self.frozen_all:
            # Move the player and arrows only.
            self.player.move()
            for arrow in self.arrows:
                arrow.move()

    def display_game_over(self, surface):
        """ Display game over screen. """
        surface.fill(RED)
        game_over = BIG_FONT.render("GAME OVER!", True, BLACK)
        play_again = BIG_FONT.render("Press space to play again", True, BLACK)
        label_y = SCREEN_HEIGHT / 3
        surface.blit(game_over, (100, label_y))
        surface.blit(play_again, (100, label_y+50))
        pygame.display.update()

    def display_won(self, surface):
        """
        Display the message when the player wins the game.
        """
        surface.fill(GOLD)
        win = BIG_FONT.render("YOU WIN!", True, BLACK)
        play_again = BIG_FONT.render("Press space to play again", True, BLACK)
        label_y = SCREEN_HEIGHT / 2
        surface.blit(win, (200, label_y))
        surface.blit(play_again, (200, label_y+50))
        pygame.mixer.Sound.play(AUDIO_APPLAUSE)
        pygame.display.update()

    def fire_arrow(self):
        """
        Add an Arrow sprite.
        """
        a_x = self.player.rect.centerx
        a_y = STAGE_HEIGHT - 20
        a = Arrow(initial_x=a_x, initial_y=a_y)
        self.arrows.add(a)
        self.all_sprites.add(a)

    def draw_hud(self, surface, level, lives):
        """ Draw the HUD."""
        # Draw the ground.
        pygame.draw.rect(surface,
                         WHITE,
                         pygame.Rect(0,
                                     STAGE_HEIGHT,
                                     SCREEN_WIDTH,
                                     SCREEN_HEIGHT-STAGE_HEIGHT))
        rh_pos = (SCREEN_WIDTH-200, STAGE_HEIGHT+5)
        lh_pos = (10, STAGE_HEIGHT+10)
        level_text = LABEL_FONT.render(f"Level: {level}", True, BLACK)
        life_text = LABEL_FONT.render("Lives:", True, BLACK)
        surface.blit(level_text, lh_pos)
        surface.blit(life_text, rh_pos)
        life_x, life_y = rh_pos
        life_x += 80
        for _ in range(lives):
            surface.blit(IMAGE_PLAYER_LIFE, (life_x, life_y))
            life_x += 40
                
    
    def collide_player(self, surface) -> bool:
        """
        Check for a collision between the player and a balloon. Returns True
        if the game should continue because there was no collision, otherwise False.
        """
        if pygame.sprite.spritecollideany(self.player, self.balloons):
            surface.fill(RED)
            game_over = BIG_FONT.render("GAME OVER!", True, BLACK)
            play_again = BIG_FONT.render("Press space to play again", True, BLACK)
            label_y = SCREEN_HEIGHT / 3
            surface.blit(game_over, (100, label_y))
            surface.blit(play_again, (100, label_y+50))
            pygame.display.update()
            return False
        else:
            return True

    def collide_arrows_balloons(self):
        """
        Check for collisions between arrows and balloons. Regular balloons with a size
        greater than 1 are replaced with two "child" balloons whose size is one less
        than their parent. Level balloons are either Star balloons, which cause all
        other balloons to explode, or Clock balloons, which initiate a long freeze.
        Some size 1 balloons are freezers, which initiate a short freeze.
        """
        for b in self.balloons:
            hit_list = pygame.sprite.spritecollide(b, self.arrows, dokill=True)
            if len(hit_list) > 0:
                # If b is a level balloon, explode all other balloons or begin
                # a long freeze event.
                if b.level_balloon:
                    if b.star:
                        self.explode_balloons()
                    else:
                        self.freeze_balloons(INTERVAL_FREEZE_CLOCK)
                elif b.size > 1 and not b.waiting:
                    # Replace the balloon with two smaller ones.
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
                    # The balloon is a size 1 freezer.
                    self.freeze_balloons(INTERVAL_FREEZE_BALLOON)
                if not b.waiting:
                    # For every type of balloon except on which is waiting,
                    # play the sound effect and remove the balloon.
                    if b.level_balloon:
                        pygame.mixer.Sound.play(AUDIO_LEVEL)
                    else:
                        pygame.mixer.Sound.play(AUDIO_POP)
                    b.kill()

if __name__ == '__main__':
    god_mode = False
    fps = FPS
    if len(sys.argv) > 1:
        if sys.argv[1] == "GOD_MODE":
            god_mode = True
    if len(sys.argv) == 4:
        if sys.argv[2] == "FPS":
            fps = int(sys.argv[3])
    game = SuperPang(god_mode, fps)
    game.play()
