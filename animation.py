import argparse
import math
import os
import subprocess
from pathlib import Path

import imageio_ffmpeg
import pygame


WIDTH, HEIGHT = 960, 540
FPS = 30
DURATION = 9.2
FRAME_COUNT = round(FPS * DURATION)
FLOOR_Y = 458

INK = (27, 39, 48)
ORANGE = (255, 137, 54)
MINT = (72, 196, 170)
PAPER = (247, 246, 237)

pygame.init()
pygame.font.init()
FONT = pygame.font.SysFont("dejavusans", 18, bold=True)
SMALL_FONT = pygame.font.SysFont("dejavusans", 13, bold=True)
TITLE_FONT = pygame.font.SysFont("dejavusans", 32, bold=True)


def make_background():
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        mix = y / HEIGHT
        color = (int(183 + 48 * mix), int(224 + 20 * mix), int(226 + 4 * mix))
        pygame.draw.line(background, color, (0, y), (WIDTH, y))

    pygame.draw.circle(background, (255, 214, 123), (790, 100), 43)
    buildings = [
        (0, 290, 100, 168), (82, 250, 96, 208), (164, 315, 98, 143),
        (700, 270, 90, 188), (772, 230, 112, 228), (860, 300, 100, 158),
    ]
    for x, y, width, height in buildings:
        pygame.draw.rect(background, (107, 157, 163), (x, y, width, height))
        pygame.draw.rect(background, (81, 132, 142), (x, y, width, 8))
        for window_y in range(y + 24, FLOOR_Y - 16, 30):
            for window_x in range(x + 14, x + width - 8, 27):
                pygame.draw.rect(background, (190, 217, 201), (window_x, window_y, 10, 13), border_radius=2)

    pygame.draw.rect(background, PAPER, (0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y))
    pygame.draw.rect(background, INK, (0, FLOOR_Y, WIDTH, 5))
    for x in range(-20, WIDTH, 48):
        pygame.draw.line(background, (226, 226, 213), (x, FLOOR_Y + 24), (x - 30, HEIGHT), 1)
    return background


BACKGROUND = make_background()


def runner_position(time_seconds):
    if time_seconds < 2.55:
        return 80 + 178 * time_seconds
    if time_seconds < 3.35:
        return 534
    return min(1080, 534 + 190 * (time_seconds - 3.35))


def draw_runner(surface, time_seconds):
    x = runner_position(time_seconds)
    knocking = 2.55 <= time_seconds < 3.35
    stride = 0 if knocking else math.sin(time_seconds * 13)
    bob = 0 if knocking else abs(math.sin(time_seconds * 13)) * 3
    ground = FLOOR_Y - bob
    head_y = ground - 105

    pygame.draw.ellipse(surface, (188, 197, 187), (x - 17, FLOOR_Y - 3, 34, 8))
    pygame.draw.circle(surface, INK, (round(x), round(head_y)), 11)
    pygame.draw.circle(surface, ORANGE, (round(x + 3), round(head_y - 2)), 3)
    pygame.draw.line(surface, INK, (x, ground - 91), (x, ground - 49), 5)

    if knocking:
        pygame.draw.line(surface, ORANGE, (x, ground - 82), (600, ground - 82), 5)
        pygame.draw.line(surface, INK, (x, ground - 80), (x - 18, ground - 59), 4)
    else:
        arm_swing = stride * 12
        pygame.draw.line(surface, ORANGE, (x, ground - 81), (x - 18 - arm_swing, ground - 61), 5)
        pygame.draw.line(surface, ORANGE, (x, ground - 81), (x + 18 + arm_swing, ground - 61), 5)

    leg_swing = stride * 15
    pygame.draw.line(surface, INK, (x, ground - 49), (x - 12 - leg_swing, ground - 8), 5)
    pygame.draw.line(surface, INK, (x, ground - 49), (x + 12 + leg_swing, ground - 8), 5)
    pygame.draw.line(surface, ORANGE, (x - 12 - leg_swing, ground - 8), (x - 2 - leg_swing, ground - 8), 4)
    pygame.draw.line(surface, ORANGE, (x + 12 + leg_swing, ground - 8), (x + 22 + leg_swing, ground - 8), 4)


def draw_sign(surface, time_seconds):
    sign_x = 600
    sign_y = FLOOR_Y - 170
    pygame.draw.ellipse(surface, (181, 190, 181), (sign_x - 13, FLOOR_Y - 5, 54, 10))
    pygame.draw.rect(surface, INK, (sign_x - 4, sign_y + 10, 8, 160), border_radius=3)
    pygame.draw.rect(surface, INK, (sign_x - 30, sign_y, 68, 104), border_radius=8)
    pygame.draw.rect(surface, (226, 247, 236), (sign_x - 24, sign_y + 6, 56, 92), border_radius=5)

    knocking = 2.55 <= time_seconds < 3.35
    if knocking:
        pulse = 0.5 + 0.5 * math.sin(time_seconds * 22)
        color = (255, int(137 + pulse * 45), 54)
        label = "TAP!"
        pygame.draw.circle(surface, color, (sign_x + 3, sign_y + 48), 28, 3)
    else:
        color = MINT
        label = "KNOCK"
    text = SMALL_FONT.render(label, True, INK)
    surface.blit(text, text.get_rect(center=(sign_x + 3, sign_y + 50)))
    pygame.draw.circle(surface, color, (sign_x + 3, sign_y + 78), 5)


def draw_hammer(surface, time_seconds):
    if time_seconds < 4.05:
        return

    runner_x = runner_position(time_seconds)
    reveal = min(1, (time_seconds - 4.05) / 0.9)
    x = -180 + reveal * (runner_x - 200 + 180)
    if time_seconds > 4.95:
        x = runner_x - 200 + 15 * math.sin(time_seconds * 2)
    bounce = abs(math.sin((time_seconds - 4.05) * 5)) * 26
    y = FLOOR_Y - 135 - bounce

    hammer = pygame.Surface((170, 112), pygame.SRCALPHA)
    pygame.draw.roundrect(hammer, INK, (57, 39, 17, 69), border_radius=6)
    pygame.draw.roundrect(hammer, ORANGE, (60, 42, 11, 63), border_radius=5)
    pygame.draw.roundrect(hammer, INK, (13, 10, 112, 47), border_radius=9)
    pygame.draw.roundrect(hammer, (224, 235, 217), (18, 15, 102, 36), border_radius=6)
    label = SMALL_FONT.render("HAMMER", True, INK)
    hammer.blit(label, label.get_rect(center=(69, 33)))
    rotated = pygame.transform.rotate(hammer, math.sin(time_seconds * 5) * 8)
    surface.blit(rotated, rotated.get_rect(center=(round(x), round(y))))
    pygame.draw.ellipse(surface, (188, 197, 187), (x - 28, FLOOR_Y - 2, 56, 8))


def render_frame(frame_number):
    time_seconds = frame_number / FPS
    surface = pygame.Surface((WIDTH, HEIGHT))
    surface.blit(BACKGROUND, (0, 0))

    cloud_x = (time_seconds * 18) % (WIDTH + 130) - 100
    for offset, radius in ((0, 20), (24, 27), (54, 18)):
        pygame.draw.circle(surface, (236, 246, 237), (round(cloud_x + offset), 105), radius)

    title = SMALL_FONT.render("SIDE STREET  /  01", True, (54, 91, 99))
    surface.blit(title, (28, 24))
    draw_sign(surface, time_seconds)
    draw_hammer(surface, time_seconds)
    draw_runner(surface, time_seconds)

    if time_seconds > 7.9:
        fade = min(1, (time_seconds - 7.9) / 0.65)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((247, 246, 237, round(205 * fade)))
        surface.blit(overlay, (0, 0))
        end_text = TITLE_FONT.render("WELL, THAT ESCALATED.", True, INK)
        end_text.set_alpha(round(255 * fade))
        surface.blit(end_text, end_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    return surface


def export_video(output_path):
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame_number in range(FRAME_COUNT):
            frame = render_frame(frame_number)
            process.stdin.write(pygame.image.tostring(frame, "RGB"))
    except BrokenPipeError:
        process.wait()
        raise RuntimeError("FFmpeg stopped before the video finished rendering.")
    finally:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg could not encode the MP4.")
    print(f"Saved {output_path} ({FRAME_COUNT} frames, {DURATION:.1f}s)")


def play_animation():
    os.environ.pop("SDL_VIDEODRIVER", None)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Side Street | A tiny animation")
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        elapsed = ((pygame.time.get_ticks() - start_ticks) / 1000) % DURATION
        screen.blit(render_frame(round(elapsed * FPS) % FRAME_COUNT), (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="Play the animation or export it as an MP4.")
    parser.add_argument("--play", action="store_true", help="open the animation in a window")
    parser.add_argument("--output", default="animation.mp4", help="MP4 output path (default: animation.mp4)")
    args = parser.parse_args()

    if args.play:
        play_animation()
    else:
        export_video(args.output)
        pygame.quit()


if __name__ == "__main__":
    main()