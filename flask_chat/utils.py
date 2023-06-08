import random

def generate_light_color():
    # Generate a random hue
    hue = random.randint(0, 360)
    # Use a fixed saturation and lightness value to achieve a light color
    color = f'hsl({hue}, 70%, 85%)'
    return color