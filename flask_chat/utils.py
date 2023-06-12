import random
from .models import Notification
from .app import db

def generate_light_color():
    # Generate a random hue
    hue = random.randint(0, 360)
    # Use a fixed saturation and lightness value to achieve a light color
    color = f'hsl({hue}, 70%, 85%)'
    return color

def notify_user(user, message):
    try:
        notification = Notification(user_id=user.id, message=message)
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        print(f"Failed to notify user {user.id}: {e}")
