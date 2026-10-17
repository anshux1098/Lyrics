#!/usr/bin/env python3
"""
LyricSh Pi Receiver
Runs on Raspberry Pi. Receives lyric data over UDP from the laptop,
renders it fullscreen via pygame (which outputs to HDMI).

Usage: python3 pi_receiver.py
Requires: sudo apt install python3-pygame
"""

import json
import socket
import sys

try:
    import pygame
    pygame.init()
except ImportError:
    print("ERROR: pygame not installed. Run: sudo apt install python3-pygame")
    sys.exit(1)

UDP_PORT = 5005
WHITE = (255, 255, 255)
DIM = (100, 100, 100)
BLACK = (0, 0, 0)
GOLD = (212, 175, 55)

# Fullscreen setup
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("LyricSh")
clock = pygame.time.Clock()

# Fonts
try:
    font_current = pygame.font.SysFont("dejavusans", HEIGHT // 12, bold=True)
    font_other = pygame.font.SysFont("dejavusans", HEIGHT // 22)
    font_status = pygame.font.SysFont("dejavusans", HEIGHT // 40)
except Exception:
    font_current = pygame.font.Font(None, HEIGHT // 12)
    font_other = pygame.font.Font(None, HEIGHT // 22)
    font_status = pygame.font.Font(None, HEIGHT // 40)


def render_text_centered(surface, text, font, color, y_center):
    """Render text centered horizontally at the given y position."""
    if not text:
        return
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, y_center))
    surface.blit(text_surface, text_rect)


def draw_lyrics(data):
    """Draw the full lyrics display."""
    screen.fill(BLACK)

    # Previous line (dim, above center)
    render_text_centered(
        screen, data.get("prev", ""), font_other, DIM, HEIGHT * 0.38
    )

    # Current line (bright, large, center)
    current = data.get("current", "")
    if current:
        render_text_centered(
            screen, current, font_current, WHITE, HEIGHT * 0.50
        )

    # Next line (dim, below center)
    render_text_centered(
        screen, data.get("next", ""), font_other, DIM, HEIGHT * 0.62
    )

    # Status bar (artist - title)
    artist = data.get("artist", "")
    title = data.get("title", "")
    if artist or title:
        status = f"{artist} — {title}"
        if data.get("state", 1) == 0:
            status += "  ⏸"
        status_surface = font_status.render(status, True, (60, 60, 60))
        status_rect = status_surface.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        screen.blit(status_surface, status_rect)


def main():
    # UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", UDP_PORT))
    sock.setblocking(False)

    current_data = {
        "artist": "",
        "title": "",
        "prev": "",
        "current": "Waiting for lyrics...",
        "next": "",
        "state": 1,
    }

    print(f"[LyricSh Pi] Listening on UDP port {UDP_PORT}")
    print(f"[LyricSh Pi] Display: {WIDTH}x{HEIGHT}")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Check for new UDP data
        try:
            while True:
                data, addr = sock.recvfrom(4096)
                try:
                    current_data = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    pass
        except BlockingIOError:
            pass

        draw_lyrics(current_data)
        pygame.display.flip()
        clock.tick(30)  # 30 FPS

    sock.close()
    pygame.quit()


if __name__ == "__main__":
    main()
