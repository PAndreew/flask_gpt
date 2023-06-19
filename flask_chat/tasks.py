#from flask import current_app
from flask_socketio import SocketIO
from .models import Message
from .app import db, celery, app, Config, socketio
from .aimodels import AIModelManager, ai_model_colors


@celery.task()
def generate_ai_response(model_name, msg, room_id):
    aimodel_manager = AIModelManager(model_name)
    ai_output = aimodel_manager.generate_response(msg)
    ai_color = ai_model_colors.get(model_name, '#111111')
    socketio = SocketIO(message_queue=Config.broker_url, logger=True, engineio_logger=True)
    
    if ai_output:
        # app = current_app._get_current_object()
        with app.app_context():
            # Save the AI's response
            ai_response = Message(
                text=ai_output, 
                aimodel_name=aimodel_manager.current_model_name, 
                user_id=None, 
                room_id=room_id, 
                message_color=ai_color
            )  # No user_id for AI responses

            db.session.add(ai_response)
            db.session.commit()

        with app.test_request_context():
            # Broadcast the AI's response to all clients in the room
            socketio.emit('message', {'msg': 'Assistant: ' + ai_output, 'sender': 'ai', 'color': ai_color}, room=room_id)

