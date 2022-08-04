import pygame, sys, copy
from pygame.locals import *
from numpy.random import permutation

PLAYSPEED = 14
BLOCK_FALL = pygame.USEREVENT

CELLSIZE = 30
BOARDWIDTH = 12
BOARDHEIGHT = 22
PANELWIDTH = 8
WINDOWWIDTH =  CELLSIZE * (BOARDWIDTH + PANELWIDTH)
WINDOWHEIGHT = CELLSIZE * BOARDHEIGHT
NEWPIECEX = BOARDWIDTH // 2 - .5
NEWPIECEY = 2.5
NEXTTEXTX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
NEXTTEXTY = 11 * CELLSIZE
NEXTPIECEX = BOARDWIDTH + PANELWIDTH // 2
NEXTPIECEY = 14
SCORETEXTX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
SCORETEXTY = 3 * CELLSIZE
SCOREX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
SCOREY = 5 * CELLSIZE
LINETEXTX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
LINETEXTY = 7 * CELLSIZE
LINEX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
LINEY = 9 * CELLSIZE
LEVELTEXTX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
LEVELTEXTY = 17 * CELLSIZE
LEVELX = (BOARDWIDTH + PANELWIDTH // 2) * CELLSIZE
LEVELY = 19 * CELLSIZE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
FONTSIZE = 32
TEXTCOLOUR = YELLOW

LEFT = (-1, 0)
RIGHT = (1, 0)
DOWN = (0, 1)
UP = (0, -1)
STOP = (0, 0)
CW = 1
CCW = -1

I = 'I'
J = 'J'
L = 'L'
O = 'O'
S = 'S'
T = 'T'
Z = 'Z'

BAG = [I, J, L, O, S, T, Z]
STATES = ['0', 'R', '2', 'L']
LINESCORE = [100, 300, 500, 800]

'''
colour: name of the tileset
centre: spawn coordinates of the centre of rotation
coords: spawn coordinates of the top left corner of the blocks wrt the centre
offset: index of the offset table to use (see below)
'''
DATA = {
    'I': {
        'colour': 'cyan',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX - .5, NEXTPIECEY),
        'coords': [(-1.5, -.5), (-.5, -.5), (.5, -.5), (1.5, -.5)],
        'offset': 1,
    },
    'J': {
        'colour': 'blue',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX, NEXTPIECEY),
        'coords': [(-1.5, -1.5), (-1.5, -.5), (-.5, -.5), (.5, -.5)],
        'offset': 0,
    },
    'L': {
        'colour': 'orange',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX, NEXTPIECEY),
        'coords': [(-1.5, -.5), (-.5, -.5), (.5, -.5), (.5, -1.5)],
        'offset': 0,
    },
    'O': {
        'colour': 'yellow',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX - .5, NEXTPIECEY),
        'coords': [(-.5, -.5), (-.5, -1.5), (.5, -.5), (.5, -1.5)],
        'offset': 2,
    },
    'S': {
        'colour': 'green',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX, NEXTPIECEY),
        'coords': [(-1.5, -.5), (-.5, -.5), (-.5, -1.5), (.5, -1.5)],
        'offset': 0,
    },
    'T': {
        'colour': 'magenta',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX, NEXTPIECEY),
        'coords': [(-1.5, -.5), (-.5, -.5), (-.5, -1.5), (.5, -.5)],
        'offset': 0,
    },
    'Z': {
        'colour': 'red',
        'centre': (NEWPIECEX, NEWPIECEY),
        'next': (NEXTPIECEX, NEXTPIECEY),
        'coords': [(-1.5, -1.5), (-.5, -1.5), (-.5, -.5), (.5, -.5)],
        'offset': 0,
    },
}

OFFSETS = [
    {
        '0': [(0, 0)] * 5,
        'R': [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        '2': [(0, 0)] * 5,
        'L': [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
    },
    {
        '0': [(0, 0), (-1, 0), (2, 0), (-1, 0), (2, 0)],
        'R': [(-1, 0), (0, 0), (0, 0), (0, -1), (0, 2)],
        '2': [(-1, -1), (1, -1), (-2, -1), (1, 0), (-2, 0)],
        'L': [(0, -1), (0, -1), (0, -1), (0, 1), (0, -2)],
    },
    {
        '0': [(0, 0)],
        'R': [(0, 1)],
        '2': [(-1, 1)],
        'L': [(-1, 0)],
    },
]

coordSum = lambda t1, t2: tuple(map(sum, zip(t1, t2)))
coordSub = lambda t1, t2: tuple(x1 - x2 for (x1, x2) in zip(t1, t2))
coordRotate = lambda c, r: (r * c[1], r * -c[0])

class Piece:
    def __init__(self, shape = I, centre = 'default'):
        self.shape = shape
        self.centre = self.startCentre(shape, centre)
        self.blocks = self.startBlocks(shape)
        self.state = 0
        self.locked = False

    def startCentre(self, shape, centre):
        if centre == 'default':
            return DATA[shape]['centre']
        if centre == 'next':
            return DATA[shape]['next']
    
    def startBlocks(self, shape):
        return [coordSum(self.centre, c) for c in DATA[shape]['coords']]

    def move(self, direction = STOP):
        self.centre = coordSum(self.centre, direction)
        self.blocks = [coordSum(c, direction) for c in self.blocks]

    def rotate(self, rotation = 1, offset = (0, 0)):
        self.blocks = [coordSum(coordSum(coordSum(self.centre, coordRotate(coordSub(self.centre, coordSum(c, (.5, .5))), rotation)), (-.5, -.5)), offset) for c in self.blocks]
        self.centre = coordSum(self.centre, offset)
        self.state = (self.state + rotation) % 4
    
    def fall(self):
        self.centre = coordSum(self.centre, DOWN)
        self.blocks = [coordSum(c, DOWN) for c in self.blocks]

    def draw(self):
        pass

TOGGLE_AUDIO = True
TOGGLE_GHOST = True
MUSIC_VOLUME = 0.5
SOUND_VOLUME = 0.5

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Tetris')
        pygame.mixer.init()
        pygame.mixer.music.load('Sounds\Tetris_theme.ogg')
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        self.soundLineClear = self.loadSound('LineClear.ogg')
        self.soundLevelUp = self.loadSound('LevelUp.ogg')
        self.soundGameOver = self.loadSound('GameOver.ogg')
        self.mainClock = pygame.time.Clock()
        self.colourCache = {}
        self.surface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
        self.textFont = pygame.font.SysFont(None, FONTSIZE)
        self.nextText = self.createText('Next:', NEXTTEXTX, NEXTTEXTY)
        self.scoreText = self.createText('Score:', SCORETEXTX, SCORETEXTY)
        self.lineText = self.createText('Lines:', LINETEXTX, LINETEXTY)
        self.levelText = self.createText('Level:', LEVELTEXTX, LEVELTEXTY)
        self.newGame()

    def newGame(self):
        self.gameOver = False
        self.bag = permutation(BAG).tolist()
        self.piece = None
        self.board = {(x, y): 'grey' for x in range(BOARDWIDTH) for y in range(BOARDHEIGHT) if x == 0 or x == BOARDWIDTH - 1 or y == 0 or y == BOARDHEIGHT - 1}
        self.rotation = None
        self.hardDrop = False
        self.direction = STOP
        self.ghostPiece = None
        self.pause = False
        self.score = 0
        self.lines = 0
        self.level = 1
        self.combo = -1
        self.updateSpeed()
        self.playBGMusic()

    def getColour(self, key):
        if not key in self.colourCache:
            self.colourCache[key] = pygame.transform.scale(pygame.image.load(f"Tileset\{key}.png").convert(), (CELLSIZE, CELLSIZE))
        return self.colourCache[key]

    def createText(self, text, x, y):
        newText = self.textFont.render(text, 0, TEXTCOLOUR)
        newTextRect = newText.get_rect()
        newTextRect.centerx = x
        newTextRect.centery = y
        return newText, newTextRect

    def loadSound(self, sound):
        global SOUND_VOLUME
        newSound = pygame.mixer.Sound(f"Sounds\{sound}")
        newSound.set_volume(SOUND_VOLUME)
        return newSound

    def playSound(self, sound):
        pygame.mixer.Sound.play(sound)

    def playBGMusic(self):
        pygame.mixer.music.rewind()
        if TOGGLE_AUDIO:
            pygame.mixer.music.play(-1)
    
    def toggleBGMusic(self):
        global TOGGLE_AUDIO
        TOGGLE_AUDIO = not TOGGLE_AUDIO
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()

    def boardRender(self):
        global TOGGLE_GHOST
        self.surface.fill(BLACK)
        for tile, colour in self.board.items():
            self.surface.blit(self.getColour(colour), (tile[0] * CELLSIZE, tile[1] * CELLSIZE))
        #Draw ghost piece
        if TOGGLE_GHOST and self.ghostPiece.blocks != self.piece.blocks:
            for c in self.ghostPiece.blocks:
                self.surface.blit(self.getColour(f"{DATA[self.piece.shape]['colour']}_ghost"), (c[0] * CELLSIZE, c[1] * CELLSIZE))
        #Draw player piece
        for c in self.piece.blocks:
            self.surface.blit(self.getColour(DATA[self.piece.shape]['colour']), (c[0] * CELLSIZE, c[1] * CELLSIZE))
        #Draw next piece
        for c in self.nextPiece.blocks:
            self.surface.blit(self.getColour(DATA[self.nextPiece.shape]['colour']), (c[0] * CELLSIZE, c[1] * CELLSIZE))
        #Draw extra text
        self.surface.blit(self.nextText[0], self.nextText[1])
        self.surface.blit(self.scoreText[0], self.scoreText[1])
        self.surface.blit(self.lineText[0], self.lineText[1])
        self.surface.blit(self.levelText[0], self.levelText[1])
        scoreNum = self.createText(f"{self.score}", SCOREX, SCOREY)
        self.surface.blit(scoreNum[0], scoreNum[1])
        lineNum = self.createText(f"{self.lines}", LINEX, LINEY)
        self.surface.blit(lineNum[0], lineNum[1])
        levelNum = self.createText(f"{self.level}", LEVELX, LEVELY)
        self.surface.blit(levelNum[0], levelNum[1])
    
    def toggleGameOver(self):
        self.gameOver = True
        pygame.mixer.music.stop()
        if TOGGLE_AUDIO:
            #pygame.mixer.Sound.play(self.soundGameOver)
            self.playSound(self.soundGameOver)

    def toggleReset(self):
        self.newGame()

    def toggleGhostPiece(self):
        global TOGGLE_GHOST
        TOGGLE_GHOST = not TOGGLE_GHOST
        if not TOGGLE_GHOST:
            self.ghostPiece = None

    def togglePause(self):
        self.pause = not self.pause
        self.toggleBGMusic()

    def computeGhost(self):
        self.ghostPiece = copy.deepcopy(self.piece)
        self.hardDropCells = 0
        while all(c not in self.board for c in self.ghostPiece.blocks):
            self.ghostPiece.move(DOWN)
            self.hardDropCells += 1
        if self.ghostPiece.blocks != self.piece.blocks:
            self.ghostPiece.move(UP)
            self.hardDropCells -= 1
    
    def updateSpeed(self):
        self.fallTimer = int(1000 * (0.8 - ((self.level - 1) * 0.007)) ** (self.level - 1))
        pygame.time.set_timer(BLOCK_FALL, self.fallTimer)

    def consolidatePiece(self):
        if self.piece:
            #Add the piece to the board
            for c in self.piece.blocks:
                self.board[c] = DATA[self.piece.shape]['colour']
            self.piece.locked = True
            #Check for full lines, and update the board accordingly
            newLines = 0
            for y in range(1, BOARDHEIGHT - 1):
                if all((x, y) in self.board for x in range(1, BOARDWIDTH - 1)):
                    newLines += 1
                    for x in range(1, BOARDWIDTH - 1):
                        del self.board[(x,y)]
                    for c in sorted([k for k in self.board if 0 < k[0] < BOARDWIDTH - 1 and 0 < k[1] < y], reverse = True):
                        self.board[(c[0], c[1] + 1)] = self.board[c]
                        del self.board[c]
            if newLines > 0:
                self.lines += newLines
                newLevel = 1 + self.lines // 10
                if newLevel > self.level:
                    if TOGGLE_AUDIO:
                        self.playSound(self.soundLevelUp)
                    self.level = newLevel
                    self.updateSpeed()
                else:
                    if TOGGLE_AUDIO:
                        self.playSound(self.soundLineClear)
                self.score += LINESCORE[newLines - 1] * self.level
                self.combo += 1
                if self.combo > 0:
                    self.score += 50 * self.combo * self.level
            else:
                self.combo = -1
            self.score += self.softDropCells

    def gravity(self):
        if all(coordSum(c, DOWN) not in self.board for c in self.piece.blocks):
            self.piece.fall()
        else:
            self.consolidatePiece()

    def play(self):
        global TOGGLE_GHOST
        if not self.piece or self.piece.locked:
            self.piece = Piece(self.bag.pop())
            self.softDropCells = 0
            if any(c in self.board for c in self.piece.blocks):
                self.toggleGameOver()
        
        if not self.gameOver:
            if not self.bag:
                self.bag = permutation(BAG).tolist()
            self.nextPiece = Piece(self.bag[-1], 'next')

            #Execute player input
            if not self.piece.locked:
                if self.hardDrop:
                    self.computeGhost()
                    self.piece = copy.deepcopy(self.ghostPiece)
                    self.hardDrop = False
                    self.consolidatePiece()
                    self.score += 2 * self.hardDropCells
                else:
                    if self.rotation:
                        for offset in [coordSub(a, b) for a, b in zip(OFFSETS[DATA[self.piece.shape]['offset']][STATES[self.piece.state]], OFFSETS[DATA[self.piece.shape]['offset']][STATES[(self.piece.state + self.rotation) % 4]])]:
                            self.testPiece = copy.deepcopy(self.piece)
                            self.testPiece.rotate(self.rotation, offset)
                            if all(c not in self.board for c in self.testPiece.blocks):
                                self.piece = copy.deepcopy(self.testPiece)
                                break
                        self.rotation = None
                    if self.direction:
                        if all(coordSum(c, self.direction) not in self.board for c in self.piece.blocks):
                            self.piece.move(self.direction)
                            if self.direction == DOWN:
                                self.softDropCells += 1

            if TOGGLE_GHOST:
                self.computeGhost()

            self.boardRender()
            pygame.display.flip()
        
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_UP or event.key == K_c:
                        self.rotation = CW
                    if event.key == K_x:
                        self.rotation = CCW
                    if event.key == K_LEFT:
                        self.direction = LEFT
                    if event.key == K_RIGHT:
                        self.direction = RIGHT
                    if event.key == K_DOWN:
                        self.direction = DOWN
                    if event.key == K_SPACE:
                        self.hardDrop = True
                if event.type == KEYUP:
                    if event.key == K_LEFT or event.key == K_RIGHT or event.key == K_DOWN or event.key == K_UP or event.key == K_x or event.key == K_c or event.key == K_SPACE:
                        self.direction = STOP
                    if event.key == K_p:
                        self.togglePause()
                    if event.key == K_r:
                        self.toggleReset()
                    if event.key == K_g:
                        self.toggleGhostPiece()
                    if event.key == K_m:
                        self.toggleBGMusic()
                    if event.key == K_ESCAPE or event.key == K_q:
                        pygame.quit()
                        sys.exit()
                if event.type == BLOCK_FALL and not self.gameOver and not self.pause:
                    self.gravity()
            if not self.gameOver and not self.pause:
                self.play()

            self.mainClock.tick(PLAYSPEED)

if __name__ == '__main__':
    game = Game()
    game.run()
