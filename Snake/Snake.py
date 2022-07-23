import pygame, sys, random, math
from pygame.locals import *

pygame.init()
mainClock = pygame.time.Clock()

CELLSIZE = 20
BOARDWIDTH = 20
BOARDHEIGHT = 20
OFFSET = 50
#Must be < BOARDWIDTH // 2
STARTLENGTH = 6
SPEEDUPLEVEL = 5
BONUSSPEED = 1

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)

RIGHT = (1, 0)
LEFT = (-1, 0)
UP = (0, -1)
DOWN = (0, 1)

def adjust(coords):
    if coords[0] == BOARDWIDTH:
        coords[0] = 0
    if coords[0] == -1:
        coords[0] = BOARDWIDTH - 1
    if coords[1] == BOARDHEIGHT:
        coords[1] = 0
    if coords[1] == -1:
        coords[1] = BOARDHEIGHT - 1
    return coords

draw_coord = lambda coords: pygame.Rect(CELLSIZE * coords[0], OFFSET + CELLSIZE * coords[1], CELLSIZE, CELLSIZE) 

WINDOWWIDTH = BOARDWIDTH * CELLSIZE
WINDOWHEIGHT = BOARDHEIGHT * CELLSIZE + OFFSET
windowSurface = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
pygame.display.set_caption('Snake')

#Top screen information
DELIMITERHEIGHT = 5
DELIMITERBORDER = 1
topDelimiter = pygame.Rect(0, OFFSET - DELIMITERHEIGHT, WINDOWWIDTH, DELIMITERHEIGHT)
topDelimiterInner = pygame.Rect(0, OFFSET - DELIMITERHEIGHT + DELIMITERBORDER, WINDOWWIDTH, DELIMITERHEIGHT - DELIMITERBORDER * 2)
FONTSIZE = 32
TEXTCOLOUR = YELLOW
scoreFont = pygame.font.SysFont(None, FONTSIZE)
def scoreDraw(score):
    scoreText = scoreFont.render(f"Score: {score}", 0, TEXTCOLOUR)
    scoreRect = scoreText.get_rect()
    scoreRect.centerx = WINDOWWIDTH // 2
    scoreRect.centery = OFFSET // 2
    return scoreText, scoreRect

FOODCAL = 4
def NewFood():
    while True:
        food = [random.randint(0, BOARDWIDTH - 1), random.randint(0, BOARDHEIGHT - 1)]
        if food not in player:
            return food

def gameStart():
    global player, player_draw, playerDirection, newDirection, MOVESPEED, food, food_draw, foodCount, gameOver
    player = [[x + STARTLENGTH // 2, math.ceil(BOARDHEIGHT / 2 - 1)] for x in range(STARTLENGTH, -1, -1)]
    #Is it better to maintain two lists, or redraw all the rectangles at each step?
    player_draw = [draw_coord(tile) for tile in player]
    playerDirection = RIGHT
    newDirection = RIGHT
    MOVESPEED = 5
    food = NewFood()
    food_draw = draw_coord(food)
    foodCount = 0
    gameOver = False

gameStart()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN and not gameOver:
            if event.key == K_LEFT or event.key == K_a:
                newDirection = LEFT if playerDirection != RIGHT else playerDirection
            if event.key == K_RIGHT or event.key == K_d:
                newDirection = RIGHT if playerDirection != LEFT else playerDirection
            if event.key == K_UP or event.key == K_w:
                newDirection = UP if playerDirection != DOWN else playerDirection
            if event.key == K_DOWN or event.key == K_s:
                newDirection = DOWN if playerDirection != UP else playerDirection
        if event.type == KEYUP:
            if event.key == K_r:
                gameStart()
            if event.key == K_ESCAPE or event.key == K_q:
                pygame.quit()
                sys.exit()
    
    if not gameOver:
        playerDirection = newDirection
        if (newHead := adjust([sum(x) for x in zip(player[0], playerDirection)])) in player:
            gameOver = True
        else:
            player.insert(0, newHead)
            player_draw.insert(0, draw_coord(newHead))
            if newHead == food:
                foodCount += 1
                if foodCount % SPEEDUPLEVEL == 0:
                    MOVESPEED += BONUSSPEED
                food = NewFood()
                food_draw = draw_coord(food)
                player += [player[-1] for x in range(FOODCAL)]
                player_draw += [draw_coord(player[-1]) for x in range(FOODCAL)]
            player.pop(-1)
            player_draw.pop(-1)

        windowSurface.fill(BLACK)
        for i in range(len(player_draw)):
            pygame.draw.rect(windowSurface, RED if gameOver and newHead == player[i] else WHITE, player_draw[i])
        
        pygame.draw.rect(windowSurface, GREEN, food_draw)

        pygame.draw.rect(windowSurface, YELLOW, topDelimiter)
        pygame.draw.rect(windowSurface, YELLOW, topDelimiterInner)
        
        scoreText, scoreRect = scoreDraw(foodCount)
        windowSurface.blit(scoreText, scoreRect)

        pygame.display.update()
        mainClock.tick(MOVESPEED)
