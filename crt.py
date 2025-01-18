import pygame
import sys
import math
import random
import time
import csv
import os
import datetime

########################
# CONFIGURATION
########################
WIN_WIDTH = 1280
WIN_HEIGHT = 1280

BG_COLOR = (30, 30, 30)
HOME_COLOR = (120, 120, 120)
TARGET_COLOR = (100, 100, 255)
TARGET_HIGHLIGHT_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 255, 255)

HOME_RADIUS = 50
TARGET_RADIUS = 50
TARGET_POS_RADIUS = 500
HOME_POS = (WIN_WIDTH // 2, WIN_HEIGHT // 2)

N_TARGETS = 16
N_TRIALS = 20

# Random delay before lighting the target (seconds)
DELAY_MIN = 1.0
DELAY_MAX = 4.0

# Name of the CSV file to store results
CSV_FILENAME = "results.csv"

pygame.init()
pygame.display.set_caption("CRT")
screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

def draw_text(surface, text, center_x, top_y, color=TEXT_COLOR):
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(midtop=(center_x, top_y))
    surface.blit(text_surf, rect)

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def generate_target_positions(n_targets):
    """
    Returns (x, y) positions for n_targets arranged in a semicircle above the home circle.
    """
    cx, cy = HOME_POS
    angles = [
        math.radians(i * (360 / n_targets))
        for i in range(n_targets)
    ]
    positions = []
    for a in angles:
        tx = cx + TARGET_POS_RADIUS * math.cos(a)
        ty = cy - TARGET_POS_RADIUS * math.sin(a)
        positions.append((int(tx), int(ty)))
    return positions

def log_to_csv(rt_ms, mt_ms, target):
    """
    Append a row to the CSV file with date/time, RT, and MT.
    If CSV doesn't exist, create it with a header.
    """
    file_exists = os.path.isfile(CSV_FILENAME)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CSV_FILENAME, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write header if file did not exist
        if not file_exists:
            writer.writerow(["datetime", "reaction_time_ms", "movement_time_ms", "target"])
        # Write the new row
        writer.writerow([now_str, f"{rt_ms:.1f}", f"{mt_ms:.1f}", f"{target}"])

def main():
    target_positions = generate_target_positions(N_TARGETS)

    for trial_index in range(1, N_TRIALS + 1):
        # --- Step 1: wait for mouse to be in home circle ---
        while True:
            screen.fill(BG_COLOR)
            pygame.draw.circle(screen, HOME_COLOR, HOME_POS, HOME_RADIUS)
            for pos in target_positions:
                pygame.draw.circle(screen, TARGET_COLOR, pos, TARGET_RADIUS)

            draw_text(screen, f"Trial {trial_index} of {N_TRIALS}", WIN_WIDTH//2, 10)
            draw_text(screen, "Place mouse in the home circle...", WIN_WIDTH//2, 50)

            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            mx, my = pygame.mouse.get_pos()
            if distance((mx, my), HOME_POS) < HOME_RADIUS:
                break

        # --- Step 2: random delay (1–4 s); if user leaves early, ABORT this trial ---
        aborted = False
        selected_target = random.randrange(N_TARGETS)
        start_delay = time.time()
        wait_time = random.uniform(DELAY_MIN, DELAY_MAX)

        while time.time() - start_delay < wait_time:
            screen.fill(BG_COLOR)
            pygame.draw.circle(screen, HOME_COLOR, HOME_POS, HOME_RADIUS)
            for pos in target_positions:
                pygame.draw.circle(screen, TARGET_COLOR, pos, TARGET_RADIUS)

            draw_text(screen, f"Trial {trial_index} of {N_TRIALS}", WIN_WIDTH//2, 10)
            draw_text(screen, "Stay in home circle...", WIN_WIDTH//2, 50)

            pygame.display.flip()
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Check if mouse left home circle prematurely
            mx, my = pygame.mouse.get_pos()
            if distance((mx, my), HOME_POS) > HOME_RADIUS:
                aborted = True
                break

        if aborted:
            # Show "Aborted" feedback briefly
            feedback_start = time.time()
            while time.time() - feedback_start < 1.0:
                screen.fill(BG_COLOR)
                draw_text(screen, f"Trial {trial_index} ABORTED", WIN_WIDTH//2, WIN_HEIGHT//2)
                pygame.display.flip()
                clock.tick(60)
            continue  # Skip to next trial

        # --- Step 3: Illuminate target; measure RT/MT ---
        rt_start = time.time()
        mt_start = None
        clicked = False
        result_rt = None
        result_mt = None

        while not clicked:
            screen.fill(BG_COLOR)
            pygame.draw.circle(screen, HOME_COLOR, HOME_POS, HOME_RADIUS)

            # Draw targets; highlight the selected one
            for i, pos in enumerate(target_positions):
                color = TARGET_COLOR
                if i == selected_target:
                    color = TARGET_HIGHLIGHT_COLOR
                pygame.draw.circle(screen, color, pos, TARGET_RADIUS)

            draw_text(screen, f"Trial {trial_index} of {N_TRIALS}", WIN_WIDTH//2, 10)
            pygame.display.flip()
            clock.tick(1000)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    # If leaving home circle for the first time, record time for MT
                    if mt_start is None and distance((mx, my), HOME_POS) > HOME_RADIUS:
                        mt_start = time.time()
                        rt_end = mt_start
                        result_rt = rt_end - rt_start
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    # Check if the click is on the selected target
                    if distance((mx, my), target_positions[selected_target]) < TARGET_RADIUS:
                        clicked = True
                        mt_end = time.time()
                        if mt_start is not None:
                            result_mt = mt_end - mt_start

        # --- Step 4: record trial results, log to CSV, and show quick feedback ---
        rt_ms = result_rt * 1000.0
        mt_ms = result_mt * 1000.0

        # Log to CSV
        log_to_csv(rt_ms, mt_ms, selected_target)

        # Show feedback
        feedback_start = time.time()
        while time.time() - feedback_start < 1.0:
            screen.fill(BG_COLOR)
            msg = f"RT: {rt_ms:.1f} ms"
            if mt_ms is not None:
                msg += f"  |  MT: {mt_ms:.1f} ms"
            draw_text(screen, msg, WIN_WIDTH//2, WIN_HEIGHT//2)
            pygame.display.flip()
            clock.tick(60)

    # --- End of experiment ---
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
