import pyMeow as pm
import ctypes
import os
import math
import tkinter as tk
from tkinter import ttk
import threading
import sys

process = pm.open_process("gmod.exe")
client = pm.get_module(process, "client.dll")
engine = pm.get_module(process, "engine.dll")

# Offsets
LocalPlayer = 0x9461C0
EntityList = 0x968158
ViewMatrix = 0x7C1568
Position = 0x308
Health = 0xC8
PlayerName = 0x3744

# Colors
white = pm.get_color("white")
green = pm.get_color("green")
blue = pm.get_color("blue")
red = pm.get_color("red")
black = pm.get_color("black")
yellow = pm.get_color("yellow")

settings = {
    "esp_box": True,
    "esp_line": True,
    "esp_health": True,
    "box_color": "red",
    "line_color": "red",
    "health_color": "red"
}

color_options = ["red", "green", "blue", "yellow", "white"]

running = True  

def get_color_from_name(name):
    colors = {
        "red": pm.get_color("red"),
        "green": pm.get_color("green"),
        "blue": pm.get_color("blue"),
        "yellow": pm.get_color("yellow"),
        "white": pm.get_color("white")
    }
    return colors.get(name, pm.get_color("white"))

def create_menu():
    global running
    
    def on_closing():
        global running
        running = False
        root.destroy()
    
    root = tk.Tk()
    root.title("Well.cc Gmod x64")
    root.geometry("300x300")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    style = ttk.Style()
    style.configure('TCheckbutton', font=('Arial', 10))
    style.configure('TLabel', font=('Arial', 12, 'bold'))
    style.configure('TCombobox', font=('Arial', 10))
    
    ttk.Label(root, text="Gmod", style='TLabel').pack(pady=5)
    
    box_var = tk.BooleanVar(value=settings["esp_box"])
    line_var = tk.BooleanVar(value=settings["esp_line"])
    health_var = tk.BooleanVar(value=settings["esp_health"])
    
    def update_settings():
        settings["esp_box"] = box_var.get()
        settings["esp_line"] = line_var.get()
        settings["esp_health"] = health_var.get()
        settings["box_color"] = box_color_combo.get()
        settings["line_color"] = line_color_combo.get()
        settings["health_color"] = health_color_combo.get()
    
    ttk.Checkbutton(root, text="ESP Box", variable=box_var, command=update_settings, style='TCheckbutton').pack(pady=2)
    ttk.Checkbutton(root, text="ESP Line", variable=line_var, command=update_settings, style='TCheckbutton').pack(pady=2)
    ttk.Checkbutton(root, text="ESP Health", variable=health_var, command=update_settings, style='TCheckbutton').pack(pady=2)
    
    ttk.Label(root, text="Box Color:").pack(pady=(10, 0))
    box_color_combo = ttk.Combobox(root, values=color_options, state="readonly")
    box_color_combo.set(settings["box_color"])
    box_color_combo.pack()
    box_color_combo.bind("<<ComboboxSelected>>", lambda e: update_settings())
    
    ttk.Label(root, text="Line Color:").pack(pady=(5, 0))
    line_color_combo = ttk.Combobox(root, values=color_options, state="readonly")
    line_color_combo.set(settings["line_color"])
    line_color_combo.pack()
    line_color_combo.bind("<<ComboboxSelected>>", lambda e: update_settings())
    
    ttk.Label(root, text="Health Color:").pack(pady=(5, 0))
    health_color_combo = ttk.Combobox(root, values=color_options, state="readonly")
    health_color_combo.set(settings["health_color"])
    health_color_combo.pack()
    health_color_combo.bind("<<ComboboxSelected>>", lambda e: update_settings())
        
    root.mainloop()

def main():
    global running
    
    if not pm.process_exists("gmod.exe"):
        print("Game not found")
        return

    menu_thread = threading.Thread(target=create_menu, daemon=True)
    menu_thread.start()

    pm.overlay_init("Garry's Mod (x64)", fps=120)
    
    while running and pm.overlay_loop():
        pm.begin_drawing()
        pm.draw_fps(10, 50)
        pm.draw_text(f"Well.cc Gmod x64", 12, 11, 24, white)        
        try:
            local = pm.r_int64(process, client["base"] + LocalPlayer)
            if not local:
                continue
                
            view_matrix = pm.r_floats(process, pm.r_int64(process, engine["base"] + ViewMatrix) + 0x2D4, 16)
            
            screen_width = pm.get_screen_width()
            screen_height = pm.get_screen_height()
            top_center = pm.vec2(screen_width // 2, 0)  
            top_right = pm.vec2(screen_width, 0)   

            for i in range(1, 64):  
                entity_addr = pm.r_int64(process, client["base"] + EntityList + i * 0x10)
                if not entity_addr or entity_addr == local:
                    continue
                    
                try:
                    health = pm.r_int(process, entity_addr + Health)
                    if health <= 0:
                        continue
                        
                    pos = pm.r_vec3(process, entity_addr + Position)
                    wts = pm.world_to_screen(view_matrix, pos, 1)
                    if not wts:
                        continue
                        
                    try:
                        name = pm.r_string(process, entity_addr + PlayerName)
                        color = get_color_from_name(settings["box_color"])
                    except:
                        color = blue

                    distance = pm.vec3_distance(pm.r_vec3(process, local + Position), pos)
                    box_size = 15000 / distance
                    
                    if settings["esp_box"]:
                        pm.draw_rectangle_lines(
                            wts["x"] - box_size/2, 
                            wts["y"] - box_size * 2.5, 
                            box_size, 
                            box_size * 2.5, 
                            color
                        )
                    
                    if settings["esp_line"]:
                        pm.draw_line(
                                top_right["x"], top_right["y"],     
                                wts["x"], wts["y"] - box_size * 2.5,  
                                get_color_from_name(settings["line_color"])
                            )
                            
                    if settings["esp_health"]:
                        hp_percent = health / 100.0  
                        hp_angle = 360 * hp_percent
                        hp_radius = box_size / 3 + 2
                        
                        pm.draw_circle_sector(
                            centerX=wts["x"],
                            centerY=wts["y"] - box_size * 2.5 - hp_radius,
                            radius=hp_radius,
                            startAngle=0,
                            endAngle=360,
                            segments=0,
                            color=black
                        )
                        
                        hp_color = get_color_from_name(settings["health_color"])
                        
                        pm.draw_circle_sector(
                            centerX=wts["x"],
                            centerY=wts["y"] - box_size * 2.5 - hp_radius,
                            radius=hp_radius - 1,
                            startAngle=-90, 
                            endAngle=-90 + hp_angle,
                            segments=0,
                            color=hp_color
                        )
                    
                except:
                    continue
                    
        except Exception as e:
            print(f"Error: {e}")
            continue
            
        pm.end_drawing()
    
    pm.overlay_close()

if __name__ == "__main__":
    main()