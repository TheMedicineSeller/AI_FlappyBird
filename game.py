import pygame
import neat
import random 
import os
import time
pygame.font.init()
# TODO change width window, scale all images
# WIN_WIDTH = 290
# WIN_HEIGHT = 510
WIN_WIDTH = 500
WIN_HEIGHT = 800
GEN = 0
BIRD_IMAGES = [ pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "bluebird1.png"))),
                pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "bluebird2.png"))),
                pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "bluebird3.png"))),
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "pipered.png")))

BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "bgdark.png")))

BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("Sprites", "base.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)
class Bird:
    IMGS = BIRD_IMAGES
    MAX_ROTATION = 25 # IN DEGREES
    ROT_VEL = 20      # FOR THE KICK IN ROTATION WHEN IT FLAPS OR FALLS
    ANIMATION_PERIOD = 5
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]  # References bbird images

    def jump(self):
        self.vel = -10.5  # Negative velocity as when it jumps as pygame window going up is decreasing y coord
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        # displacement since last jump, similar to d = ut + 0.5at^2
        # Here a = 3
        d = self.vel * self.tick_count + 1.5 * self.tick_count**2
        if d >= 16:
            d = 16 # Cannot acclerate beyond a displacement of 16
        if d < 0:
            d -= 2 # making it jump a lil bit more
        self.y += d
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:  # limit 90 degrees
                self.tilt -= self.ROT_VEL

    def draw(self, wind):
        self.img_count += 1
        # Animation period represents the no of frames for which the same image is used, until changed , which is once per 5 frames
        if self.img_count < self.ANIMATION_PERIOD:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_PERIOD * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_PERIOD * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_PERIOD * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_PERIOD * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_PERIOD * 2
        # Rotates image about the origin by theta
        # So we want to rotate it at the centre and hence shift org
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        wind.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    # In the game the pipes move and not the bird
    VEL = 5
    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.TOP_PIPE = pygame.transform.flip(PIPE_IMG, False, True)
        self.BOTTOM_PIPE = PIPE_IMG
        self.passed = False
        # Sets the pipe height randomly
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 540)
        # We define the very top of the toppipe somewhere in the negative y (up) so that bird can't just fly over by defining TOPPIPE.get_height
        # We subtract from height (from y=0), the length of pipe
        self.top = self.height - self.TOP_PIPE.get_height()
        self.bottom = self.height + self.GAP
    
    def move(self):
        self.x -= self.VEL
    
    def draw(self, wind):
        wind.blit(self.TOP_PIPE, (self.x, self.top))
        wind.blit(self.BOTTOM_PIPE, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.TOP_PIPE)
        bottom_mask = pygame.mask.from_surface(self.BOTTOM_PIPE)
        # distances from top pipe's and bottom pipe's left 
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        # Finding the first point where bird collides with the bottom pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        # Finding the first point where bird collides with the top pipe
        t_point = bird_mask.overlap(top_mask, top_offset)

        # Both return NONE when there exists no overlapping point
        if t_point or b_point:
            return True
        else :
            return False

class Base:
    VEL = 5 # same as pipe
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG
    def __init__(self, y):
        self.y = y
        # x1, x2 both ends of the base
        self.x1 = 0
        self.x2 = self.WIDTH
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        # Movement of the base, whenever the first base img goes out of window, first base is made the next base image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, wind):
        # rendering the 2 base images
        wind.blit(self.IMG, (self.x1, self.y))
        wind.blit(self.IMG, (self.x2, self.y))

def draw_window(wind, birds, pipes, base, score, GEN):
    # Blit draws on the pygame screen
    wind.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(wind)
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    wind.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    text = STAT_FONT.render("Gen: " + str(GEN), 1, (255, 255, 255))
    wind.blit(text, (10, 10))
    base.draw(wind)
    for bird in birds:
        bird.draw(wind)
    pygame.display.update()

def main(genomes, config_file):
    global GEN
    GEN += 1
    # So now we are running the game loop for a population of birds instead of a single one, so we need birds[]
    birds = []
    nets = []   # Corresponding neural networks and genomes for each bird
    ge = []
    # We use underscore to consider only the genome object instead of the id as genome is actually a tuple
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config_file)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    # bird = Bird(230, 350) # initial coords passed
    base = Base(730)
    pipes = [Pipe(500)]
    wind = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    run = True
    score = 0
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
        pipe_ind = 0 # Initially we have our distance calculation to the first pipe in the list
        if len(birds) > 0:
            # Until When on the screen there exist more than one pipe, then we shift our focus to the next pipe in list if we cross the first pipe
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].TOP_PIPE.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1  # Encourages the bird to stay alive by giving tiny fitness boost
            # 3 inputs to the NN, the y pos of Bird, distance to the top pipe and distance to the bottom pipe
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            # Activation function, greater than 0.5 => jumps
            if output[0] > 0.5:
                bird.jump()
        add_pipe = False
        to_remove = []
        # bird.play_step()
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # Reduce fitness of birds which collided and remove them
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
            # When the pipe vanishes out of the screen, append it to remove list
            if pipe.x + pipe.TOP_PIPE.get_width() < 0:
                to_remove.append(pipe)
            pipe.move()
        if add_pipe:
            # Any surviving bird that passes the pipe gets its fitness boosted
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(500))
        # Dispose passed pipes
        for r in to_remove:
            pipes.remove(r)
        # When any Bird hits the floor or jumps above the render screen, remove it and its genomes
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)
        base.move()
        draw_window(wind, birds, pipes, base, score, GEN)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    popu = neat.Population(config)
    popu.add_reporter(neat.StdOutReporter(True))  # Gives us some live statistics
    stats = neat.StatisticsReporter()
    popu.add_reporter(stats)

    winner = popu.run(main, 50)      # Running the population for 50 runs on given fitness function
    # Here we run the main() only for determining fitness, so makes sense it is passed as the fitness function
# Start prog by calling main
# main()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "Neat-config.txt")
    run(config_path)