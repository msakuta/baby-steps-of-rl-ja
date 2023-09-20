from copy import deepcopy
from typing import List, Tuple
import pygame
from pygame.locals import *
import numpy as np

file = 'back2_32.png'
agent_file = "raccoon.png"
crate_file = "crate.png"
image = pygame.image.load(file)
rect = image.get_rect()
print(image)

class Tileset:
    def __init__(self, file, size=(32, 32), margin=1, spacing=1):
        self.file = file
        self.size = size
        self.margin = margin
        self.spacing = spacing
        self.image = pygame.image.load(file)
        self.rect = self.image.get_rect()
        self.tiles = []
        self.load()


    def load(self):

        self.tiles = []
        x0 = y0 = self.margin
        w, h = self.rect.size
        dx = self.size[0] + self.spacing
        dy = self.size[1] + self.spacing
        
        for x in range(x0, w, dx):
            for y in range(y0, h, dy):
                tile = pygame.Surface(self.size)
                tile.blit(self.image, (0, 0), (x, y, *self.size))
                self.tiles.append(tile)

    def __str__(self):
        return f'{self.__class__.__name__} file:{self.file} tile:{self.size}'

class Tilemap:
    def __init__(self, tileset: Tileset, size=(10, 20), rect=None, scale=1):
        self.size = size
        self.tileset = tileset
        self.scale = scale
        self.map = np.zeros(size, dtype=int)

        h, w = self.size
        self.image = pygame.Surface((32*w*scale, 32*h*scale))
        if rect:
            self.rect = pygame.Rect(rect)
        else:
            self.rect = self.image.get_rect()

    def render(self):
        m, n = self.map.shape
        for i in range(m):
            for j in range(n):
                tile = self.tileset.tiles[self.map[i, j]]
                scaled_tile = pygame.transform.scale(tile, (32*self.scale, 32*self.scale)) if self.scale != 1 else tile
                self.image.blit(scaled_tile,
                                (j*32*self.scale, i*32*self.scale))

    def set_zero(self):
        self.map = np.zeros(self.size, dtype=int)
        print(self.map)
        print(self.map.shape)
        self.render()

    def set_random(self, choices=None, border=None):
        if choices is None:
            n = len(self.tileset.tiles)
            self.map = np.random.randint(n, size=self.size)
        else:
            self.map = np.asarray(choices)[np.random.randint(len(choices), size=self.size)]
        if border is not None:
            self.map[:,0] = border
            self.map[:,-1] = border
            self.map[0,:] = border
            self.map[-1,:] = border
        print(f"map: {self.map}")
        self.render()

    def __str__(self):
        return f'{self.__class__.__name__} {self.size}'

class Direction:
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3

class Game:
    W = 640
    H = 480
    SIZE = W, H
    CELLW = 32
    CELLH = 32
    SCALE = 2

    def __init__(self):
        pygame.init()
        self.tileset = Tileset(file, margin=0, spacing=0)
        self.tileset.load()
        self.tilemap = Tilemap(self.tileset, (
            self.H // self.CELLH // self.SCALE,
            self.W // self.CELLW // self.SCALE
        ), scale=2)
        self.agent = [0, 0]
        self.agent_image = pygame.image.load(agent_file)
        self.crates = []
        self.crate_image = pygame.transform.scale(pygame.image.load(crate_file), (self.CELLW * self.SCALE, self.CELLH * self.SCALE))
        self.screen = pygame.display.set_mode(Game.SIZE)
        pygame.display.set_caption("Pygame Tiled Demo")
        self.init_state()
        self.running = True

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False

                elif event.type == KEYDOWN:
                    if event.key == K_l:
                        self.load_image(file)
                    if event.key == K_i:
                        self.init_state()
                    if event.key == K_r:
                        self.random_image()
                    if event.key == K_z:
                        self.zero_image()
                    elif event.key == K_LEFT:
                        self._try_move(Direction.LEFT)
                    elif event.key == K_RIGHT:
                        self._try_move(Direction.RIGHT)
                    elif event.key == K_UP:
                        self._try_move(Direction.UP)
                    elif event.key == K_DOWN:
                        self._try_move(Direction.DOWN)
        pygame.quit()

    def render(self):
        self.screen.blit(self.tilemap.image, self.tilemap.image.get_rect())
        for crate in self.crates:
            self.screen.blit(self.crate_image, (crate[0] * self.CELLW * self.SCALE, crate[1] * self.CELLH * self.SCALE))
        self.screen.blit(self.agent_image, (self.agent[0] * self.CELLW * self.SCALE, self.agent[1] * self.CELLH * self.SCALE))
        pygame.display.update()

    def _try_move(self, direction: int):
        directions = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        direc = directions[direction]
        pos = [self.agent[0] + direc[0], self.agent[1] + direc[1]]
        if self.tilemap.map[pos[1], pos[0]] == 0:
            agent_pos = deepcopy(pos)
            crates = [deepcopy(crate) for crate in enumerate(self.crates)]
            moved_crates = []
            bad = False
            while True:
                hit_crate = self._check_crates(crates, pos)
                if hit_crate is not None:
                    print(f"hit_crate: {hit_crate}")
                    orgi, crate = crates[hit_crate]
                    crate[0] += direc[0]
                    crate[1] += direc[1]
                    if self.tilemap.map[crate[1], crate[0]] != 0:
                        bad = True
                        break
                    pos = crate
                    moved_crates.append((orgi, crate))
                    crates = crates[:hit_crate] + crates[hit_crate+1:]
                else:
                    break
            if not bad:
                self.agent = agent_pos
                for orgi, crate in moved_crates:
                    print(f"replacing crate {self.crates[orgi]} with {crate}")
                    self.crates[orgi] = crate
                self.render()
    
    def _check_crates(self, crates: List[Tuple[int, List[int]]], pos):
        for i, (_, crate) in enumerate(crates):
            if crate == pos:
                return i
        return None

    def load_image(self, file):
        self.file = file
        self.image = pygame.image.load(file)
        self.rect = self.image.get_rect()

        self.screen = pygame.display.set_mode(self.rect.size)
        pygame.display.set_caption(f'size:{self.rect.size}')
        self.screen.blit(self.image, self.rect)
        pygame.display.update()

    def init_state(self):
        self.tilemap.set_random(choices=[0, 2], border=2)
        while self.tilemap.map[self.agent[1], self.agent[0]] != 0:
            self.agent = [np.random.randint(self.tilemap.size[1]), np.random.randint(self.tilemap.size[0])]
        print(f"Agent: {self.agent}")
        self.crates = []
        for _ in range(5):
            for _ in range(20):
                pos = [np.random.randint(self.tilemap.size[1]), np.random.randint(self.tilemap.size[0])]
                if self.tilemap.map[pos[1], pos[0]] != 0:
                    continue
                if pos == self.agent:
                    continue
                if any([pos == crate for crate in self.crates]):
                    continue
                break
            self.crates.append(pos) 

        self.tilemap.render()
        self.render()

    def random_image(self):
        self.tilemap.set_random()
        self.tilemap.render()
        self.screen.blit(self.tilemap.image, self.tilemap.image.get_rect())
        pygame.display.update()

    def zero_image(self):
        self.tilemap.set_zero()
        self.tilemap.render()
        self.screen.blit(self.tilemap.image, self.tilemap.image.get_rect())
        pygame.display.update()

game = Game()
game.run()
