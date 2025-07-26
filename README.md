# PuyoPuyo-like Puzzle Game

A classic falling-block puzzle game similar to Puyo Puyo, implemented in Python using Pygame.

## Features

- **Classic Puyo Gameplay**: Two puyos fall together as a pair that you can move and rotate
- **Chain Reactions**: Clear 4+ connected puyos to trigger chain reactions for higher scores
- **Score System**: Advanced scoring with chain bonuses and group size bonuses
- **Next Puyo Preview**: See the next puyo pair that will fall
- **Game Over Detection**: Game ends when puyos reach the top
- **Restart Functionality**: Press R to restart after game over

## Game Mechanics

- **Grid**: 6 columns × 12 rows playing field
- **Puyo Colors**: 5 different colored puyos (Red, Blue, Green, Yellow, Purple)
- **Clearing**: Connect 4 or more puyos of the same color to clear them
- **Gravity**: Puyos fall down after clearing, potentially creating chain reactions
- **Scoring**: 
  - Base points: 10 points per cleared puyo
  - Chain bonus: 2× multiplier per chain level
  - Group bonus: Additional multiplier based on number of groups cleared

## Controls

- **← →**: Move puyo pair left/right
- **↓**: Soft drop (faster falling)
- **↑**: Hard drop (instant drop)
- **Z/X**: Rotate puyo pair clockwise
- **C**: Rotate puyo pair counter-clockwise
- **R**: Restart game (when game over)

## Installation and Running

1. Install the required dependency:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the game:
   ```bash
   python puyo_game.py
   ```

## Game Rules

1. Puyo pairs fall from the top of the screen
2. Use the controls to position and rotate the falling pair
3. When a pair lands, individual puyos will fall to the lowest possible position
4. If 4 or more puyos of the same color are connected (horizontally or vertically), they will disappear
5. When puyos are cleared, remaining puyos fall down due to gravity
6. This can create chain reactions if new groups of 4+ are formed
7. Chain reactions give exponentially higher scores
8. Game ends when puyos stack up to the top of the playing field

## Technical Implementation

The game is built using object-oriented design with the following key classes:

- **PuyoGame**: Main game controller and rendering
- **GameGrid**: Manages the game board state and puyo placement
- **PuyoPair**: Represents falling puyo pairs with rotation logic
- **Position**: Simple coordinate class for position management

The game runs at 60 FPS and includes proper collision detection, gravity simulation, and flood-fill algorithms for connected puyo detection.
