import pygame
import random
import sys

# --- Initialization ---
pygame.init()
pygame.font.init()

# --- Screen Constants ---
WIDTH, HEIGHT = 1000, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cyber Escape") # CHANGED GAME NAME HERE

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# --- Fonts ---
# Adjusted font sizes to prevent them from going off-screen
HEALTH_FONT = pygame.font.SysFont('comicsans', 30)
MAIN_FONT = pygame.font.SysFont('comicsans', 35) # Reduced from 40
TITLE_FONT = pygame.font.SysFont('comicsans', 55) # Reduced from 70
CLUE_FONT = pygame.font.SysFont('consolas', 20)
QUIZ_FONT = pygame.font.SysFont('comicsans', 25)

# --- Game Constants ---
FPS = 60
PLAYER_VEL = 5
PATCH_VEL = 7 # Projectile speed
ENEMY_PATCH_VEL = 4

# --- Game Asset Classes ---

class Projectile:
    """Base class for all projectiles"""
    def __init__(self, x, y, width, height, color, vel):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.vel = vel

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)

    def move(self):
        self.rect.y += self.vel

    def is_off_screen(self):
        return not (0 <= self.rect.y <= HEIGHT)

    def collision(self, obj):
        return self.rect.colliderect(obj.rect)

class Patch(Projectile):
    """Player's projectile"""
    def __init__(self, x, y):
        super().__init__(x, y, 5, 10, BLUE, -PATCH_VEL)

class DataPacket(Projectile):
    """Enemy's projectile"""
    def __init__(self, x, y):
        super().__init__(x, y, 8, 8, YELLOW, ENEMY_PATCH_VEL)

class Ship:
    """Base class for Player and Enemy ships"""
    COOLDOWN = 30 # Half a second at 60 FPS

    def __init__(self, x, y, width, height, color, health=100):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.health = health
        self.max_health = health
        self.cooldown_counter = 0
        self.projectiles = []

    def draw(self, win):
        pygame.draw.rect(win, self.color, self.rect)
        self.draw_health_bar(win)

    def draw_health_bar(self, win):
        # Red background
        pygame.draw.rect(win, RED, (self.rect.x, self.rect.y + self.rect.height + 5, self.rect.width, 10))
        # Green foreground
        health_ratio = self.health / self.max_health
        pygame.draw.rect(win, GREEN, (self.rect.x, self.rect.y + self.rect.height + 5, self.rect.width * health_ratio, 10))

    def move_projectiles(self, obj):
        """Move projectiles and handle collision with 'obj' (e.g., player or enemy)"""
        self.cooldown()
        for projectile in self.projectiles:
            projectile.move()
            if projectile.is_off_screen():
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
            elif projectile.collision(obj):
                obj.health -= 15
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)

    def cooldown(self):
        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1

    def shoot(self, ProjectileType):
        if self.cooldown_counter == 0:
            projectile = ProjectileType(self.rect.centerx - (ProjectileType(0,0).rect.width / 2), self.rect.y)
            self.projectiles.append(projectile)
            self.cooldown_counter = self.COOLDOWN

class Player(Ship):
    """Player's ship (The Defender)"""
    def __init__(self, x, y):
        super().__init__(x, y, 50, 40, GREEN, health=100)

    def shoot(self):
        super().shoot(Patch) # Shoots a Patch

    def move_projectiles(self, objs):
        """Override to handle collision with a list of enemies"""
        self.cooldown()
        for projectile in self.projectiles:
            projectile.move()
            if projectile.is_off_screen():
                if projectile in self.projectiles:
                    self.projectiles.remove(projectile)
            else:
                for obj in objs:
                    if projectile.collision(obj):
                        obj.health -= 10
                        if projectile in self.projectiles:
                            self.projectiles.remove(projectile)
                        if obj.health <= 0:
                            if obj in objs:
                                objs.remove(obj)

class Enemy(Ship):
    """Enemy ship (The Malware)"""
    def __init__(self, x, y, width, height, color, health, name, vel_x):
        super().__init__(x, y, width, height, color, health)
        self.name = name
        self.vel_x = vel_x
        self.vel_y = 1
        self.shoot_chance = 0.01 # 1% chance per frame

    def move(self):
        self.rect.x += self.vel_x
        # Bounce off walls
        if self.rect.x <= 0 or self.rect.right >= WIDTH:
            self.vel_x *= -1
            # Move down when hitting a wall
            self.rect.y += self.rect.height // 2

    def attempt_shoot(self):
        if random.random() < self.shoot_chance:
            super().shoot(DataPacket) # Shoots a DataPacket

# --- Helper Functions ---

def get_boss_for_level(level):
    """Returns a new boss based on the level number"""
    if level == 1:
        return Enemy(WIDTH/2 - 35, 50, 70, 50, RED, 100, "Worm", 4)
    elif level == 2:
        boss = Enemy(WIDTH/2 - 40, 50, 80, 60, PURPLE, 200, "Trojan", 5)
        boss.shoot_chance = 0.03 # Trojans shoot more
        return boss
    elif level == 3:
        boss = Enemy(WIDTH/2 - 50, 50, 100, 70, ORANGE, 300, "Ransomware", 6)
        boss.shoot_chance = 0.05 # Ransomware shoots a lot
        return boss
    return None

def draw_window(win, player, boss, level, mystery_clues):
    """Main drawing function, called every frame"""
    win.fill(BLACK) # Dark background

    # Draw UI
    player_health_label = HEALTH_FONT.render(f"Defender Health: {player.health}", 1, WHITE)
    level_label = MAIN_FONT.render(f"Threat Level: {level}", 1, WHITE)
    win.blit(player_health_label, (10, 10))
    win.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

    # Draw Mystery Clues
    clue_title = CLUE_FONT.render("--- DECRYPTED DATA ---", 1, GREEN)
    win.blit(clue_title, (10, 50))
    for i, clue in enumerate(mystery_clues):
        clue_label = CLUE_FONT.render(clue, 1, GREEN)
        win.blit(clue_label, (10, 75 + i * 25))

    # Draw Game Objects
    player.draw(win)
    if boss:
        boss.draw(win)
        boss_name_label = MAIN_FONT.render(boss.name, 1, boss.color)
        win.blit(boss_name_label, (WIDTH/2 - boss_name_label.get_width()/2, 10))

    for patch in player.projectiles:
        patch.draw(win)

    if boss:
        for packet in boss.projectiles:
            packet.draw(win)

    pygame.display.update()

def draw_quiz(win, quiz_data, message=None):
    """Draws the centered quiz screen with word wrapping."""
    win.fill(BLACK)
    
    line_spacing = QUIZ_FONT.get_height() + 5 # Dynamic spacing, approx 30px
    current_y = HEIGHT // 4 # Start higher up to maximize space

    # 1. Draw Title
    title_label = MAIN_FONT.render("== THREAT ASSESSMENT QUIZ ==", 1, YELLOW)
    win.blit(title_label, (WIDTH/2 - title_label.get_width()/2, current_y))
    current_y += title_label.get_height() + 20 # Move down

    # 2. Draw Question (with wrapping logic)
    question_text = quiz_data["question"]
    wrapped_lines = []
    words = question_text.split(' ')
    current_line = ""
    max_width = WIDTH - 80 # Leave 40px margin on each side

    for word in words:
        test_line = current_line + word + " "
        if QUIZ_FONT.size(test_line)[0] < max_width:
            current_line = test_line
        else:
            if current_line:
                wrapped_lines.append(current_line.strip())
            current_line = word + " "
    wrapped_lines.append(current_line.strip())

    current_y += 10 # Small gap before question
    for line in wrapped_lines:
        q_label = QUIZ_FONT.render(line, 1, WHITE)
        win.blit(q_label, (WIDTH/2 - q_label.get_width()/2, current_y))
        current_y += line_spacing
    
    current_y += 20 # Gap before options

    # 3. Draw Options
    for option_text in quiz_data["options"]:
        opt_label = QUIZ_FONT.render(option_text, 1, WHITE)
        win.blit(opt_label, (WIDTH/2 - opt_label.get_width()/2, current_y))
        current_y += line_spacing

    # 4. Draw Prompt/Feedback Area
    current_y += 15 # Gap before prompt

    prompt_line = "Press 1, 2, or 3 to answer."
    
    if message:
        # If there is feedback, show that instead of the generic prompt
        feedback_color = RED if "Incorrect" in message else GREEN
        feedback_font = MAIN_FONT
        feedback_label = feedback_font.render(message, 1, feedback_color)
        win.blit(feedback_label, (WIDTH/2 - feedback_label.get_width()/2, current_y))
    else:
        # Show the regular prompt
        prompt_label = QUIZ_FONT.render(prompt_line, 1, WHITE)
        win.blit(prompt_label, (WIDTH/2 - prompt_label.get_width()/2, current_y))
    
    # pygame.display.update() is handled outside


def draw_message(win, text_lines, duration_ms):
    """Shows a centered message for a duration"""
    win.fill(BLACK)
    
    # Adjusted line spacing from 50 to 40 for smaller font
    total_height = len(text_lines) * 40
    start_y = (HEIGHT - total_height) / 2
    
    for i, line in enumerate(text_lines):
        message_label = MAIN_FONT.render(line, 1, WHITE)
        # Adjusted spacing from 50 to 40
        win.blit(message_label, (WIDTH/2 - message_label.get_width()/2, start_y + i * 40))
    
    pygame.display.update()
    pygame.time.delay(duration_ms)

# --- Main Game Function ---

def main():
    run = True
    clock = pygame.time.Clock()

    # Game state can be "MENU", "PLAYING", "QUIZ", or "LOST"
    game_state = "PLAYING"
    
    level = 0
    player = Player(WIDTH/2 - 25, HEIGHT - 70)
    
    boss = None
    boss_name_for_clue = ""
    mystery_clues = []
    current_quiz = None
    quiz_feedback = None # Stores messages like "Correct!" or "Incorrect, try again."

    QUIZ_DATA = {
        1: {
            "question": "The spreading entity must be contained. What boundary stops unauthorized internal movement?",
            "options": ["1. Strong Passwords", "2. Network Firewall", "3. Antivirus Software"],
            "answer": 2, # Network Firewall
            "clue": "Clue 1: 'Always_use_'",
        },
        2: {
            "question": "The deceiver passed as friend. What policy trusts nothing and verifies everything?",
            "options": ["1. Least Privilege", "2. Defense in Depth", "3. Zero Trust"],
            "answer": 3, # Zero Trust
            "clue": "Clue 2: 'strong_passwords_'",
        },
        3: {
            "question": "The vault is sealed, the key is lost. What backup plan restores the lost data?",
            "options": ["1. Pay the ransom", "2. Regular Data Backups", "3. Change your IP address"],
            "answer": 2, # Regular Data Backups
            "clue": "Clue 3: '&_2FA!'",
        }
    }


    # --- Initial Level Setup ---
    level = 1
    boss = get_boss_for_level(level)
    draw_message(WIN, [f"WARNING! New Threat Detected:",
                        f"--- {boss.name.upper()} ---"], 2000)

    while run:
        clock.tick(FPS)

        # --- Game State Logic ---
        threat_breached = False
        
        # 1. Check for player defeat (health = 0)
        if player.health <= 0:
            game_state = "LOST"
        
        # 2. Check for system breach (boss passed the bottom)
        if game_state == "PLAYING" and boss and boss.rect.bottom >= HEIGHT:
            game_state = "LOST"
            threat_breached = True
        
        if game_state == "LOST":
            if threat_breached:
                # If the boss passed the line
                draw_message(WIN, [f"THREAT {boss.name.upper()} COMPROMISED SYSTEM", "GAME OVER"], 4000)
            else:
                # If the player health reached 0
                draw_message(WIN, ["DEFENDER DEFEATED", "GAME OVER"], 4000)
            
            run = False
            continue

        # Check for boss defeat ONLY if playing
        if game_state == "PLAYING" and boss and boss.health <= 0:
            boss_name_for_clue = boss.name
            boss = None
            
            if level < len(QUIZ_DATA):
                # Transition to quiz state
                level += 1 # Advance to the next level's data
                current_quiz = QUIZ_DATA[level - 1] # Get quiz for the level just defeated
                game_state = "QUIZ"
                quiz_feedback = None
            else:
                # Level 3 defeated, straight to win screen
                game_state = "LOST" # Using LOST state to trigger the final win message
                # CHANGED VICTORY MESSAGE HERE
                draw_message(WIN, ["ALL THREATS NEUTRALIZED! You have escaped the lab!", 
                                 "Secret: Always_use_strong_passwords_&_2FA!"], 5000)
                run = False
                continue

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            
            if game_state == "QUIZ" and event.type == pygame.KEYDOWN:
                answer = 0
                if event.key == pygame.K_1:
                    answer = 1
                elif event.key == pygame.K_2:
                    answer = 2
                elif event.key == pygame.K_3:
                    answer = 3
                
                if answer == current_quiz["answer"]:
                    # Correct Answer!
                    clue = current_quiz["clue"]
                    mystery_clues.append(clue)
                    draw_message(WIN, [f"ANSWER ACCEPTED: Correct!",
                                         "New Data Fragment Decrypted:",
                                         f"{clue}",
                                         "Press any key to face the next threat..."], 3000)
                    
                    # Spawn next boss and go back to PLAYING
                    boss = get_boss_for_level(level)
                    game_state = "PLAYING"
                    draw_message(WIN, [f"WARNING! New Threat Detected:",
                                         f"--- {boss.name.upper()} ---"], 2000)

                elif answer in [1, 2, 3]:
                    # Incorrect Answer
                    quiz_feedback = "INCORRECT! System health compromised. Try again."
                    player.health = max(1, player.health - 10) # Minor penalty

        
        # --- Game Loop (PLAYING State) ---
        if game_state == "PLAYING":
            # --- Input Handling (Movement/Shooting) ---
            keys = pygame.key.get_pressed()
            if (keys[pygame.K_a] or keys[pygame.K_LEFT]) and player.rect.x - PLAYER_VEL > 0:
                player.rect.x -= PLAYER_VEL
            if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player.rect.right + PLAYER_VEL < WIDTH:
                player.rect.x += PLAYER_VEL
            if keys[pygame.K_SPACE]:
                player.shoot()

            # --- Update Game Objects ---
            
            # We need a list for the player to check against
            boss_list = [boss] if boss else []
            player.move_projectiles(boss_list) # Moves player patches, checks collision with boss
            
            if boss:
                boss.move()
                boss.attempt_shoot()
                boss.move_projectiles(player) # Moves boss packets, checks collision with player

            # --- Drawing ---
            draw_window(WIN, player, boss, level, mystery_clues)

        # --- Quiz Loop (QUIZ State) ---
        elif game_state == "QUIZ":
            draw_quiz(WIN, current_quiz, quiz_feedback)
            pygame.display.update()


    pygame.quit()
    sys.exit()

def main_menu():
    """Shows the main menu screen"""
    run = True
    while run:
        WIN.fill(BLACK)
        title_label = TITLE_FONT.render("CYBER ESCAPE", 1, GREEN) # CHANGED MENU TITLE HERE
        prompt_label = MAIN_FONT.render("Press any key to begin...", 1, WHITE)
        
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, HEIGHT/2 - 100))
        WIN.blit(prompt_label, (WIDTH/2 - prompt_label.get_width()/2, HEIGHT/2 + 20))
        
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                main() # Start the main game
                run = False # Exit menu loop once game is over

    pygame.quit()
    sys.exit()

# --- Run the Game ---
if __name__ == "__main__":
    main_menu()