import sys
import math
import pygame
import time



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

# Vector Field Histogram
N_BINS = 36
BIN_SIZE = 360 / N_BINS
DETECTION_RANGE = 200

# Additional parameters for line of sight & collision avoidance
FOV_DEG = 270  # total field-of-view in degrees for "line of sight"
FOV_RAD = math.radians(FOV_DEG)
SOFT_COLLISION_DIST = 80  # distance threshold below which we apply a "push away"

custom_obstacles = []

def compute_vfh(pos_x, pos_y, obstacles, n_bins=N_BINS, detection_range=DETECTION_RANGE):
    """
    Vector Field Histogram using closest point on each obstacle.
    For obstacles within detection_range, weight = (detection_range - distance) / detection_range.
    """
    histogram = [0] * n_bins
    for obs in obstacles:
        r = obs["rect"]
        # Closest point
        closest_x = max(r.x, min(pos_x, r.x + r.width))
        closest_y = max(r.y, min(pos_y, r.y + r.height))
        
        dx = closest_x - pos_x
        dy = closest_y - pos_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance == 0 or distance > detection_range:
            continue
        
        angle = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        weight = (detection_range - distance) / detection_range
        bin_index = int(angle // BIN_SIZE) % n_bins
        histogram[bin_index] += weight
    return histogram

def draw_obstacle_vectors(
    surface,
    robot_center,     # (x, y) of the robot
    robot_angle,      # heading in radians
    obstacles,
    color=(255, 255, 0)   # yellow
):
    """
    Draw lines from the robot to obstacles *only if* they are in line of sight (within FOV)
    and within detection range.
    """
    rx, ry = robot_center
    
    for obs in obstacles:
        rect = obs["rect"]
        
        # Closest point
        closest_x = max(rect.x, min(rx, rect.x + rect.width))
        closest_y = max(rect.y, min(ry, rect.y + rect.height))
        
        dx = closest_x - rx
        dy = closest_y - ry
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < 1 or distance > DETECTION_RANGE:
            continue
        
        # Angle difference from heading
        global_angle = math.atan2(dy, dx)
        angle_diff = (global_angle - robot_angle + math.pi) % (2*math.pi) - math.pi
        
        # If outside the FOV, skip
        if abs(angle_diff) > FOV_RAD / 2.0:
            continue
        
        # Draw line: length = distance
        end_x = rx + distance * math.cos(global_angle)
        end_y = ry + distance * math.sin(global_angle)
        
        pygame.draw.line(surface, color, (rx, ry), (end_x, end_y), 2)
        pygame.draw.circle(surface, color, (int(end_x), int(end_y)), 3)

def draw_histogram(surface, pos, histogram, max_height=50):
    bin_width = 10
    for i, value in enumerate(histogram):
        height = int(value * max_height)
        rect = pygame.Rect(pos[0] + i * bin_width, pos[1] + max_height - height, bin_width - 1, height)
        pygame.draw.rect(surface, (255, 0, 0), rect)

def get_obstacles():
    obstacles = []
    # Example default obstacles
    obstacles.append({"rect": pygame.Rect(660, 0, 30, 150), "color": (128, 128, 128)})
    obstacles.append({"rect": pygame.Rect(750, 0, 30, 150), "color": (128, 128, 128)})
    obstacles.append({"rect": pygame.Rect(440, 150, 250, 20), "color": (0, 128, 0)})
    obstacles.append({"rect": pygame.Rect(440, 260, 400, 20), "color": (0, 128, 0)})
    obstacles.append({"rect": pygame.Rect(750, 150, 100, 20), "color": (0, 128, 0)})
    obstacles.append({"rect": pygame.Rect(30, 350, 150, 80),  "color": (200, 0, 0)})
    obstacles.append({"rect": pygame.Rect(250, 350, 80, 50),  "color": (200, 0, 0)})
    obstacles.append({"rect": pygame.Rect(30, 500, 40, 40),   "color": (200, 0, 0)})
    obstacles.append({"rect": pygame.Rect(150, 500, 60, 40),  "color": (200, 0, 0)})
    
    # Custom obstacles (user-added)
    obstacles.extend(custom_obstacles)
    return obstacles

def add_obstacle_mode(screen, clock, font):
    adding = True
    while adding:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click_pos = event.pos
                new_rect = pygame.Rect(click_pos[0], click_pos[1], 50, 50)
                new_obstacle = {"rect": new_rect, "color": (255, 255, 0)}
                custom_obstacles.append(new_obstacle)
                adding = False
        screen.fill((50, 50, 50))
        instructions = font.render("Click anywhere to place a new square obstacle.", True, (255, 255, 255))
        screen.blit(instructions, (50, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        clock.tick(60)

def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheelchair Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    
    # Now we have 4 buttons: 1) "head" 2) "head_sip" 3) "xbox" 4) add obstacle
    button1 = pygame.Rect(150, 100, 500, 50)
    button2 = pygame.Rect(150, 200, 500, 50)
    button3 = pygame.Rect(150, 300, 500, 50)
    button4 = pygame.Rect(150, 400, 500, 50)
    
    mode = None
    while mode is None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if button1.collidepoint(pos):
                    mode = "head"
                elif button2.collidepoint(pos):
                    mode = "head_sip"
                elif button3.collidepoint(pos):
                    mode = "xbox"
                elif button4.collidepoint(pos):
                    add_obstacle_mode(screen, clock, font)
        
        screen.fill((50, 50, 50))
        title_surface = font.render("Wheelchair Simulation", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 40))
        screen.blit(title_surface, title_rect)
        
        pygame.draw.rect(screen, (100, 200, 100), button1)
        pygame.draw.rect(screen, (100, 200, 100), button2)
        pygame.draw.rect(screen, (100, 200, 100), button3)
        pygame.draw.rect(screen, (100, 200, 100), button4)
        
        text1 = font.render("Joystick + Head-control (Arrow keys + z/x)", True, (0, 0, 0))
        text2 = font.render("Head control + Sip and Puff (i/l/p/k + z/x)", True, (0, 0, 0))
        text3 = font.render("Xbox Controller (Right Joystick)", True, (0, 0, 0))
        text4 = font.render("Add New Square Obstacle", True, (0, 0, 0))
        
        screen.blit(text1, text1.get_rect(center=button1.center))
        screen.blit(text2, text2.get_rect(center=button2.center))
        screen.blit(text3, text3.get_rect(center=button3.center))
        screen.blit(text4, text4.get_rect(center=button4.center))
        
        pygame.display.flip()
        clock.tick(60)
    return mode

def apply_soft_collision_avoidance(pos_x, pos_y, angle, forward_speed, turning_input, obstacles):
    """
    Apply soft collision avoidance only if an obstacle directly in the path
    (based on the effective heading) is too close.
    """
    if forward_speed >= 0:
        effective_heading = angle
    else:
        effective_heading = (angle + math.pi) % (2 * math.pi)
    
    min_dist = None
    best_angle_diff = 0
    for obs in obstacles:
        rect = obs["rect"]
        # Find the closest point on the rectangle
        closest_x = max(rect.x, min(pos_x, rect.x + rect.width))
        closest_y = max(rect.y, min(pos_y, rect.y + rect.height))
        
        dx = closest_x - pos_x
        dy = closest_y - pos_y
        distance = math.sqrt(dx*dx + dy*dy)
        if distance < 1 or distance > DETECTION_RANGE:
            continue
        
        global_angle = math.atan2(dy, dx)
        angle_diff = (global_angle - effective_heading + math.pi) % (2*math.pi) - math.pi
        
        # Only consider obstacles in the forward direction within the FOV
        if abs(angle_diff) > FOV_RAD / 2.0:
            continue
        
        # Ensure it's "in front" relative to effective heading
        eff_vec = (math.cos(effective_heading), math.sin(effective_heading))
        dot = dx * eff_vec[0] + dy * eff_vec[1]
        if dot < 0:
            continue
        
        if min_dist is None or distance < min_dist:
            min_dist = distance
            best_angle_diff = angle_diff
    
    if min_dist is not None and min_dist < SOFT_COLLISION_DIST:
        scale = min_dist / SOFT_COLLISION_DIST
        forward_speed *= scale
        turning_input -= TURNING_SCALE * best_angle_diff
    return forward_speed, turning_input


def simulation(mode):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheelchair Simulation")
    clock = pygame.time.Clock()
    last_print_time = 0.0
    
    # Attempt to initialize joystick if using "xbox" mode
    joystick = None
    if mode == "xbox":
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            print("Using Joystick:", joystick.get_name())
        else:
            print("No joystick detected. Falling back to no movement.")
    
    pos_x, pos_y = START_POS
    angle = START_ANGLE
    wheelchair_surf = pygame.Surface((WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT), pygame.SRCALPHA)
    wheelchair_surf.fill(COLOR_WHEELCHAIR)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        obstacles = get_obstacles()  # get latest obstacles (including user-added)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        forward_speed = 0
        user_turning_input = 0
        
        if mode == "head":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_DOWN]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_LEFT]:
                user_turning_input = -TURNING_SCALE
            elif keys[pygame.K_RIGHT]:
                user_turning_input = TURNING_SCALE
            if keys[pygame.K_z]:
                user_turning_input -= FINE_TURN_SCALE
            if keys[pygame.K_x]:
                user_turning_input += FINE_TURN_SCALE
        
        elif mode == "head_sip":
            keys = pygame.key.get_pressed()
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
        
        elif mode == "xbox":
    # Use the right stick for forward/back and left/right turning
    # Axis 2 (horizontal) = turning, axis 3 (vertical) = forward/back
    # NOTE: Make sure you've done "pygame.joystick.init()" and joystick detection outside if needed.

            # Just skip if we have no joystick
            if joystick is not None:
                try:
                    now = time.time()
                    # Print axes for debugging every 0.5s
                    #if now - last_print_time >= 0.5:
                        #axis_vals = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
                        #print("Axis values:", axis_vals)
                        #last_print_time = now

                    axis_turn = joystick.get_axis(2)   # right stick horizontal
                    axis_forward = joystick.get_axis(3)   # right stick vertical

                    DEADZONE = 0.15
                    if abs(axis_turn) < DEADZONE:
                        axis_turn = 0
                    if abs(axis_forward) < DEADZONE:
                        axis_forward = 0

                    # Up on the stick is typically negative => invert if you want up=forward
                    forward_speed = -axis_forward * SPEED_SCALE
                    # If axis_turn is +1 at far right => turning_input is +2 => turn right
                    turning_input = axis_turn * TURNING_SCALE

                except Exception as e:
                    print("Joystick error:", e)
                    forward_speed = 0
                    turning_input = 0

        # 2) VFH lane-keep
        obstacles = get_obstacles()
        vfh = compute_vfh(pos_x, pos_y, obstacles)
        current_heading_deg = (math.degrees(angle) + 360) % 360
        current_bin = int(current_heading_deg // BIN_SIZE)
        density_ahead = vfh[current_bin]

        THRESHOLD = 0.5
        vfh_turn_adjustment = 0
        if density_ahead > THRESHOLD:
            best_bin = min(range(N_BINS), key=lambda i: vfh[i])
            desired_heading = math.radians(best_bin * BIN_SIZE + BIN_SIZE/2)
            angle_diff = (desired_heading - angle + math.pi) % (2*math.pi) - math.pi
            vfh_turn_adjustment = TURNING_SCALE * angle_diff

        forward_threshold = 0.5
        forward_scaling = 1.0
        if density_ahead > forward_threshold:
            forward_scaling = max(0, 1 - (density_ahead - forward_threshold) / (1 - forward_threshold))
        forward_speed *= forward_scaling

        turning_input += vfh_turn_adjustment

        # 3) Soft collision avoidance
        forward_speed, turning_input = apply_soft_collision_avoidance(
            pos_x, pos_y, angle, forward_speed, turning_input, obstacles
        )

        # 4) Update the angle and position
        angle += turning_input * dt
        pos_x += forward_speed * math.cos(angle) * dt
        pos_y += forward_speed * math.sin(angle) * dt

        # 5) Simple collision detection
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
        
        # Draw lines only for obstacles in line of sight
        draw_obstacle_vectors(
            surface=screen,
            robot_center=(pos_x, pos_y),
            robot_angle=angle,
            obstacles=obstacles,
            color=(255, 255, 0)
        )
        
        # Draw the wheelchair
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
