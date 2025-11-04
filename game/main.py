import pygame
import sys
import json
import os
from DATABASE import Database

class ClickerGame:
    def __init__(self):
        pygame.init()
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Clicker Game")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.running = True
        
        # Load settings
        self.settings = self.load_settings()
        
        # Initialize database
        self.db = Database('../database/clicker.db')
        
        # Game state
        self.score = 0
        self.clicks = 0
        self.upgrades = []
        self.user_id = None
        
    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                return json.load(f)
        return {'music_volume': 0.5, 'sound_effects': True}
    
    def save_settings(self):
        with open('settings.json', 'w') as f:
            json.dump(self.settings, f)
    
    def login(self, username, password):
        user = self.db.get_user(username)
        if user and user['password'] == password:  # In real app, use hashing!
            self.user_id = user['id']
            self.load_game_state()
            return True
        return False
    
    def register(self, username, password):
        return self.db.create_user(username, password)
    
    def load_game_state(self):
        if self.user_id:
            save = self.db.get_user_save(self.user_id)
            if save:
                self.score = save['score']
                self.clicks = save['clicks']
                self.upgrades = self.db.get_user_upgrades(self.user_id)
    
    def save_game_state(self):
        if self.user_id:
            self.db.update_user_save(self.user_id, self.score, self.clicks)
    
    def draw_button(self, text, x, y, width, height, color, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        
        if x < mouse[0] < x + width and y < mouse[1] < y + height:
            pygame.draw.rect(self.screen, (color[0]-20, color[1]-20, color[2]-20), (x, y, width, height))
            if click[0] == 1 and action is not None:
                action()
        else:
            pygame.draw.rect(self.screen, color, (x, y, width, height))
            
        text_surf = self.font.render(text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=((x + (width/2)), (y + (height/2))))
        self.screen.blit(text_surf, text_rect)
    
    def draw_text(self, text, x, y, color=(0, 0, 0)):
        text_surf = self.font.render(text, True, color)
        self.screen.blit(text_surf, (x, y))
    
    def main_loop(self):
        while self.running:
            self.screen.fill((240, 240, 240))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_game_state()
                    self.running = False
            
            # Draw game interface
            self.draw_text(f"Score: {self.score}", 20, 20)
            self.draw_text(f"Clicks: {self.clicks}", 20, 50)
            
            # Draw click button
            self.draw_button("CLICK ME!", 300, 200, 200, 100, (100, 200, 100), self.click)
            
            # Draw upgrades
            for i, upgrade in enumerate(self.db.get_all_upgrades()):
                self.draw_button(
                    f"{upgrade['name']} - {upgrade['cost']}",
                    500, 100 + i * 60, 200, 50,
                    (200, 100, 100),
                    lambda u=upgrade: self.buy_upgrade(u)
                )
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()
    
    def click(self):
        self.clicks += 1
        self.score += 1
        # Add upgrade bonuses
        for upgrade in self.upgrades:
            self.score += upgrade['increment']
    
    def buy_upgrade(self, upgrade):
        if self.score >= upgrade['cost']:
            self.score -= upgrade['cost']
            self.db.add_user_upgrade(self.user_id, upgrade['id'])
            self.upgrades = self.db.get_user_upgrades(self.user_id)

if __name__ == "__main__":
    game = ClickerGame()
    
    # Simple login screen
    logged_in = False
    while not logged_in:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        game.screen.fill((240, 240, 240))
        game.draw_text("Clicker Game - Login", 300, 100)
        game.draw_text("Username: admin", 300, 150)
        game.draw_text("Password: admin", 300, 200)
        game.draw_button("Login", 300, 250, 200, 50, (100, 100, 200), 
                            lambda: game.login('admin', 'admin') and setattr(game, 'logged_in', True))
        
        pygame.display.flip()
        game.clock.tick(60)
        
        if hasattr(game, 'logged_in') and game.logged_in:
            logged_in = True
    
    game.main_loop()