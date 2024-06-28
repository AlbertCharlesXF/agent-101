from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from ollama_agent import OllamaAgent
import uuid


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('ask_question')
def handle_question(data):
    user_id = str(uuid.uuid4())  # Generate a unique ID for each question
    question = data['input']
    model = data['model']
    
    print(f"Received question from {user_id}: {question}")
    print(f"Using model: {model}")
    
    get_ollama_ans(question, model)

def get_ollama_ans(question, model):
    sentiment_agent = OllamaAgent(model)
    messages = [{"role": "system", "content": "你应该尽可能详细地回答我的问题。"}]
    messages.append({"role": "user", "content": question})
    # ans = ""
    # for char in sentiment_agent.get_ollama_yield(messages, model):
    #     print(char, end="", flush=True)
    #     ans += char
    #     socketio.emit('question_answer', {'content': char})
    # socketio.emit('stream_end')
        
    for char in sentiment_agent.analyze_sentiment_yield(question, page=1):
        print(char, end="", flush=True)
        socketio.emit('question_answer', {'content': char})
    socketio.emit('stream_end')


if __name__ == '__main__':
    socketio.run(app, debug=True, port=3000)
    
    
'''

flask run --host=0.0.0.0 --port=3000

'''
