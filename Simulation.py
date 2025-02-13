
import sys
import math
import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

#Wheelchair parameters
WHEELCHAIR_WIDTH = 40
WHEELCHAIR_HEIGHT = 60
START_POS = (100, 100)
START_ANGLE = 0  # in radians

#Movement scales
SPEED_SCALE = 200       #pixels per second for forward/backward motion
TURNING_SCALE = 2.0     #radians per second for main turning input
FINE_TURN_SCALE = 0.5   #additional radians per second from fine-tune keys (z and x)

#Colors
COLOR_BG = (30, 30, 30)
COLOR_WHEELCHAIR = (0, 200, 0)


def get_obstacles():
   
    obstacles = []
    #Left obstacle: Grass (green)
    obstacles.append({
        "rect": pygame.Rect(660, 0, 30, 150),
        "color": (128, 128, 128)  # grey
    })
    # Right obstacle: Road (grey)
    obstacles.append({
        "rect": pygame.Rect(750, 0, 30, 150),
        "color": (128, 128, 128)  # grey
    })
    # Ramp obstacle
    obstacles.append({
        "rect": pygame.Rect(440, 150, 250, 20),
        "color": (0, 128, 0)  # 1sidewalk
    })
    obstacles.append({
        "rect": pygame.Rect(440, 260, 400, 20),
        "color": (0, 128, 0)  # 2sidewalk
    })
    obstacles.append({
        "rect": pygame.Rect(750, 150, 100, 20),
        "color": (0, 128, 0)  # 3sidewalk 
    })
    
    #bedroom layout (obstacles spaced out)
    obstacles.append({
        "rect": pygame.Rect(30, 350, 150, 80),
        "color": (200, 0, 0)  # bed (red)
    })
    obstacles.append({
        "rect": pygame.Rect(250, 350, 80, 50),
        "color": (200, 0, 0)  # dresser (red)
    })
    obstacles.append({
        "rect": pygame.Rect(30, 500, 40, 40),
        "color": (200, 0, 0)  # nightstand (red)
    })
    obstacles.append({
        "rect": pygame.Rect(150, 500, 60, 40),
        "color": (200, 0, 0)  # table (red)
    })
    return obstacles


def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheelchair Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    
    # Define two buttons
    button1 = pygame.Rect(150, 200, 500, 50)
    button2 = pygame.Rect(150, 300, 500, 50)
    
    mode = None
    while mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if button1.collidepoint(pos):
                    mode = "head"      #Head-control using arrow keys (+ z/x for fine turn)
                elif button2.collidepoint(pos):
                    mode = "head_sip"  #Head control + Sip and Puff (i, l, p, k for main movement, + z/x for fine turn)
        
        screen.fill((50, 50, 50))
        # Draw title text
        title_surface = font.render("Wheelchair Simulation", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)
        
        # Draw buttons and labels
        pygame.draw.rect(screen, (100, 200, 100), button1)
        pygame.draw.rect(screen, (100, 200, 100), button2)
        
        text1 = font.render("Joystick + Head-control (Arrow keys + z/x)", True, (0, 0, 0))
        text2 = font.render("Head control + Sip and Puff (i/l/p/k + z/x)", True, (0, 0, 0))
        screen.blit(text1, text1.get_rect(center=button1.center))
        screen.blit(text2, text2.get_rect(center=button2.center))
        
        pygame.display.flip()
        clock.tick(60)
    
    return mode

def simulation(mode):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheelchair Simulation")
    clock = pygame.time.Clock()
    
    obstacles = get_obstacles()
    
    # Initialize wheelchair state
    pos_x, pos_y = START_POS
    angle = START_ANGLE
    wheelchair_surf = pygame.Surface((WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT), pygame.SRCALPHA)
    wheelchair_surf.fill(COLOR_WHEELCHAIR)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds since last frame
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        keys = pygame.key.get_pressed()
        forward_speed = 0
        turning_input = 0
        
        if mode == "head":
            # Main movement via arrow keys:
            if keys[pygame.K_UP]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_DOWN]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_LEFT]:
                turning_input = -TURNING_SCALE
            elif keys[pygame.K_RIGHT]:
                turning_input = TURNING_SCALE
            
        elif mode == "head_sip":
            #Main movement via Sip and Puff keys:
            if keys[pygame.K_i]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_l]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_p]:
                turning_input = -TURNING_SCALE
            elif keys[pygame.K_k]:
                turning_input = TURNING_SCALE
        
        #In both modes, use z and x for fine turn adjustments.
        if keys[pygame.K_z]:
            turning_input -= FINE_TURN_SCALE
        if keys[pygame.K_x]:
            turning_input += FINE_TURN_SCALE
        
        angle += turning_input * dt
        pos_x += forward_speed * math.cos(angle) * dt
        pos_y += forward_speed * math.sin(angle) * dt
        
        # Create a collision rectangle for the wheelchair
        wheelchair_rect = pygame.Rect(0, 0, WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT)
        wheelchair_rect.center = (pos_x, pos_y)
        
        # Check for collision with any obstacle (using each obstacle's "rect")
        if any(wheelchair_rect.colliderect(obs["rect"]) for obs in obstacles):
            print("Collision detected! Resetting wheelchair position.")
            pos_x, pos_y = START_POS
            angle = START_ANGLE
        
        screen.fill(COLOR_BG)
        
        # Draw obstacles with their defined colors
        for obs in obstacles:
            pygame.draw.rect(screen, obs["color"], obs["rect"])
        
        # Rotate the wheelchair image according to its angle
        rotated_surf = pygame.transform.rotate(wheelchair_surf, -math.degrees(angle))
        rotated_rect = rotated_surf.get_rect(center=(pos_x, pos_y))
        screen.blit(rotated_surf, rotated_rect.topleft)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


def main():
    mode = main_menu()  
    simulation(mode)    

if __name__ == "__main__":
    main()
