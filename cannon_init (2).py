''' Cannon game: First Assignment 1 for Scientific Computing at Roskilde University

 Program functionality description:

     The following program displays a (2000m broad and 1000m high) field with two cannons, a white one with 20m wide, 90m high
     positioned 200m from the left side of the field and a red one with the same measures positioned 280m from the left side.
     The scaling factor is 0.5, thus the window is 1000 pixels x 500 pixels.

     Both having a barrel representing the projectile's initial velocity of approximately with --> (84.85, 84.85) m/s.
     Everytime we press space key the cannon will fire projectiles (from the center of the cannon) starting with the
     initial velocity. The projectiles are affected by gravity and drag due to wind. When a projectile exits the field,
     it is repositioned to the center of the cannon and refired. The game allows for 5 rounds, alternating
     turns between the two players, and incorporates random wind effects to influence the projectile's trajectory.

Program controls:
    Press Esc to quit,
          g to show/hide grid

  Authors: Maja H Kirkeby & Ulf R. Pedersen

  !!! Remember to update the program description for your version !!!

'''

# Import modules
import pygame
import sys
import random #import module Random to generate a random number between -15 and 15.
import math

# Initialize pygame
pygame.init()

left = 1 #integer value representing left click

# Define colors
BLACK = 0, 0, 0
WHITE = 255, 255, 255
BLUE = 0, 0, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
LIGHTBLUE = 173, 216, 230

# Define a frame rate
frames_per_second = 60

# Initialize real world parameters
g = 9.8   # Gravitational acceleration (m/s**2)
mass = 1  # Mass of projectile (kg)
D = 0.1 #Coefficient of friction

# Set parameters for time
speedup = 8    # in order to reduce waiting time for impact we speed up by increasing the timestep
t = 0.0        # time in seconds
dt = (1 / frames_per_second)*speedup  # time increment in seconds

width = 2000.0   # Position of wall to the right and width of the coordinate system
height = 1000.0  # Height of the coordinate system
x_grid = 100 # the interval of x-axis grid of the coordinate system
y_grid = 100  # the interval of y-axis grid of the coordinate system

scale_real_to_screen = 0.5 # scale from the real-world to the screen-coordinate system

def convert(real_world_x, real_world_y, scale=scale_real_to_screen, real_world_height=height):
    ''' conversion from real-world coordinates to pixel-coordinates '''
    return int(real_world_x*scale), int((real_world_height-real_world_y)*scale-1)


def convert_back(mouse_x, mouse_y, scale=scale_real_to_screen, real_world_height=height):
    ''' conversion from pixel-coordinates to real-world coordinates '''
    return mouse_x/scale, real_world_height - mouse_y/scale
# initialize real world cannon(s):
# ================================
# The values for the cannon is kept in a dictionary called cannon1. The correctness of some of the functions depend
# on the cannon to have the specified keys defined (you can add other key-value pairs). The intention is that you
# can create extra cannons, i.e., dictionaries with the same keys and different values, and add those to the
# players-list.
# 315.0 m/s Cannonball, e.g., https://www.arc.id.au/CannonBallistics.html
# 120 m/s small gun https://en.wikipedia.org/w/index.php?title=Muzzle_velocity&oldid=970936654

cannon_width, cannon_height = 40, 90
cannon1 = {"x": 200,
           "y": 0+cannon_height,
           "vx": 84.85,  # ≈ 120 m/s angle 45
           "vy": 84.85,  # ≈ 120 m/s angle 45
           "width": cannon_width,
           "height": cannon_height,
           "color": WHITE,
           'ball_radius': 10,  # radius in meters
           "score": 0,
           "power": 0,
           "angle_vector": {"x": 0, "y": 0}
            }
cannon2 = {"x": 280,
           "y": 0+cannon_height,
           "vx": 84.85,  # ≈ 120 m/s angle 45
           "vy": 84.85,  # ≈ 120 m/s angle 45
           "width": cannon_width,
           "height": cannon_height,
           "color": RED,
           'ball_radius': 10,  # radius in meters
           "score": 0, # I was about to use it for the score table. Each time it reaches the target, I add 1
           "power": 0,
            "angle_vector": {"x": 0, "y": 0}
            }

# list of players
players = [cannon1, cannon2]

def calc_init_ball_pos(cannon):
    ''' Finds the center of the cannon '''
    return cannon['x'] + cannon['width']/2, cannon['y'] - cannon['height']/2

def draw_cannon(surface, cannon):
    ''' Draw the cannon (the barrel will be the length of the initial velocity of the ball '''
    rect = (
        convert(cannon['x'], cannon['y']),
        (cannon['width']*scale_real_to_screen, cannon['height']*scale_real_to_screen)
    )
    pygame.draw.rect(surface, cannon['color'], rect)
    cannon_center = calc_init_ball_pos(cannon)
    line_from = convert(cannon_center[0], cannon_center[1])
    line_to = convert(cannon_center[0]+cannon['vx']*scale_real_to_screen, cannon_center[1]+cannon['vy']*scale_real_to_screen)
    line_width = 2
    pygame.draw.line(surface, cannon['color'], line_from, line_to, line_width)

def is_inside_field(real_world_x, real_world_y, field_width=width):
    ''' Return true if input is within world '''
    # Note: there is no ceiling
    return 0 < real_world_x < field_width and real_world_y > 0

# Create PyGame screen:
# 1. specify screen size
screen_width, screen_height = int(width*scale_real_to_screen), int(height*scale_real_to_screen)
# 2. define screen
screen = pygame.display.set_mode((screen_width, screen_height))
# 3. set caption
pygame.display.set_caption("Cannon Game")

# Update pygames clock use the framerate
clock = pygame.time.Clock()


def draw_grid(surface, color, real_x_grid, real_y_grid, real_width=width, real_height=height):
    ''' Draw real-world grid on screen '''
    # vertical lines
    for i in range(int(real_width / real_x_grid)):
        pygame.draw.line(surface, color, convert(i * real_x_grid, 0),  convert(i * real_x_grid, real_height))
    # horizontal lines
    for i in range(int(real_height / y_grid)):
        pygame.draw.line(surface, color, convert(0 , i * real_y_grid ), convert(real_width, i * real_y_grid))

# Initialize game loop variables
running = True
shooting = False
show_grid = False
turn = 0
countRounds = 0
maxRounds = 5

#target values
x_target, y_target = 800, 450
target_radius = 20

#Initialize the wind variable
vwind =  random.randint(-15, 15)

print(f"Wind velocity for player {turn + 1}: {vwind} m/s in x direction")


# Initialize projectile values (see also function below)
x, y = calc_init_ball_pos(players[turn])

vx = players[turn]['vx']  # x velocity in meters per second
vy = players[turn]['vy']  # y velocity in meters per second

ball_color = players[turn]['color']
ball_radius = players[turn]['ball_radius']

#Applied the wind for the first shot
vx = vx + vwind

def drawArrow(screen, color ,vwind):
    start_pos = (500, 30)  # Position where the arrow starts, I chose to put it in the middle of my screen.

    # Takes the position "0" which is the value of X (500), then I convert
    # into int the value of wind times 10. I put times ten for a better view
    # because if I delete de multiplication and I leave only int(vwind), the
    # the wind changes would be almost impossible to see due to the small number.
    end_pos = (start_pos[0] + vwind*10, start_pos[1])
    # then I write a line with sending the values of screen,the color,
    # the start position and the end position, and finally i assign a width.
    pygame.draw.line(screen, color, start_pos, end_pos, 2)
    #Arrowhead

    # if wind direction is going to the right, draw right arrow
    if vwind > 0:
        pygame.draw.polygon(screen, color,
                [(end_pos[0], end_pos[1]), (end_pos[0] - 10, end_pos[1] - 10), (end_pos[0] - 10, end_pos[1] + 10)])
    # else draw left arrow
    else:
        pygame.draw.polygon(screen, color,
                            [(end_pos[0]-10, end_pos[1]), (end_pos[0], end_pos[1] - 10),
                             (end_pos[0], end_pos[1] + 10)])

def change_player():
    ''' Initialize the global variables of the projectile to be those of the players cannon '''
    global players, turn, x, y, vx, vy, ball_color, ball_radius, countRounds, vwind
    # Technical comment concerning the "global" (can be deleted):
    #   we need to tell the program that we want to update the global variables. If we did not, the program would instead
    #   think that we are working with some other variables with the same name.s

    turn = (turn + 1) % len(players)
    # players[turn] == cannon1
    # players[turn]['color'] == WHITE

    # This verifies if current turn become zero.
    # meaning that all players has played. So one ROUND is passed.
    if turn == 0:
        countRounds += 1
        print(f"Round {countRounds} completed")  # this print in the console how it's going in terms of rounds completed.

    # verifies if the max round is reach
    if countRounds >= maxRounds:
        print("Game over! 5 rounds completed.")
        print("The winner is ...")
        if players[0]['score'] > players[1]['score']:
            print("Player 1 with a score of", players[0]['score'])
        elif players[0]['score'] < players[1]['score']:
            print("Player 2 with a score of", players[1]['score'])
        else:
            print("It's a draw!", players[0]['score'], " - ", players[1]['score'])
        pygame.quit()  # Close pygame
        sys.exit()

    # Generating the random integer number within -15 and 15.
    vwind = (random.randint(-15, 15))
    print (f"Wind velocity for player {turn + 1}: {vwind} m/s in x direction")

    x, y = calc_init_ball_pos(players[turn])
    #Adding the random wind (vwind) to x-velocity (horizontal velocity)
    #vx has now the wind force

    vx, vy = players[turn]['vx'], players[turn]['vy']
    ball_color = players[turn]['color']
    ball_radius = players[turn]['ball_radius']

def drawBall():
    pygame.draw.circle(screen, ball_color, (x_pix, y_pix), ball_radius_pix)

def Target():
    return pygame.draw.circle(screen, GREEN, (x_target, y_target), target_radius)


# SOME MAXIMUM VALUES FOR THE POWER
max_power = 200
power_color = [200, 255, 25]

def draw_power_arrow(screen, player):
    final_color = power_color.copy()
    start_pos = convert(player["x"] + player["width"] / 2, player["y"] - player["height"] / 2)
    end_pos = (
        start_pos[0] + int(player["angle_vector"]["x"] * player["power"]),
        start_pos[1] - int(player["angle_vector"]["y"] * player["power"])
    )
    pygame.draw.line(screen, final_color, start_pos, end_pos, 2)



# Game loop:
while running:

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == left or event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            shooting = True
            #little animation in the cannon
            players[turn]['y'] = cannon_height - 15
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_g:
            show_grid = not show_grid
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            player_x, player_y = calc_init_ball_pos(players[turn])

            mouse_real_x, mouse_real_y = convert_back(mouse_x, mouse_y)

            dis_x = mouse_real_x - player_x
            dis_y = mouse_real_y - player_y

            dis_x, dis_y = dis_x * scale_real_to_screen, dis_y * scale_real_to_screen

            # I calculate the normalized distance between the mouse and the cannon
            magnitude = math.sqrt(dis_x**2 + dis_y**2)
            players[turn]["angle_vector"]["x"] = dis_x / magnitude
            players[turn]["angle_vector"]["y"] = dis_y / magnitude

            #print(f"Angle Vector: {players[turn]['angle_vector']}")

            players[turn]["power"] = min(magnitude, max_power)
            #print(f"power: {players[turn]['power']}")

            players[turn]["vx"] = players[turn]["angle_vector"]["x"] * players[turn]["power"]
            players[turn]["vy"] = players[turn]["angle_vector"]["y"] * players[turn]["power"]

    #drawArrow(screen, players[turn]['color'], vwind)

    # Check whether the ball is outside the field
    if not is_inside_field(x,y):
        players[turn]['y'] = cannon_height
        change_player() # if there is only one player, the ball will restart at that players center
        shooting = False

    # Game logic
    # draw a background using screen.fll()
    screen.fill(BLACK)

    # draw grid
    if show_grid:
        draw_grid(screen, RED, x_grid, y_grid, width, height)

    # I draw the arrow, sending screen values, the color of the cannon playing, and the value of wind.
    drawArrow(screen, players[turn]['color'], vwind)

    # draw the player's cannon
    draw_cannon(screen, cannon1)
    draw_cannon(screen, cannon2)


    #circle target
    Target()

    #I got the color from the cannon who is playing
    #drawArrow(screen, players[turn]['color'], vwind)

    # convert the real-world coordinates to pixel-coordinates
    x_pix, y_pix = convert(x, y)
    ball_radius_pix = round(scale_real_to_screen * ball_radius)

    # draw ball using the pixel coordinates
    drawBall()

    # print time passed, position and velocity
    #print(f"time: {t}, pos: ({x,y}), vel: ({vx,vy}, pixel pos:({x_pix},{y_pix}))")

    if shooting:

        # update time passed, the projectile 's real-world acceleration, velocity,
        # position for the next time_step using the Leap-Frog algorithm

        # At the beginning the only force applied was gravity, in the negative direction of Y, but now
        # we have the drag force which goes in the opposite direction.

        # Fx = 0 --> i don't need to initialize this variable with zero anymore
        # now Fx has a value that depends on the new velocity with the drag applied

        Fy_gravity = -mass * g

        # Drag force in x and y.
        # the minus in "-D", which is the resistance force, means that the force is going opposite to the horizontal movement.(x)
        dragFx = -D * (vx - vwind)
        dragFy= -D * vy  # Here the same, but opposite to the VERTICAL movement.(y)

        # calculations of all the forces that act over the gun.
        Fx = dragFx
        Fy = Fy_gravity + dragFy

        # Now besides the gravity, the gun will have to lead with a new resistence each time it goes further.
        # in x(horizontal), and y (vertical), which cause a gradual decrease in both directions
        # due to wind (drag force).

        # Compute acceleration, but now the force has the drag
        ax = Fx/mass
        ay = Fy/mass

        # Update velocities from acceleration
        vx = vx + ax*dt
        vy = vy + ay*dt

        # Update positions from velocities
        x = x + vx * dt
        y = y + vy * dt

        # real world to pixel coordinates
        x_pix, y_pix = convert(x, y)

        if y_target - target_radius < y_pix < y_target + target_radius and x_target - target_radius < x_pix < x_target + target_radius:
            players[turn]['score'] += 1
            print(f"Player {turn + 1} hit the target! Score: {players[turn]['score']}")
            change_player()
            shooting = False

    else:
        vx = players[turn]['vx']
        vy = players[turn]['vy']
        draw_power_arrow(screen, players[turn])

    # Redraw the screen
    pygame.display.flip()

    # Limit the framerate (must be called in each iteration)
    clock.tick(frames_per_second)

# Close after the game loop
pygame.quit()
sys.exit()
