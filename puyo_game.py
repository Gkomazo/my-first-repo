import pygame
import random
import time
from enum import Enum
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_WIDTH = 6
GRID_HEIGHT = 12
CELL_SIZE = 40
GRID_X_OFFSET = 100
GRID_Y_OFFSET = 50

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)

# Puyo colors (1-5, 0 is empty)
PUYO_COLORS = {
    0: BLACK,
    1: RED,
    2: BLUE,
    3: GREEN,
    4: YELLOW,
    5: PURPLE
}

class PuyoType(Enum):
    EMPTY = 0
    RED = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    PURPLE = 5

@dataclass
class Position:
    x: int
    y: int
    
    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y)

class PuyoPair:
    """Represents a falling pair of puyos"""
    def __init__(self, color1: int, color2: int, x: int = GRID_WIDTH // 2 - 1, y: int = 0):
        self.main_puyo = Position(x, y)
        self.sub_puyo = Position(x + 1, y)
        self.main_color = color1
        self.sub_color = color2
        self.rotation_state = 0  # 0: right, 1: down, 2: left, 3: up
        
    def get_positions(self) -> Tuple[Position, Position]:
        """Get current positions of both puyos based on rotation state"""
        offsets = [
            Position(1, 0),   # right
            Position(0, 1),   # down
            Position(-1, 0),  # left
            Position(0, -1)   # up
        ]
        sub_pos = self.main_puyo + offsets[self.rotation_state]
        return self.main_puyo, sub_pos
    
    def rotate_clockwise(self):
        """Rotate the pair clockwise"""
        self.rotation_state = (self.rotation_state + 1) % 4
        
    def rotate_counter_clockwise(self):
        """Rotate the pair counter-clockwise"""
        self.rotation_state = (self.rotation_state - 1) % 4
        
    def move(self, dx: int, dy: int):
        """Move the pair by dx, dy"""
        self.main_puyo.x += dx
        self.main_puyo.y += dy

class GameGrid:
    """Represents the game board"""
    def __init__(self, width: int = GRID_WIDTH, height: int = GRID_HEIGHT):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is within bounds and empty"""
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 0
        
    def can_place_pair(self, pair: PuyoPair) -> bool:
        """Check if a puyo pair can be placed at its current position"""
        main_pos, sub_pos = pair.get_positions()
        return (self.is_valid_position(main_pos.x, main_pos.y) and 
                self.is_valid_position(sub_pos.x, sub_pos.y))
    
    def place_puyo(self, x: int, y: int, color: int):
        """Place a puyo at the specified position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = color
            
    def apply_gravity(self):
        """Apply gravity to all puyos"""
        for x in range(self.width):
            # Collect all non-zero puyos in this column
            puyos = []
            for y in range(self.height - 1, -1, -1):
                if self.grid[y][x] != 0:
                    puyos.append(self.grid[y][x])
                self.grid[y][x] = 0
            
            # Place them at the bottom
            for i, puyo in enumerate(puyos):
                self.grid[self.height - 1 - i][x] = puyo
                
    def find_connected_puyos(self, start_x: int, start_y: int, color: int, visited: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Find all puyos connected to the starting position with the same color"""
        if (start_x, start_y) in visited:
            return set()
            
        if (start_x < 0 or start_x >= self.width or 
            start_y < 0 or start_y >= self.height or
            self.grid[start_y][start_x] != color):
            return set()
            
        visited.add((start_x, start_y))
        connected = {(start_x, start_y)}
        
        # Check all four directions
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dx, dy in directions:
            new_connected = self.find_connected_puyos(start_x + dx, start_y + dy, color, visited)
            connected.update(new_connected)
            
        return connected
    
    def find_and_clear_groups(self) -> Tuple[int, int]:
        """Find and clear groups of 4+ connected puyos. Returns (cleared_count, groups_cleared)"""
        visited = set()
        to_clear = set()
        groups_cleared = 0
        
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in visited and self.grid[y][x] != 0:
                    color = self.grid[y][x]
                    connected = self.find_connected_puyos(x, y, color, visited)
                    
                    if len(connected) >= 4:
                        to_clear.update(connected)
                        groups_cleared += 1
        
        # Clear the marked puyos
        cleared_count = len(to_clear)
        for x, y in to_clear:
            self.grid[y][x] = 0
            
        return cleared_count, groups_cleared
    
    def is_game_over(self) -> bool:
        """Check if the game is over (puyos reached the top)"""
        return any(self.grid[0][x] != 0 for x in range(self.width))

class PuyoGame:
    """Main game class"""
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("PuyoPuyo-like Puzzle Game")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.grid = GameGrid()
        self.current_pair = self.generate_new_pair()
        self.next_pair = self.generate_new_pair()
        self.score = 0
        self.chain_count = 0
        self.game_over = False
        self.fall_timer = 0
        self.fall_speed = 500  # milliseconds
        self.soft_drop_speed = 50  # milliseconds when soft dropping
        
        # Fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
    def generate_new_pair(self) -> PuyoPair:
        """Generate a new random puyo pair"""
        color1 = random.randint(1, 5)
        color2 = random.randint(1, 5)
        return PuyoPair(color1, color2)
    
    def can_move_pair(self, dx: int, dy: int) -> bool:
        """Check if the current pair can move in the given direction"""
        test_pair = PuyoPair(self.current_pair.main_color, self.current_pair.sub_color,
                           self.current_pair.main_puyo.x, self.current_pair.main_puyo.y)
        test_pair.rotation_state = self.current_pair.rotation_state
        test_pair.move(dx, dy)
        return self.grid.can_place_pair(test_pair)
    
    def can_rotate_pair(self, clockwise: bool = True) -> bool:
        """Check if the current pair can rotate"""
        test_pair = PuyoPair(self.current_pair.main_color, self.current_pair.sub_color,
                           self.current_pair.main_puyo.x, self.current_pair.main_puyo.y)
        test_pair.rotation_state = self.current_pair.rotation_state
        
        if clockwise:
            test_pair.rotate_clockwise()
        else:
            test_pair.rotate_counter_clockwise()
            
        return self.grid.can_place_pair(test_pair)
    
    def place_current_pair(self):
        """Place the current pair on the grid"""
        main_pos, sub_pos = self.current_pair.get_positions()
        
        # Apply gravity to each puyo individually
        for pos, color in [(main_pos, self.current_pair.main_color), 
                          (sub_pos, self.current_pair.sub_color)]:
            final_y = pos.y
            while final_y + 1 < self.grid.height and self.grid.grid[final_y + 1][pos.x] == 0:
                final_y += 1
            self.grid.place_puyo(pos.x, final_y, color)
    
    def process_chains(self):
        """Process chain reactions and update score"""
        self.chain_count = 0
        
        while True:
            self.grid.apply_gravity()
            cleared_count, groups_cleared = self.grid.find_and_clear_groups()
            
            if cleared_count == 0:
                break
                
            self.chain_count += 1
            
            # Calculate score: base points * group bonus * chain bonus
            base_score = cleared_count * 10
            chain_bonus = max(1, self.chain_count * 2)
            group_bonus = groups_cleared
            
            self.score += base_score * chain_bonus * group_bonus
            
            # Small delay for visual effect
            pygame.time.wait(200)
            self.draw()
            pygame.display.flip()
    
    def spawn_new_pair(self):
        """Spawn a new pair at the top"""
        self.current_pair = self.next_pair
        self.next_pair = self.generate_new_pair()
        
        # Reset position
        self.current_pair.main_puyo = Position(GRID_WIDTH // 2 - 1, 0)
        self.current_pair.rotation_state = 0
        
        # Check if game over
        if not self.grid.can_place_pair(self.current_pair):
            self.game_over = True
    
    def handle_input(self, event):
        """Handle keyboard input"""
        if event.type == pygame.KEYDOWN and not self.game_over:
            if event.key == pygame.K_LEFT:
                if self.can_move_pair(-1, 0):
                    self.current_pair.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                if self.can_move_pair(1, 0):
                    self.current_pair.move(1, 0)
            elif event.key == pygame.K_DOWN:
                if self.can_move_pair(0, 1):
                    self.current_pair.move(0, 1)
            elif event.key == pygame.K_UP:  # Hard drop
                while self.can_move_pair(0, 1):
                    self.current_pair.move(0, 1)
                self.place_current_pair()
                self.process_chains()
                self.spawn_new_pair()
            elif event.key == pygame.K_z or event.key == pygame.K_x:
                if self.can_rotate_pair(True):
                    self.current_pair.rotate_clockwise()
            elif event.key == pygame.K_c:
                if self.can_rotate_pair(False):
                    self.current_pair.rotate_counter_clockwise()
        elif event.type == pygame.KEYDOWN and self.game_over:
            if event.key == pygame.K_r:  # Restart game
                self.restart_game()
    
    def restart_game(self):
        """Restart the game"""
        self.grid = GameGrid()
        self.current_pair = self.generate_new_pair()
        self.next_pair = self.generate_new_pair()
        self.score = 0
        self.chain_count = 0
        self.game_over = False
        self.fall_timer = 0
    
    def update(self, dt: int):
        """Update game logic"""
        if self.game_over:
            return
            
        # Handle automatic falling
        keys = pygame.key.get_pressed()
        current_fall_speed = self.soft_drop_speed if keys[pygame.K_DOWN] else self.fall_speed
        
        self.fall_timer += dt
        if self.fall_timer >= current_fall_speed:
            self.fall_timer = 0
            
            if self.can_move_pair(0, 1):
                self.current_pair.move(0, 1)
            else:
                # Puyo pair has landed
                self.place_current_pair()
                self.process_chains()
                self.spawn_new_pair()
    
    def draw_puyo(self, x: int, y: int, color: int):
        """Draw a single puyo"""
        screen_x = GRID_X_OFFSET + x * CELL_SIZE
        screen_y = GRID_Y_OFFSET + y * CELL_SIZE
        
        pygame.draw.rect(self.screen, PUYO_COLORS[color], 
                        (screen_x, screen_y, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(self.screen, WHITE, 
                        (screen_x, screen_y, CELL_SIZE, CELL_SIZE), 2)
    
    def draw_grid(self):
        """Draw the game grid"""
        # Draw grid background
        grid_rect = pygame.Rect(GRID_X_OFFSET, GRID_Y_OFFSET, 
                               GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
        pygame.draw.rect(self.screen, GRAY, grid_rect, 2)
        
        # Draw placed puyos
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid.grid[y][x] != 0:
                    self.draw_puyo(x, y, self.grid.grid[y][x])
        
        # Draw current falling pair
        if not self.game_over:
            main_pos, sub_pos = self.current_pair.get_positions()
            if 0 <= main_pos.y < GRID_HEIGHT:
                self.draw_puyo(main_pos.x, main_pos.y, self.current_pair.main_color)
            if 0 <= sub_pos.y < GRID_HEIGHT:
                self.draw_puyo(sub_pos.x, sub_pos.y, self.current_pair.sub_color)
    
    def draw_next_puyo(self):
        """Draw the next puyo pair"""
        next_x = GRID_X_OFFSET + GRID_WIDTH * CELL_SIZE + 50
        next_y = GRID_Y_OFFSET + 50
        
        # Label
        text = self.small_font.render("NEXT:", True, WHITE)
        self.screen.blit(text, (next_x, next_y - 30))
        
        # Draw next pair
        pygame.draw.rect(self.screen, PUYO_COLORS[self.next_pair.main_color],
                        (next_x, next_y, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(self.screen, WHITE,
                        (next_x, next_y, CELL_SIZE, CELL_SIZE), 2)
        
        pygame.draw.rect(self.screen, PUYO_COLORS[self.next_pair.sub_color],
                        (next_x + CELL_SIZE, next_y, CELL_SIZE, CELL_SIZE))
        pygame.draw.rect(self.screen, WHITE,
                        (next_x + CELL_SIZE, next_y, CELL_SIZE, CELL_SIZE), 2)
    
    def draw_ui(self):
        """Draw UI elements"""
        ui_x = GRID_X_OFFSET + GRID_WIDTH * CELL_SIZE + 50
        ui_y = GRID_Y_OFFSET + 150
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (ui_x, ui_y))
        
        # Chain count (if > 0)
        if self.chain_count > 0:
            chain_text = self.small_font.render(f"Chain: {self.chain_count}", True, YELLOW)
            self.screen.blit(chain_text, (ui_x, ui_y + 40))
        
        # Controls
        controls_y = ui_y + 100
        controls = [
            "Controls:",
            "← → Move",
            "↓ Soft Drop",
            "↑ Hard Drop",
            "Z/X Rotate →",
            "C Rotate ←"
        ]
        
        for i, control in enumerate(controls):
            color = WHITE if i == 0 else GRAY
            text = self.small_font.render(control, True, color)
            self.screen.blit(text, (ui_x, controls_y + i * 20))
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over text
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(game_over_text, text_rect)
        
        # Final score
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)
        
        # Restart instruction
        restart_text = self.small_font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def draw(self):
        """Main drawing function"""
        self.screen.fill(BLACK)
        self.draw_grid()
        self.draw_next_puyo()
        self.draw_ui()
        
        if self.game_over:
            self.draw_game_over()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            dt = self.clock.tick(60)  # 60 FPS
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_input(event)
            
            # Update game
            self.update(dt)
            
            # Draw everything
            self.draw()
            pygame.display.flip()
        
        pygame.quit()

def main():
    """Entry point"""
    game = PuyoGame()
    game.run()

if __name__ == "__main__":
    main()