VERSION = "v1.0"

import pygame
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

root = tk.Tk()
root.withdraw()

CHART = {
    "meta": {
        "bpm": 150,
        "music": None,
        "scroll_speed": 3
    },
    "actions": []
}

def read_chart(name):
    if not name:
        return

    with open(name) as f:
        lines = f.readlines()
    
    meta = lines[0].split()
    meta[0], meta[2] = float(meta[0]), float(meta[2])
    keys = ["bpm", "music", "scroll_speed"]
    CHART["meta"].update(zip(keys, meta))

    CHART["actions"].clear()
    for i in range(1, len(lines)):
        cols = lines[i].split()
        if len(cols) <= 4:
            continue

        time = float(cols[0])
        event = int(cols[1])
        player = int(cols[2])
        lane = int(cols[3])
        note_type = int(cols[4])

        action = {
            "time": time,
            "event": event,
            "player": player,
            "lane": lane,
            "type": note_type,
        }
        if note_type == 1:
            action["length"] = float(cols[5] if len(cols) > 5 else 0)

        CHART["actions"].append(action)

def write_chart(name):
    if not name:
        return

    keys = ["bpm", "music", "scroll_speed"]
    meta_values = [str(CHART["meta"].get(key, "")) for key in keys]

    with open(name, "w") as f:
        f.write(" ".join(meta_values) + "\n")

        for action in sorted(CHART["actions"], key=lambda a: (
            float(a.get("time", 0)),
            int(a.get("lane", 0)),
            int(a.get("player", 0))
        )):
            action_keys = ["time", "event", "player", "lane", "type"]
            if action.get("type") == 1:
                action_keys.append("length")
            values = [str(action.get(key, "")) for key in action_keys]
            f.write(" ".join(values) + "\n")

savefile = None
unsaved = False

scroll = 0
zoom = 150
step = 4
note_type = 0

class Color:
    BACKGROUND = (0, 0, 0)
    GUIDELINE = (50, 50, 50)
    STEP = (100, 100, 100)
    BEAT = (150, 150, 150)
    NOTES = [
        (255, 0, 255),
        (0, 255, 255),
        (0, 255, 0),
        (255, 0, 0),
        (0, 0, 0)
    ]

def frange(start, end=None, step=1.0):
    if end is None:
        end = start
        start = 0.0

    i = start
    while i < end:
        yield i
        i += step

def get_action_at_mouse():
    pos = pygame.mouse.get_pos()

    if not (pos[0] < 200 or 250 <= pos[0] < 450):
        return None

    bx = pos[0] // 50
    step_width = zoom / step
    by = round((pos[1] + scroll) / step_width)

    time = by / step
    player, lane = divmod(bx, 5)

    return next(
        (
            a for a in CHART["actions"]
            if a["time"] == time
            and a.get("player", -1) == player
            and a.get("lane", -1) == lane
        ),
        None
    )

def tick(dt: float):
    for event in pygame.event.get():
        global unsaved
        if event.type == pygame.QUIT:
            global running
            if unsaved:
                try:
                    if messagebox.askyesno(
                        "Quit", "You have unsaved changes. Quit without saving?", icon='warning'
                    ):
                        running = False
                except: pass
            else:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            global scroll
            global zoom
            global step
            global note_type
            if event.button == 4:  # wheel up
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    mouse_y = event.pos[1]
                    old_zoom = zoom
                    zoom = min(300, zoom * 1.1)
                    scroll = max(0, zoom * (mouse_y + scroll) / old_zoom - mouse_y)
                else:
                    scroll = max(0, scroll - 25)
            elif event.button == 5:  # wheel down
                if pygame.key.get_mods() & pygame.KMOD_CTRL:
                    mouse_y = event.pos[1]
                    old_zoom = zoom
                    zoom = max(30, zoom / 1.1)
                    scroll = max(0, zoom * (mouse_y + scroll) / old_zoom - mouse_y)
                else:
                    scroll += 25
            elif event.button == 1:  # left click -> add action
                action = get_action_at_mouse()
                if not action:
                    pos = pygame.mouse.get_pos()
                    if (pos[0] < 200 or 250 <= pos[0] < 450):
                        bx = pos[0] // 50
                        step_width = zoom / step
                        by = round((pos[1] + scroll) / step_width)
                        time = by / step
                        player, lane = divmod(bx, 5)
                        action = {
                            "time": time,
                            "event": 0,
                            "player": player,
                            "lane": lane,
                            "type": note_type
                        }
                        if note_type == 1:
                            action["length"] = 1
                        CHART["actions"].append(action)
                        unsaved = True
            elif event.button == 3:  # right click -> remove action
                action = get_action_at_mouse()
                if action:
                    CHART["actions"].remove(action)
                    unsaved = True
        elif event.type == pygame.KEYDOWN:
            global savefile
            if event.key == pygame.K_s and event.mod & pygame.KMOD_CTRL:
                if savefile:
                    file = savefile
                else:
                    file = filedialog.asksaveasfilename(
                        title="Save chart",
                        defaultextension=".txt",
                        filetypes=[
                            ("Scratch lists", "*.txt"),
                            ("All files", "*.*")
                        ]
                    )
                if file:
                    write_chart(file)
                    unsaved = False
                    savefile = file
            elif event.key == pygame.K_o and event.mod & pygame.KMOD_CTRL:
                file = filedialog.askopenfilename(
                    title="Open chart",
                    filetypes=[
                        ("Scratch lists", "*.txt"),
                        ("All files", "*.*")
                    ]
                )
                if file:
                    read_chart(file)
                    unsaved = False
                    savefile = file
            elif event.key == pygame.K_DOWN:
                action = get_action_at_mouse()
                if action:
                    if "length" in action:
                        action["length"] += 1 / step
                        unsaved = True
            elif event.key == pygame.K_UP:
                action = get_action_at_mouse()
                if action:
                    if "length" in action:
                        action["length"] = max(0, action["length"] - 1 / step)
                        unsaved = True
            elif event.key == pygame.K_LEFTBRACKET:
                step = max(1, step - 1)
            elif event.key == pygame.K_RIGHTBRACKET:
                step += 1
            elif event.key == pygame.K_MINUS:
                note_type = max(0, note_type - 1)
                print(note_type)
            elif event.key == pygame.K_EQUALS:
                note_type = min(1, note_type + 1)
                print(note_type)

def render(screen: pygame.Surface):
    screen.fill(Color.BACKGROUND)

    for x in [
        0, 50, 100, 150, 200,
        250, 300, 350, 400, 450
    ]:
        pygame.draw.line(screen, Color.GUIDELINE, (x, 0), (x, 600), 3)

    step_width = zoom / step
    offset = scroll % step_width
    for y in frange(-offset, 600, step_width):
        pygame.draw.line(screen, Color.STEP, (0, int(y)), (200, int(y)), 3)
        pygame.draw.line(screen, Color.STEP, (250, int(y)), (450, int(y)), 3)

    beat_width = zoom
    offset = scroll % beat_width
    for y in frange(-offset, 600, beat_width):
        pygame.draw.line(screen, Color.BEAT, (0, int(y)), (200, int(y)), 3)
        pygame.draw.line(screen, Color.BEAT, (250, int(y)), (450, int(y)), 3)

    time_start = scroll / zoom
    time_end = (scroll + 600) / zoom
    for a in CHART["actions"]:
        if a["time"] + a.get("length", 0) < time_start or a["time"] >= time_end:
            continue
        if a["event"] == 1:
            continue
        bx = a["player"] * 5 + a["lane"]
        by = a["time"]
        x = int(bx * 50)
        y = int(by * zoom - scroll)
        if a["type"] == 0:
            note_surf = pygame.Surface((31, 5), pygame.SRCALPHA)
            color = Color.NOTES[a["lane"]]
            note_surf.fill(color)
            screen.blit(note_surf, (x + 10, y - 2))
        elif a["type"] == 1:
            height = int(3 + a["length"] * zoom)
            note_surf = pygame.Surface((31, max(5, height)), pygame.SRCALPHA)
            color = Color.NOTES[a["lane"]]
            note_surf.fill(color, (0, 0, 31, 5))
            note_surf.fill(color, (14, 0, 5, height))
            screen.blit(note_surf, (x + 10, y - 2))

    pos = pygame.mouse.get_pos()
    if pos[0] < 200 or (pos[0] >= 250 and pos[0] < 450):
        bx = pos[0] // 50
        by = round((pos[1] + scroll) / step_width)
        x = int(bx * 50)
        y = int((by / step) * zoom - scroll)
        hover_surf = pygame.Surface((31, 5), pygame.SRCALPHA)
        color = Color.NOTES[bx % 5]
        color = (*color[:3], 128)
        hover_surf.fill(color)
        screen.blit(hover_surf, (x + 10, y - 2))

    pygame.display.flip()

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption(f"TFE Editor {VERSION}")
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(60) / 1000
    tick(dt)
    render(screen)

pygame.quit()
root.destroy()
sys.exit()