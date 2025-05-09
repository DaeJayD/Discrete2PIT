import turtle
import time
import subprocess
import random
import math
import uvicorn

def wait_for_backend(url, timeout=10):
    """Wait for the backend to be ready"""
    for _ in range(timeout * 2):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    return False

def create_intro():
    # Set up turtle screen
    intro = turtle.Screen()
    intro.bgcolor('#F5F5DC')
    intro.setup(width=800, height=600)
    intro.title("Mega Lotto")
    intro.tracer(0)  

    # Create neon border
    border = turtle.Turtle()
    border.speed(0)
    border.color('yellow')
    border.pensize(5)
    border.penup()
    border.goto(-350, 250)
    border.pendown()
    for _ in range(2):
        border.forward(700)
        border.right(90)
        border.forward(500)
        border.right(90)
    border.hideturtle()

    # Create glowing title text
    title = turtle.Turtle()
    title.speed(0)
    title.color('dark blue')
    title.penup()
    title.goto(0, 100)
    title.write("MEGA LOTTO", align='center', font=('Arial', 48, 'bold'))
    title.hideturtle()

    circles = []
    colors = ['red', 'blue', 'gold',]
    for i in range(12):
        t = turtle.Turtle()
        t.shape('circle')
        t.shapesize(2)
        t.color(random.choice(colors))
        t.penup()
        angle = i * 30
        rad_angle = math.radians(angle) 
        t.goto(200 * math.cos(rad_angle), 200 * math.sin(rad_angle))
        circles.append(t)

    # Animation loop
    start_time = time.time()
    while time.time() - start_time < 3:  
        intro.update()
        
        # Pulsing circles
        for i, circle in enumerate(circles):
            size = 2 + abs(math.sin(time.time() * 2 + i)) * 2
            circle.shapesize(size)
            if random.random() > 2:
                circle.color(random.choice(colors))
        
        # Glowing title
        glow = abs(math.sin(time.time() * 3)) * 0.5 + 0.5
        title.color((glow, 0, glow))
        
        # Flickering border
        if random.random() > 0.9:
            border.color(random.choice(['cyan', 'white', 'blue']))
        else:
            border.color('cyan')

    intro.bye()
    print("Launching intro...")

if __name__ == "__main__":

    backend = subprocess.Popen(
        ["python", "-m", "uvicorn", "lotto_backend:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    create_intro()


    subprocess.run(["python", "lottofront.py"])
    backend.terminate()