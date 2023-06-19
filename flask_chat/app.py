import eventlet
eventlet.monkey_patch()
from celery import Celery
from flask import Flask, session, redirect, url_for, render_template
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from langchain import OpenAI, LLMChain, PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
import os


class Config:
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/0'
    SECRET_KEY = 'secret!'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///messages.db'
    session_cookie_secure = True

db = SQLAlchemy()
socketio = SocketIO()
# socketio = SocketIO(app, message_queue=Config.broker_url)

celery = Celery(__name__, broker=Config.broker_url, backend=Config.result_backend)


# Configuration and initialization code for OpenAI, prompt, chatgpt_chain, etc.
    
# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Define the template for the prompt
template = """Assistant is a large language model trained by OpenAI.
Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

{history}
Human: {human_input}
Assistant:"""

# Define the PromptTemplate
prompt = PromptTemplate(
    input_variables=["history", "human_input"],
    template=template
)

# Create the chatgpt_chain
chatgpt_chain = LLMChain(
    llm=OpenAI(temperature=0),
    prompt=prompt,
    verbose=True,
    memory=ConversationBufferWindowMemory(k=2),
)



global app
def create_app():
    global app
    # global socketio
    # global celery
    app = Flask(__name__)
    app.config.from_object(Config)
    login_manager = LoginManager(app)  # This line is essential
    # celery = make_celery(app)
    celery.conf.update(app.config)
    # socketio = SocketIO(message_queue='redis://')


    @app.route('/')
    def index():
        if 'username' in session:
            # The user is logged in, so redirect them to the chat page
            return redirect(url_for('chat.chat'))
        else:
            # The user is not logged in, so show the login page
            return render_template('index.html')
            
    db.init_app(app)
    # db = SQLAlchemy(app)
    socketio.init_app(app, message_queue=Config.broker_url)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User  # Import User model here to avoid circular import
        return User.query.get(user_id)

    # Import the routes and other components
    from .routes.auth import auth_blueprint
    from .routes.chat import chat_blueprint
    from .routes.rooms import rooms_blueprint

    # Register the blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(chat_blueprint, url_prefix='/chat')
    app.register_blueprint(rooms_blueprint, url_prefix='/rooms')
    
    with app.app_context():
        db.create_all()  # Create database tables for our data models
    
    print(id(app))
    return app
