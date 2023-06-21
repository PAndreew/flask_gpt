#from flask import current_app
from flask_socketio import SocketIO
from .models import Message
from .app import db, celery, app, Config, socketio
from .aimodels import AIModelManager, ai_model_colors
from .utils import upload_to_server


@celery.task()
def generate_ai_response(model_name, user_input):
    with app.app_context():
        aimodel_manager = AIModelManager(model_name)
        response = aimodel_manager.generate_response(user_input)
        return response


@celery.task()
def process_response(response, room_id, model_name):
    ai_color = ai_model_colors.get(model_name, '#111111')

    if response["type"] == "text":
        ai_output = response["content"]
        media_url = None
        media_type = None
    elif response["type"] == "image":
        ai_output = "AI has generated an image."
        media_url = upload_to_server(response["content"])
        media_type = "image"
    else:
        # Add more types if necessary
        return

    with app.app_context():
        # Save the AI's response
        ai_response = Message(
            text=ai_output, 
            aimodel_name=model_name, 
            user_id=None, 
            room_id=room_id, 
            message_color=ai_color,
            media_url=media_url, 
            media_type=media_type 
        )

        db.session.add(ai_response)
        db.session.commit()

    with app.test_request_context():
        # Broadcast the AI's response to all clients in the room
        socketio.emit('message', {
            'msg': ai_output, 
            'sender': 'ai', 
            'color': ai_color,
            'media_url': media_url,
            'media_type': media_type
        }, room=room_id)

