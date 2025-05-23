import sys
import math
import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Wheelchair parameters
WHEELCHAIR_WIDTH = 40
WHEELCHAIR_HEIGHT = 60
START_POS = (100, 100)
START_ANGLE = 0  # in radians

# Movement scales
SPEED_SCALE = 200       # pixels per second for forward/backward motion
TURNING_SCALE = 2.0     # radians per second for main turning input
FINE_TURN_SCALE = 0.5   # additional radians per second from fine-tune keys (z and x)

# Colors
COLOR_BG = (30, 30, 30)
COLOR_WHEELCHAIR = (0, 200, 0)

N_BINS = 36           # Number of bins (each bin covers 10 degrees)
BIN_SIZE = 360 / N_BINS

# Set a detection range for obstacles (in pixels)
DETECTION_RANGE = 300

def compute_vfh(pos_x, pos_y, obstacles, n_bins=N_BINS, detection_range=DETECTION_RANGE):
    """
    Compute a simple vector field histogram.
    For obstacles within the detection_range, the weight is computed as:
       weight = (detection_range - distance) / detection_range
    so that obstacles very close have weight ~1 and obstacles at the edge have weight ~0.
    """
    histogram = [0] * n_bins
    for obs in obstacles:
        r = obs["rect"]
        # Compute obstacle center
        obs_cx = r.x + r.width / 2.0
        obs_cy = r.y + r.height / 2.0
        
        dx = obs_cx - pos_x
        dy = obs_cy - pos_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance == 0 or distance > detection_range:
            continue
        
        # Compute angle from the robot to the obstacle in degrees (0 to 360)
        angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        # Weight increases as distance decreases (closer obstacles have higher weight)
        weight = (detection_range - distance) / detection_range
        bin_index = int(angle // BIN_SIZE) % n_bins
        histogram[bin_index] += weight

    return histogram

def draw_vfh_arrows(surface, robot_center, robot_angle, histogram, scale=100):
    """
    Draws arrows emanating from robot_center representing the VFH.
    The robot_angle (in radians) is used to rotate the arrows so that
    they are displayed relative to the wheelchair's forward direction.
    
    Each arrow's direction corresponds to the bin's center angle, and
    its length is proportional to the histogram weight in that bin.
    """
    for i, weight in enumerate(histogram):
        # Compute the global angle for the center of this bin (in degrees)
        bin_center_deg = i * BIN_SIZE + BIN_SIZE / 2.0
        # Convert to radians and transform into the robot's local frame by subtracting robot_angle
        local_angle = math.radians(bin_center_deg) - robot_angle
        
        # Compute arrow length scaled by weight (adjust scale factor as needed)
        arrow_length = weight * scale
        
        # Compute arrow endpoint relative to robot_center
        end_x = robot_center[0] + arrow_length * math.cos(local_angle)
        end_y = robot_center[1] + arrow_length * math.sin(local_angle)
        
        # Draw the arrow as a line (yellow color here)
        pygame.draw.line(surface, (255, 255, 0), robot_center, (end_x, end_y), 2)
        
        # Optionally, draw a small circle at the tip for clarity
        pygame.draw.circle(surface, (255, 255, 0), (int(end_x), int(end_y)), 3)

def draw_histogram(surface, pos, histogram, max_height=50):
    """
    Draws a simple vertical histogram on the given surface.
    'pos' is the top-left position where the histogram is drawn.
    Each bin is drawn as a vertical red bar.
    """
    bin_width = 10
    for i, value in enumerate(histogram):
        # Scale the value to a height (if value=1, height=max_height)
        height = int(value * max_height)
        rect = pygame.Rect(pos[0] + i * bin_width, pos[1] + max_height - height, bin_width - 1, height)
        pygame.draw.rect(surface, (255, 0, 0), rect)  # red bars

def get_obstacles():
    obstacles = []
    # Left obstacle: Grass (green)
    obstacles.append({
        "rect": pygame.Rect(660, 0, 30, 150),
        "color": (128, 128, 128)  # grey
    })
    # Right obstacle: Road (grey)
    obstacles.append({
        "rect": pygame.Rect(750, 0, 30, 150),
        "color": (128, 128, 128)  # grey
    })
    # Ramp obstacles
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
    # Bedroom layout obstacles
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
                    mode = "head"      # Head-control using arrow keys (+ z/x for fine turn)
                elif button2.collidepoint(pos):
                    mode = "head_sip"  # Head control + Sip and Puff (i/l/p/k + z/x for fine turn)
        
        screen.fill((50, 50, 50))
        title_surface = font.render("Wheelchair Simulation", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)
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
    
    pos_x, pos_y = START_POS
    angle = START_ANGLE
    wheelchair_surf = pygame.Surface((WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT), pygame.SRCALPHA)
    wheelchair_surf.fill(COLOR_WHEELCHAIR)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Get user inputs
        keys = pygame.key.get_pressed()
        forward_speed = 0
        user_turning_input = 0
        
        if mode == "head":
            if keys[pygame.K_UP]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_DOWN]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_LEFT]:
                user_turning_input = -TURNING_SCALE
            elif keys[pygame.K_RIGHT]:
                user_turning_input = TURNING_SCALE
        elif mode == "head_sip":
            if keys[pygame.K_i]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_l]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_p]:
                user_turning_input = -TURNING_SCALE
            elif keys[pygame.K_k]:
                user_turning_input = TURNING_SCALE
        
        if keys[pygame.K_z]:
            user_turning_input -= FINE_TURN_SCALE
        if keys[pygame.K_x]:
            user_turning_input += FINE_TURN_SCALE
        
        # ---- Compute VFH BEFORE updating state ----
        vfh = compute_vfh(pos_x, pos_y, obstacles)
        current_heading_deg = (math.degrees(angle) + 360) % 360
        current_bin = int(current_heading_deg // BIN_SIZE)
        density_ahead = vfh[current_bin]
        
        # Adjust turning based on VFH as before:
        THRESHOLD = 0.5  # tuning parameter for turning adjustment
        vfh_turn_adjustment = 0
        if density_ahead > THRESHOLD:
            best_bin = min(range(N_BINS), key=lambda i: vfh[i])
            desired_heading = math.radians(best_bin * BIN_SIZE + BIN_SIZE/2)
            angle_diff = (desired_heading - angle + math.pi) % (2*math.pi) - math.pi
            vfh_turn_adjustment = TURNING_SCALE * angle_diff
        
        # ---- New: Adjust forward/backward input ----
        # If obstacles are too dense ahead, scale down the forward speed.
        forward_threshold = 0.5  # tuning parameter for forward speed adjustment
        forward_scaling = 1.0
        if density_ahead > forward_threshold:
            # As density increases from the threshold to 1, scaling reduces from 1 to 0.
            forward_scaling = max(0, 1 - (density_ahead - forward_threshold) / (1 - forward_threshold))
            # Optionally, you can print/log forward_scaling for debugging.
        
        forward_speed *= forward_scaling
        
        # Combine turning adjustments (user input + VFH)
        turning_input = user_turning_input + vfh_turn_adjustment
        
        # ---- Update state ----
        angle += turning_input * dt
        pos_x += forward_speed * math.cos(angle) * dt
        pos_y += forward_speed * math.sin(angle) * dt
        
        # Simple collision detection using the wheelchair's rectangle
        wheelchair_rect = pygame.Rect(0, 0, WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT)
        wheelchair_rect.center = (pos_x, pos_y)
        if any(wheelchair_rect.colliderect(obs["rect"]) for obs in obstacles):
            print("Collision detected! Resetting position.")
            pos_x, pos_y = START_POS
            angle = START_ANGLE
        
        # ----- Drawing -----
        screen.fill(COLOR_BG)
        for obs in obstacles:
            pygame.draw.rect(screen, obs["color"], obs["rect"])
        
        # Draw the VFH histogram (optional)
        draw_histogram(screen, (10, 10), vfh)
        # And draw VFH arrows emanating from the wheelchair (optional)
        draw_vfh_arrows(screen, (int(pos_x), int(pos_y)), angle, vfh, scale=100)
        
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
