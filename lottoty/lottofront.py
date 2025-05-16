from tkinter import *
from PIL import Image, ImageTk
import requests
import random
import time
from tkinter import messagebox
from pygame import mixer
import json
from datetime import datetime
import turtle
import time
import random
import math  
from tkinter import Tk, messagebox


def send_draw_to_backend(drawn_numbers):
    try:
        response = requests.post(
            "http://127.0.0.1:8000/record/",
            json={"numbers": drawn_numbers},
            timeout=3
        )
        if response.status_code != 201:
            print(f"Backend returned status {response.status_code}")
    except Exception as e:
        print(f"Failed to send draw to backend: {e}")


mixer.init()
try:
    button_press_sound = mixer.Sound("click.ogg")
    button_click_sound = mixer.Sound("press.wav")  
except:
    print("Warning: Could not load sound files")

window = Tk()
window.title('Mega Lotto')

try:
    icon_image = PhotoImage(file="image.png")
    window.iconphoto(True, icon_image)  
    
    display_image = PhotoImage(file="img.png") 
    image_label = Label(window, image=display_image)
    image_label.image = display_image 
    image_label.place(x=100, y=100)  
except Exception as e:
    print("")

window.config(bg="black")
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
window.geometry(f"{screen_width}x{screen_height}")
window.resizable(False, False)


try:

    main_bg_gif = Image.open("background.gif")
    main_gif_frames = []
    
    for frame in range(main_bg_gif.n_frames):
        main_bg_gif.seek(frame)
        frame_img = main_bg_gif.copy().resize((screen_width, screen_height), Image.LANCZOS)
        main_gif_frames.append(ImageTk.PhotoImage(frame_img))
    
    main_bg_label = Label(window)
    main_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    
    def animate_main_bg(frame_num=0):
        frame = main_gif_frames[frame_num % len(main_gif_frames)]
        main_bg_label.config(image=frame)
        window.after(main_bg_gif.info['duration'], animate_main_bg, frame_num + 1)
    
    animate_main_bg()
    
    # Store references
    window.main_gif_frames = main_gif_frames
    window.main_bg_gif = main_bg_gif

except Exception as e:
    print(f"Error loading main GIF background: {e}")
    try:
        # Fallback to static image
        bg_image_pil = Image.open("img.png")
        bg_image_resized = bg_image_pil.resize((screen_width, screen_height), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(bg_image_resized)
        bg_label = Label(window, image=bg_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = bg_image
    except Exception as e:
        print(f"Error loading static image: {e}")
        bg_label = Label(window, bg="black")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)


history = []
HISTORY_FILE = "lottery_history.json"
def update_sample_size():
    try:
        # Create popup window
        popup = Toplevel(window)
        popup.title("Set Sample Size")
        popup.geometry("300x150")
        popup.resizable(False, False)
        popup.config(bg="black")
        
        # Try to load GIF background
        try:
            gif = Image.open("popup_bg.gif")
            frames = []
            for frame in range(gif.n_frames):
                gif.seek(frame)
                frames.append(ImageTk.PhotoImage(gif.copy().resize((300, 150), Image.LANCZOS)))
            
            bg_label = Label(popup)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            def animate(frame_num=0):
                frame = frames[frame_num % len(frames)]
                bg_label.config(image=frame)
                popup.after(100, animate, frame_num + 1)
            
            animate()
            popup.frames = frames
        except:
            popup.config(bg="#8B0000")

        Label(popup, 
              text="Enter Sample Size:",
              font=("Impact", 12),
              fg="#FFD700",
              bg="black").pack(pady=10)

        entry = Entry(popup, 
                     font=("Courier", 14),
                     justify=CENTER,
                     bd=3,
                     relief=SUNKEN)
        entry.pack(pady=5)
        entry.focus_set()

        def submit():
            try:
                size = int(entry.get())
                if size < 1:
                    messagebox.showerror("Error", "Sample size must be at least 1")
                    return
                
                # Send to backend
                response = requests.post(
                    "http://127.0.0.1:8000/config/",
                    json={"sample_size": size},
                    timeout=3
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Success", f"Sample size updated to {size}")
                    popup.destroy()
                else:
                    messagebox.showerror("Error", f"Backend returned status {response.status_code}")
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update sample size: {str(e)}")

        Button(popup,
               text="Submit",
               command=submit,
               font=("Impact", 10),
               fg="#FFD700",
               bg="#8B0000",
               bd=3,
               relief=RAISED).pack(pady=5)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to create sample size dialog: {str(e)}")

sample_button = Button(
    window,
    text="Set Sample Size",
    command=update_sample_size,
    font=("Impact", 12),
    fg="#FFD700",
    bg="#8B0000",
    bd=3,
    relief=RAISED
)
sample_button.place(x=100, y=470, width=200, height=40)  # Position below your frequency button

def press_sample():
    try:
        button_press_sound.play()
    except:
        print("Could not play button sound")
    update_sample_size()

sample_button.config(command=press_sample)


def load_history():
    global history
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    except:
        history = []

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

history_frame = Frame(window, bd=3, relief=RAISED)
history_frame.place(x=50, y=100, width=300, height=300)

try:
    history_gif = Image.open("history_bg.gif")  
    history_gif_frames = []
    
    for frame in range(history_gif.n_frames):
        history_gif.seek(frame)
        frame_img = history_gif.copy().resize((300, 300), Image.LANCZOS)
        history_gif_frames.append(ImageTk.PhotoImage(frame_img))
    
    history_bg_label = Label(history_frame)
    history_bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    
    def animate_history_bg(frame_num=0):
        frame = history_gif_frames[frame_num % len(history_gif_frames)]
        history_bg_label.config(image=frame)
        history_frame.after(100, animate_history_bg, frame_num + 1)
    
    animate_history_bg()
    
    # Store references
    history_frame.gif_frames = history_gif_frames
    
except Exception as e:
    print(f"History GIF error: {e}")
    history_frame.config(bg="#8B0000")

history_label = Label(
    history_frame, 
    text="Recent Combinations:",
    font=("Impact", 14),
    fg="#FFD700",
    bg="black", 
    bd=0
)
history_label.pack(pady=5)

history_text = Text(
    history_frame,
    font=("Courier", 12),
    fg="#FFD700",
    bg="black", 
    width=30,
    height=12,
    state=DISABLED,
    highlightthickness=0,
    bd=0
)
history_text.pack(pady=5)

def update_history_display():
    history_text.config(state=NORMAL)
    history_text.delete(1.0, END)
    for combo in history[-10:]:  # Show last 10 combinations
        history_text.insert(END, " ".join(map(str, combo)) + "\n")
    history_text.config(state=DISABLED)

def press():
    try:
        button_press_sound.play()
    except:
        print("Could not play button sound")
    show_frequencies()  

freq_button = Button(
    window,
    text="Show Frequencies",
    command=press,  # Use the new function that includes the sound
    font=("Impact", 12),
    fg="#FFD700",
    bg="#8B0000",
    bd=3,
    relief=RAISED
)
freq_button.place(x=100, y=420, width=200, height=40)

def show_frequencies():
    try:
        response = requests.get("http://127.0.0.1:8000/lucky_numbers/")
        if response.status_code != 200:
            messagebox.showerror("Error", "Failed to get lucky number data")
            return

        data = response.json()
        numbers = data.get("numbers", [])
        frequencies = data.get("frequencies", {})
        
        # Create frequency window
        freq_window = Toplevel(window)
        freq_window.title("Number Frequencies")
        freq_window.geometry("800x640")
        freq_window.resizable(False, False)
        freq_window.config(bg="black")

        try:
            # Load animated GIF
            gif = Image.open("animated_bg.gif")
            frames = []
            
            for frame in range(gif.n_frames):
                gif.seek(frame)
                frames.append(ImageTk.PhotoImage(gif.copy().resize((800, 640), Image.LANCZOS)))
            
            bg_label = Label(freq_window, bg="black")
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            def update_gif(frame_num=0):
                frame = frames[frame_num]
                bg_label.config(image=frame)
                next_frame = (frame_num + 1) % len(frames)
                freq_window.after(100, update_gif, next_frame)
            
            update_gif()
            freq_window.frames = frames
            
        except Exception as e:
            print(f"GIF error: {e}")


        content_frame = Frame(freq_window, bg="black")
        content_frame.place(relx=0.5, rely=0.5, anchor=CENTER, width=580, height=320)


        Label(content_frame, 
              text="NUMBER FREQUENCIES",
              font=("Impact", 16),
              fg="#FFD700",
              bg="black").pack(pady=15)

        # Create canvas with dark scrollbar
        canvas = Canvas(content_frame, bg="black", highlightthickness=0)
        
        # Custom dark scrollbar
        scrollbar = Scrollbar(content_frame, 
                             orient=VERTICAL, 
                             command=canvas.yview,
                             bg="black",
                             troughcolor="#121212",
                             activebackground="#333333")
        
        inner_frame = Frame(canvas, bg="black")

        canvas.create_window((0, 0), window=inner_frame, anchor=NW)
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)
        
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # Display numbers
        for num in sorted(numbers):
            frame = Frame(inner_frame, bg="black")
            frame.pack(fill=X, pady=6, padx=15)

            count = frequencies.get(str(num), 0)
            bar_length = min(count * 2, 350)

            Label(frame,
                  text=f"{num:02d}",
                  font=("Courier", 14, "bold"),
                  fg="#FFD700",
                  bg="black",
                  width=4).pack(side=LEFT)

            Frame(frame, bg="#dba42c", width=bar_length, height=25).pack(side=LEFT, padx=8)

            Label(frame,
                  text=f"{count} appearances",
                  font=("Courier", 12),
                  fg="white",
                  bg="black").pack(side=LEFT)
                  
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load frequency data: {str(e)}")

def click():
    try:
        button_click_sound.play()
    except:
        print("Could not play Button sound")

    animate_numbers()

def create_slot_lever(parent, click_func):
    # Create canvas
    canvas = Canvas(
        parent,
        width=85,
        height=175,
        bg="#b46c6c",
        highlightthickness=0
    )
    canvas.place(x=1252, y=425)

\
    state = {
        'base_x': 50,
        'base_y': 200,
        'lever_length': 120,
        'angle': 0,
        'is_pulling': False
    }

    # Draw lever components
    canvas.create_oval(
        state['base_x']-20, state['base_y']-20,
        state['base_x']+20, state['base_y']+20,
        fill="#C0C0C0", outline="#FFD700", width=2
    )
    
    lever = canvas.create_line(
        state['base_x'], state['base_y'],
        state['base_x'], state['base_y'] - state['lever_length'],
        width=10, fill="#D4AF37", capstyle=ROUND
    )
    
    handle = canvas.create_oval(
        state['base_x']-15, state['base_y']-state['lever_length']-15,
        state['base_x']+15, state['base_y']-state['lever_length']+15,
        fill="#8B0000", outline="#FF0000"
    )

    def update_position():
        rad = math.radians(state['angle'])
        end_x = state['base_x'] + state['lever_length'] * math.sin(rad)
        end_y = state['base_y'] - state['lever_length'] * math.cos(rad)
        canvas.coords(lever, state['base_x'], state['base_y'], end_x, end_y)
        canvas.coords(handle, end_x-15, end_y-15, end_x+15, end_y+15)

    def animate_up():
        if state['angle'] > 0:
            state['angle'] -= 5
            update_position()
            canvas.after(20, animate_up)
        else:
            state['is_pulling'] = False
            click_func()  # Execute the passed click function

    def animate_down():
        if state['angle'] < 45:
            state['angle'] += 3
            update_position()
            canvas.after(20, animate_down)
        else:
            canvas.after(300, animate_up)

    def pull(event=None):
        if not state['is_pulling']:
            try:
                button_click_sound.play()
            except:
                pass
            state['is_pulling'] = True
            animate_down()

    # Make clickable
    canvas.create_rectangle(0, 0, 100, 250, outline="", fill="", tags="clickable")
    canvas.tag_bind("clickable", "<Button-1>", pull)

    # Store references to prevent garbage collection
    if not hasattr(parent, '_lever_objects'):
        parent._lever_objects = []
    parent._lever_objects.append((canvas, lever, handle))

# Create the lever by calling the function
create_slot_lever(window, click)

def create_pull_me_text():
    try:
        
        pull_me_canvas = Canvas(
            window,
            width=60,
            height=180,
            bg="#b46c6c",
            highlightthickness=0
        )
        pull_me_canvas.place(x=1320, y=425)  


        vertical_text = "P U L L  M E"
        y_position = 20
        
        for char in vertical_text:
            if char != ' ':  
                
                pull_me_canvas.create_text(
                    32, y_position,
                    text=char,
                    font=("Impact", 18, "bold"),
                    fill="#8B0000",
                    angle=0
                )
                # Main text
                pull_me_canvas.create_text(
                    30, y_position,
                    text=char,
                    font=("Impact", 18, "bold"),
                    fill="#FFD700",
                    angle=0
                )
            y_position += 22  


        arrow = pull_me_canvas.create_line(
            50, 90,  
            20, 90,  
            arrow=LAST, 
            width=3,
            fill="#FF0000",
            arrowshape=(8, 10, 5),  
            tags="arrow"
        )


        def animate_arrow():

            x1, y1, x2, y2 = pull_me_canvas.coords(arrow)
            if x2 > 25:  # Extend left
                pull_me_canvas.coords(arrow, x1, y1, x2-2, y2)
            else:  # Snap back
                pull_me_canvas.coords(arrow, x1, y1, 30, y2)
            

            current_color = pull_me_canvas.itemcget(arrow, "fill")
            new_color = "#FFD700" if current_color == "#FF0000" else "#FF0000"
            pull_me_canvas.itemconfig(arrow, fill=new_color)
            
            window.after(150, animate_arrow)

        animate_arrow()

        if not hasattr(window, 'canvas_elements'):
            window.canvas_elements = []
        window.canvas_elements.append(pull_me_canvas)

    except Exception as e:
        print(f"Error creating pull me text: {e}")
        # Fallback
        pull_me_label = Label(
            window,
            text="PULL\nME",
            font=("Impact", 18, "bold"),
            fg="#FFD700",
            bg="#b46c6c"
        )
        pull_me_label.place(x=1380, y=425)


create_pull_me_text()

def animate_numbers():
    freq_button.config(state=DISABLED)

    # Initialize sounds
    global spin_channel, flash_sound
    try:
        spin_sound = mixer.Sound("spin_loop.wav")
        flash_sound = mixer.Sound("flash.wav")
        spin_channel = mixer.Channel(1)
    except Exception as e:
        print(f"Sound initialization error: {e}")

    # Start spinning sound
    if spin_channel:
        spin_channel.play(spin_sound, loops=-1)
    
    # Reset all labels to ?
    for label in labels:
        label.config(text="?", fg="green", bg="#F5F5DC")
    window.update()

    spin_duration = 2
    stop_intervals = [200, 225, 250, 275, 300, 325]

    # Get final numbers FIRST before animation starts
    final_numbers = get_final_values()
    print("Final numbers from API:", final_numbers)  # Debug print

    def spin_reel(reel_index):
        start_time = time.time()
        end_time = start_time + spin_duration + (stop_intervals[reel_index]/1000)
        
        def update():
            if time.time() < end_time:
                # Alternate between ? and ₱ during spin
                current_text = labels[reel_index].cget("text")
                new_text = "₱" if current_text == "?" else "?"
                labels[reel_index].config(text=new_text)
                window.update()
                elapsed = time.time() - start_time
                progress = min(elapsed/(end_time - start_time), 1.0)
                delay = 50 + int(50 * progress)
                window.after(delay, update)
            else:
                # Show final number when reel stops
                labels[reel_index].config(text=str(final_numbers[reel_index]))
        
        update()

    # Start spinning all reels
    for i in range(6):
        window.after(stop_intervals[i], spin_reel, i)

    def update_reels():
        # Stop sounds
        try:
            if spin_channel:
                spin_channel.stop()
            if flash_sound:
                flash_sound.play()
        except Exception as e:
            print(f"Sound error: {e}")

        # Update history and frequencies
        history.append(final_numbers)
        for num in final_numbers:
            frequency_data[num] = frequency_data.get(num, 0) + 1
        
        save_history()
        save_frequencies()
        update_history_display()
        
        # Flash animation
        def flash(remaining=4):
            if remaining > 0:
                current_fg = labels[0].cget("fg")
                new_color = "#FF0000" if current_fg == "#FFD700" else "#FFD700"
                for label in labels:
                    label.config(fg=new_color)
                window.after(300, flash, remaining - 1)
            else:
                for label in labels:
                    label.config(fg="#FF0000")
                freq_button.config(state=NORMAL)
        
        flash()

    # Schedule the final update
    window.after(int(spin_duration * 1000) + max(stop_intervals), update_reels)

def get_final_values():
    try:
        response = requests.get("http://127.0.0.1:8000/biased_spin/", timeout=3)
        if response.status_code == 200:
            data = response.json()
            # Updated to match your API's response structure
            numbers = data.get('numbers', [])
            if len(numbers) == 6 and all(isinstance(n, int) and 1 <= n <= 45 for n in numbers):
                # Send the draw to your backend
                send_draw_to_backend(numbers)
                return numbers
    except Exception as e:
        print(f"API error: {e}")
    
    # Fallback: Generate 6 unique numbers between 1-45
    fallback_numbers = sorted(random.sample(range(1, 46), 6))
    send_draw_to_backend(fallback_numbers)
    return fallback_numbers

    
frequency_data = {num: 0 for num in range(1, 46)}  # Tracks counts for numbers 1-45
FREQUENCY_FILE = "number_frequencies.json"

def load_frequencies():
    global frequency_data
    try:
        with open(FREQUENCY_FILE, "r") as f:
            loaded = json.load(f)
            # Handle both string and integer keys
            frequency_data = {int(k): v for k, v in loaded.items()}
    except:
        frequency_data = {num: 0 for num in range(1, 46)}

def save_frequencies():
    with open(FREQUENCY_FILE, "w") as f:
        json.dump(frequency_data, f)


frame = Frame(window, bg="#FFD700")
frame.place(relx=0.505, rely=0.60, anchor=CENTER)
for i in range(6):
    frame.grid_columnconfigure(i, weight=1, uniform="equal")

labels = []
for i in range(6):
    label = Label(
        frame,
        text="₱",
        fg="green",
        font=("impact", 20, 'bold'),
        width=5,
        height=2,
        bg="#F5F5DC",
    )
    label.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
    labels.append(label)

# Load initial history
load_history()
load_frequencies()
update_history_display()

window.mainloop()
