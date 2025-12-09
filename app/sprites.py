"""
Sprites for the game.
"""
import pygame
import pygame.locals as pl
import os

# Physics Constants
# Vertical acceleration due to gravity. The higher this value, the faster the arc.
GRAVITY = 0.5 
# Initial horizontal speed (constant).
INITIAL_SPEED_X = 3
# Initial vertical speed (upwards) when the balloon is created or bounces.
INITIAL_SPEED_Y = 20 
# Bounce Damping: 1.0 is a perfect bounce (no energy lost, constant height). 
# Use 0.95 to simulate slight energy loss (the balloon bounces slightly lower each time).
DAMPING_FACTOR = 1.0

# Paths to assets
ASSETS_PATH = "assets"
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")
AUDIO_PATH = os.path.join(ASSETS_PATH, "audio")
IMAGE_PLAYER_STANDING = pygame.image.load(os.path.join(IMAGES_PATH, "player_standing.png"))
IMAGE_PLAYER_FIRING = pygame.image.load(os.path.join(IMAGES_PATH, "player_firing.png"))
IMAGE_PLAYER_LEFT_0 = pygame.image.load(os.path.join(IMAGES_PATH, "player_left_0.png"))
IMAGE_ARROW = pygame.image.load(os.path.join(IMAGES_PATH, "arrow.png"))

IMAGE_BALLOON_5 = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_5.png"))
IMAGE_BALLOON_4 = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_4.png"))
IMAGE_BALLOON_3 = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_3.png"))
IMAGE_BALLOON_2 = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_2.png"))
IMAGE_BALLOON_1 = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_1.png"))
BALLOONS = {1: IMAGE_BALLOON_1,
            2: IMAGE_BALLOON_2,
            3: IMAGE_BALLOON_3,
            4: IMAGE_BALLOON_4,
            5: IMAGE_BALLOON_5}
IMAGE_BALLOON_FREEZE = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_1_freeze.png")) 
IMAGE_BALLOON_STAR = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_star.png"))
IMAGE_BALLOON_CLOCK = pygame.image.load(os.path.join(IMAGES_PATH, "balloon_clock.png"))

class Player(pygame.sprite.Sprite):
    """ The player sprite."""
    def __init__(self, initial_x, initial_y, min_x, max_x):
        """
        Create a new Player with the initial coordinates and that can move in the
        given bounds.
        """ 
        super().__init__() 
        self.image = IMAGE_PLAYER_STANDING
        self.rect = self.image.get_rect()
        self.rect.center = (initial_x, initial_y)
        self.min_x = min_x
        self.max_x = max_x
        self.is_firing = False
        self.animate_tick = 0
 
    def move(self):
        """
        Move the sprite if the left or right arrow key is pressed. Also changes
        the image depending on the direction the player is moving in. 
        """
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pl.K_LEFT] or pressed_keys[pl.K_RIGHT]:
            image = IMAGE_PLAYER_STANDING
            if pressed_keys[pl.K_LEFT] and self.rect.left > self.min_x:
                self.rect.move_ip(-8, 0)
                image = IMAGE_PLAYER_LEFT_0
            elif pressed_keys[pl.K_RIGHT] and self.rect.right < self.max_x:        
                self.rect.move_ip(8, 0)
                image = pygame.transform.flip(IMAGE_PLAYER_LEFT_0, flip_x=True, flip_y=False)
            self.set_image(image)

    def firing(self, is_firing):
        """
        Switch the image when the player is firing.
        """
        self.is_firing = is_firing
        if is_firing:
            self.set_image(IMAGE_PLAYER_FIRING)
        else:
            self.set_image(IMAGE_PLAYER_STANDING)

    def set_image(self, image):
        """
        Change the image used to represent the sprite.
        """
        x,y = self.rect.centerx, self.rect.centery
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        

class Balloon(pygame.sprite.Sprite):
    """
    Class for the Balloon sprite.
    """
    def __init__(self,
                 size,
                 initial_x,
                 initial_y,
                 x_dir,
                 vy,
                 bounds,
                 level_balloon=False,
                 freezer=False):
        """
        Create a new balloon sprite with the given attributes.
        """
        super().__init__()
        self.size = size
        if level_balloon:
            image = IMAGE_BALLOON_STAR
        elif size == 1 and freezer:
            image = IMAGE_BALLOON_FREEZE
        else:
            image = BALLOONS[size]
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center=(initial_x, initial_y)
        # Velocities (float for smooth movement)
        self.vx = INITIAL_SPEED_X * x_dir
        self.vy = vy        
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        self.bounds = bounds
        self.level_balloon = level_balloon
        self.star = True # flip between star and clock on each bounce
        self.freezer=freezer
        self.flash_off = True
        self.waiting = size == 5

    def level_balloon_flip(self):
        """
        Toggle the image for level balloons.
        """
        if self.star:
            self.image = IMAGE_BALLOON_CLOCK
            self.star = False
        else:
            self.image = IMAGE_BALLOON_STAR
            self.star = True
          
    def move(self):
        """
        Move the sprite.
        """
        # Apply Gravity (Acceleration): This creates the arc motion.
        # Vertical velocity is constantly increasing (downwards)
        self.vy += GRAVITY
        
        # Update Position: Use float positions, then sync with rect
        self.x += self.vx
        self.y += self.vy
        
        # Handle Wall Collisions (Horizontal Bounce)
        if self.rect.left <= self.bounds['min_x']:
            self.vx *= -1 # Reverse horizontal direction
            self.x = 1 # Prevent sticking to the wall
        elif self.rect.right >= self.bounds['max_x']:
            self.vx *= -1 # Reverse horizontal direction
            self.x = self.bounds['max_x'] - self.rect.width - 1 # Prevent sticking
        # Handle Floor Collision (Vertical Bounce)
        if self.y >= self.bounds['max_y'] - self.rect.height:
            self.vy = -INITIAL_SPEED_Y * DAMPING_FACTOR 
            self.y = self.bounds['max_y'] - self.rect.height # Prevent falling through the floor
            if self.level_balloon:
                self.level_balloon_flip()
        
        # Sync Rect position with float position
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

class Arrow(pygame.sprite.Sprite):
    """
    Class for the arrow sprite.
    """
    def __init__(self, initial_x, initial_y, speed):
        """
        Create an new Arrow sprite.
        """
        super().__init__() 
        self.image = IMAGE_ARROW
        self.rect = self.image.get_rect()
        self.rect.center=(initial_x, initial_y)
        self.speed = speed
 
    def move(self):
        """
        Move the sprite, removing it when it reaches the top of the screen.
        """
        if self.rect.top > 0:
            self.rect.move_ip(0,-self.speed)
        else:
            self.kill()
