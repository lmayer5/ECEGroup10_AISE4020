
import sys
import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Wheelchair parameters (3D)
WHEELCHAIR_WIDTH = 20
WHEELCHAIR_HEIGHT = 20    # Lower height for better view
WHEELCHAIR_DEPTH = 40
START_POS = (100, 100)    # (x, z) position on the ground
START_ANGLE = 0           # in radians

# Movement scales
SPEED_SCALE = 200       # units per second
TURNING_SCALE = 2.0     # radians per second (main turning)
FINE_TURN_SCALE = 0.5   # additional radians per second (fine turn)

# Colors (RGB)
COLOR_BG = (30, 30, 30)
COLOR_WHEELCHAIR = (0, 0, 255)

OBSTACLE_HEIGHT = WHEELCHAIR_HEIGHT / 2

# Parameters for collision avoidance & vector drawing (in 2D X-Z plane)
DETECTION_RANGE = 500
SOFT_COLLISION_DIST = 80
FOV_DEG = 60
FOV_RAD = math.radians(FOV_DEG)

# -------------------------
# Utility: AABB collision in 2D (X-Z plane)
# -------------------------
def aabb_collision(ax, az, aw, ad, bx, bz, bw, bd):
    return (abs(ax - bx) * 2 < (aw + bw)) and (abs(az - bz) * 2 < (ad + bd))

# -------------------------
# Ground Drawing (3D)
# -------------------------
def draw_ground():
    glColor3f(COLOR_BG[0]/255.0, COLOR_BG[1]/255.0, COLOR_BG[2]/255.0)
    glBegin(GL_QUADS)
    glVertex3f(-1000, 0, -1000)
    glVertex3f( 1000, 0, -1000)
    glVertex3f( 1000, 0,  1000)
    glVertex3f(-1000, 0,  1000)
    glEnd()



def draw_box(center, size, color, rotation=0, draw_edges=False):
  
    cx, cy, cz = center
    w, h, d = size
    hx, hy, hz = w/2.0, h/2.0, d/2.0
    r, g, b = [c/255.0 for c in color]
    
    #Define the 8 vertices of the box (in local coordinates)
    vertices = [
        (-hx, -hy,  hz),  # 0: front-bottom-left
        ( hx, -hy,  hz),  # 1: front-bottom-right
        ( hx,  hy,  hz),  # 2: front-top-right
        (-hx,  hy,  hz),  # 3: front-top-left
        (-hx, -hy, -hz),  # 4: back-bottom-left
        ( hx, -hy, -hz),  # 5: back-bottom-right
        ( hx,  hy, -hz),  # 6: back-top-right
        (-hx,  hy, -hz)   # 7: back-top-left
    ]
    
    #Define faces (as indices into the vertices list)
    faces = [
        (0, 1, 2, 3),  # front
        (4, 5, 6, 7),  # back
        (0, 4, 7, 3),  # left
        (1, 5, 6, 2),  # right
        (3, 2, 6, 7),  # top
        (0, 1, 5, 4)   # bottom
    ]
    
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(rotation, 0, 1, 0)
    
    #Draw solid faces
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    for face in faces:
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()
    
    #Optionally draw black edges for clarity
    if draw_edges:
        glColor3f(0, 0, 0)  
        glLineWidth(2.0)
        for face in faces:
            glBegin(GL_LINE_LOOP)
            for vertex in face:
                glVertex3fv(vertices[vertex])
            glEnd()
    
    glPopMatrix()


# -------------------------
# Obstacle Definitions
# -------------------------
def get_obstacles():
    obstacles = []
    def rect_to_obstacle(rect, color):
        # Here, rect.x and rect.y represent X and Z in the simulation.
        cx = rect.x + rect.width / 2.0
        cz = rect.y + rect.height / 2.0
        cy = OBSTACLE_HEIGHT / 2.0  # so the box sits on the ground
        size = (rect.width, OBSTACLE_HEIGHT, rect.height)
        return {'center': (cx, cy, cz), 'size': size, 'color': color}
    
    # Top right: "sidewalk"/ramp area
    obs_list = [
        (pygame.Rect(660, 0, 30, 150), (128, 128, 128)),
        (pygame.Rect(750, 0, 30, 150), (128, 128, 128)),
        (pygame.Rect(440, 150, 250, 20), (0, 128, 0)),
        (pygame.Rect(440, 260, 400, 20), (0, 128, 0)),
        (pygame.Rect(750, 150, 100, 20), (0, 128, 0))
    ]
    for rect, color in obs_list:
        obstacles.append(rect_to_obstacle(rect, color))
    
    # Bottom left: Bedroom layout
    obs_list = [
        (pygame.Rect(30, 350, 150, 80), (200, 0, 0)),
        (pygame.Rect(250, 350, 80, 50), (200, 0, 0)),
        (pygame.Rect(30, 500, 40, 40), (200, 0, 0)),
        (pygame.Rect(150, 500, 60, 40), (200, 0, 0))
    ]
    for rect, color in obs_list:
        obstacles.append(rect_to_obstacle(rect, color))
    
    # Walls around environment
    env_left = 0
    env_top = 0
    env_right = 900
    env_bottom = 600
    wall_color = (173, 216, 230)  # light blue
    
    obstacles.append({
        'center': (env_left + 10, OBSTACLE_HEIGHT/2, (env_top + env_bottom)/2),
        'size': (20, OBSTACLE_HEIGHT, env_bottom - env_top),
        'color': wall_color
    })
    obstacles.append({
        'center': (env_right - 10, OBSTACLE_HEIGHT/2, (env_top + env_bottom)/2),
        'size': (20, OBSTACLE_HEIGHT, env_bottom - env_top),
        'color': wall_color
    })
    obstacles.append({
        'center': ((env_left+env_right)/2, OBSTACLE_HEIGHT/2, env_top + 10),
        'size': (env_right - env_left, OBSTACLE_HEIGHT, 20),
        'color': wall_color
    })
    obstacles.append({
        'center': ((env_left+env_right)/2, OBSTACLE_HEIGHT/2, env_bottom - 10),
        'size': (env_right - env_left, OBSTACLE_HEIGHT, 20),
        'color': wall_color
    })
    
    return obstacles

# -------------------------
# Soft Collision Avoidance (2D version applied in X-Z plane)
# -------------------------
def apply_soft_collision_avoidance_3d(pos_x, pos_z, angle, forward_speed, turning_input, obstacles):
    # Effective heading: if moving forward, use current angle; if reverse, use angle+pi.
    if forward_speed >= 0:
        effective_heading = angle
    else:
        effective_heading = (angle + math.pi) % (2*math.pi)
    
    min_dist = None
    best_angle_diff = 0
    for obs in obstacles:
        cx, cy, cz = obs['center']
        w, h, d = obs['size']
        left = cx - w/2
        right = cx + w/2
        top = cz - d/2
        bottom = cz + d/2
        closest_x = max(left, min(pos_x, right))
        closest_z = max(top, min(pos_z, bottom))
        dx = closest_x - pos_x
        dz = closest_z - pos_z
        distance = math.sqrt(dx*dx + dz*dz)
        if distance < 1 or distance > DETECTION_RANGE:
            continue
        global_angle = math.atan2(dz, dx)
        angle_diff = (global_angle - effective_heading + math.pi) % (2*math.pi) - math.pi
        if abs(angle_diff) > FOV_RAD / 2:
            continue
        # Ensure obstacle is "in front" along the effective heading.
        effective_vec = (math.cos(effective_heading), math.sin(effective_heading))
        dot = dx * effective_vec[0] + dz * effective_vec[1]
        if dot < 0:
            continue
        if min_dist is None or distance < min_dist:
            min_dist = distance
            best_angle_diff = angle_diff
    if min_dist is not None and min_dist < SOFT_COLLISION_DIST:
        forward_scale = min_dist / SOFT_COLLISION_DIST
        forward_speed *= forward_scale
        turning_input -= TURNING_SCALE * best_angle_diff
    return forward_speed, turning_input

# -------------------------
# 3D Obstacle Vector Drawing
# -------------------------
def draw_obstacle_vectors_3d(obstacles, pos_x, pos_z, angle):
    """
    Draw yellow lines (using OpenGL) from the wheelchair's center to the
    closest point on each obstacle that is in line of sight.
    """
    wheelchair_y = WHEELCHAIR_HEIGHT / 2
    glColor3f(1.0, 1.0, 0.0)  # Yellow
    glLineWidth(2.0)
    glBegin(GL_LINES)
    for obs in obstacles:
        cx, cy, cz = obs['center']
        w, h, d = obs['size']
        left = cx - w/2
        right = cx + w/2
        top = cz - d/2
        bottom = cz + d/2
        closest_x = max(left, min(pos_x, right))
        closest_z = max(top, min(pos_z, bottom))
        dx = closest_x - pos_x
        dz = closest_z - pos_z
        distance = math.sqrt(dx*dx + dz*dz)
        if distance < 1 or distance > DETECTION_RANGE:
            continue
        global_angle = math.atan2(dz, dx)
        angle_diff = (global_angle - angle + math.pi) % (2*math.pi) - math.pi
        if abs(angle_diff) > FOV_RAD / 2:
            continue
        glVertex3f(pos_x, wheelchair_y, pos_z)
        # For drawing, use the obstacle's vertical center (OBSTACLE_HEIGHT/2)
        glVertex3f(closest_x, OBSTACLE_HEIGHT/2, closest_z)
    glEnd()

# -------------------------
# Main Menu
# -------------------------
def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Wheelchair Simulation")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    
    # Two buttons for control mode selection
    button1 = pygame.Rect(150, 200, 500, 50)
    button2 = pygame.Rect(150, 300, 500, 50)
    
    mode = None
    while mode is None:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if button1.collidepoint(pos):
                    mode = "head"      # Arrow keys + z/x
                elif button2.collidepoint(pos):
                    mode = "head_sip"  # i/l/p/k + z/x
        screen.fill((50, 50, 50))
        title_surface = font.render("Wheelchair Simulation", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
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

# -------------------------
# 3D Simulation
# -------------------------
def simulation(mode):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Wheelchair Simulation")
    
    # Set up perspective projection
    glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, SCREEN_WIDTH/SCREEN_HEIGHT, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glEnable(GL_DEPTH_TEST)
    
    obstacles = get_obstacles()
    
    # Initial wheelchair state (position on X-Z plane and rotation about Y)
    pos_x, pos_z = START_POS
    angle = START_ANGLE
    
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds
        
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        
        # ----- Input Handling -----
        keys = pygame.key.get_pressed()
        forward_speed = 0
        turning_input = 0
        
        if mode == "head":
            if keys[pygame.K_UP]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_DOWN]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_LEFT]:
                turning_input = -TURNING_SCALE
            elif keys[pygame.K_RIGHT]:
                turning_input = TURNING_SCALE
        elif mode == "head_sip":
            if keys[pygame.K_i]:
                forward_speed = SPEED_SCALE
            elif keys[pygame.K_l]:
                forward_speed = -SPEED_SCALE
            if keys[pygame.K_p]:
                turning_input = -TURNING_SCALE
            elif keys[pygame.K_k]:
                turning_input = TURNING_SCALE
        
        # Fine-tuning keys (z, x) add to turning but disable collision avoidance:
        fine_tuning = keys[pygame.K_z] or keys[pygame.K_x]
        if keys[pygame.K_z]:
            turning_input -= FINE_TURN_SCALE
        if keys[pygame.K_x]:
            turning_input += FINE_TURN_SCALE
        
        # ----- Apply Collision Avoidance (if not fine-tuning) -----
        if not fine_tuning:
            forward_speed, turning_input = apply_soft_collision_avoidance_3d(
                pos_x, pos_z, angle, forward_speed, turning_input, obstacles
            )
        
        # Update wheelchair state
        angle += turning_input * dt
        pos_x += forward_speed * math.cos(angle) * dt
        pos_z += forward_speed * math.sin(angle) * dt
        
        # Simple collision detection using AABB in X-Z plane
        for obs in obstacles:
            bx = obs['center'][0]
            bz = obs['center'][2]
            bw = obs['size'][0]
            bd = obs['size'][2]
            if aabb_collision(pos_x, pos_z, WHEELCHAIR_WIDTH, WHEELCHAIR_DEPTH, bx, bz, bw, bd):
                print("Collision detected! Resetting position.")
                pos_x, pos_z = START_POS
                angle = START_ANGLE
                break
        
        # Compute wheelchair center in 3D
        wheelchair_center = (pos_x, WHEELCHAIR_HEIGHT/2, pos_z)
        
        # ----- Set Up Camera -----
        front_face = ( pos_x + math.cos(angle)*(WHEELCHAIR_DEPTH/2),
                       WHEELCHAIR_HEIGHT/2,
                       pos_z + math.sin(angle)*(WHEELCHAIR_DEPTH/2) )
        extra_offset = 10  # extra distance in front of the wheelchair
        camera_pos = ( front_face[0] + math.cos(angle)*extra_offset,
                       front_face[1] + 5,
                       front_face[2] + math.sin(angle)*extra_offset )
        look_at = ( camera_pos[0] + math.cos(angle),
                    camera_pos[1],
                    camera_pos[2] + math.sin(angle) )
        
        glLoadIdentity()
        gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
                  look_at[0], look_at[1], look_at[2],
                  0, 1, 0)
        
        # ----- Drawing -----
        glClearColor(COLOR_BG[0]/255.0, COLOR_BG[1]/255.0, COLOR_BG[2]/255.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        draw_ground()
        for obs in obstacles:
            draw_box(obs['center'], obs['size'], obs['color'], rotation=0, draw_edges=True)
        
        # Draw the moving wheelchair block
        draw_box(wheelchair_center,
                 (WHEELCHAIR_WIDTH, WHEELCHAIR_HEIGHT, WHEELCHAIR_DEPTH),
                 COLOR_WHEELCHAIR,
                 rotation=math.degrees(angle),
                 draw_edges=False)
        
        # Optionally, draw obstacle vectors (yellow lines) for debugging
        draw_obstacle_vectors_3d(obstacles, pos_x, pos_z, angle)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

def main():
    mode = main_menu()  # Show the home screen and choose control mode.
    simulation(mode)    # Run the 3D simulation.

if __name__ == "__main__":
    main()




