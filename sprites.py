import pygame
import pygame.locals as pl

# --- Physics Constants ---
# Vertical acceleration due to gravity. The higher this value, the faster the arc.
GRAVITY = 0.5 
# Initial horizontal speed (constant).
INITIAL_SPEED_X = 3
# Initial vertical speed (upwards) when the balloon is created or bounces.
INITIAL_SPEED_Y = 20 
# Bounce Damping: 1.0 is a perfect bounce (no energy lost, constant height). 
# Use 0.95 to simulate slight energy loss (the balloon bounces slightly lower each time).
DAMPING_FACTOR = 1.0 

class Player(pygame.sprite.Sprite):
    def __init__(self, initial_x, initial_y, min_x, max_x):
        super().__init__() 
        self.image = pygame.image.load("player.png")
        self.rect = self.image.get_rect()
        self.rect.center = (initial_x, initial_y)
        self.min_x = min_x
        self.max_x = max_x
 
    def move(self):
        pressed_keys = pygame.key.get_pressed()

        if self.rect.left > self.min_x:
              if pressed_keys[pl.K_LEFT]:
                  self.rect.move_ip(-5, 0)
        if self.rect.right < self.max_x:        
              if pressed_keys[pl.K_RIGHT]:
                  self.rect.move_ip(5, 0)

class Balloon(pygame.sprite.Sprite):
      def __init__(self, size, initial_x, initial_y, x_dir, vy, bounds):
          """ 3 is the largest size balloon."""
          super().__init__()
          self.size = size
          image = pygame.image.load("balloon.png")
          # return a width and height of an image
          img_size = image.get_size()
          # scale the image
          self.image = pygame.transform.scale(image, (int(img_size[0]*self.size), int(img_size[1]*self.size)))
          self.rect = self.image.get_rect()
          self.rect.center=(initial_x, initial_y)
          # Velocities (float for smooth movement)
          
          self.vx = INITIAL_SPEED_X * x_dir
          self.vy = vy        
          self.x = float(self.rect.x)
          self.y = float(self.rect.y)
          self.bounds = bounds
 
      def move(self):
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
          # 4. Handle Floor Collision (Vertical Bounce)
          if self.y >= self.bounds['max_y']:
              self.vy = -INITIAL_SPEED_Y * DAMPING_FACTOR 
              self.y = self.bounds['max_y'] - self.rect.height # Prevent falling through the floor
            
        
          # 5. Sync Rect position with float position
          self.rect.x = int(self.x)
          self.rect.y = int(self.y)

class Arrow(pygame.sprite.Sprite):
      def __init__(self, initial_x, initial_y, speed):
        super().__init__() 
        self.image = pygame.image.load("arrow.png")
        self.rect = self.image.get_rect()
        self.rect.center=(initial_x, initial_y)
        self.speed = speed
 
      def move(self):
        if self.rect.top > 0:
            self.rect.move_ip(0,-self.speed)
        else:
            self.kill()
