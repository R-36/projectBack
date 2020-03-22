from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit, join_room, leave_room
import uuid

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://xowmwjmfoeodaa:f3314bbaaf7d787f03149e86c4d23cdc531e12e2b717716c0' \
                                        'b391d3ea6ef79fd@ec2-54-246-89-234.eu-west-1.compute.amazonaws.com:' \
                                        '5432/d6u6hpm1v38eq4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")
user_stack = []
user_id = []
actual_rooms = []
actual_answer = []
room_stack = []


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


class GetUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    avatar = db.Column(db.String(120), nullable=False, default="")
    experience_act = db.Column(db.Integer, nullable=False, default="0")
    experience_next = db.Column(db.Integer, nullable=False, default="0")
    user_level = db.Column(db.Integer, nullable=False, default="1")
    point_default = db.Column(db.Integer, nullable=True, default="0")
    point_gold = db.Column(db.Integer, nullable=True, default="0")

    def __repr__(self):
        return '<GetUser %r>' % self.username


class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    programming_skills = db.Column(db.Integer, nullable=False, default="0")
    design_skills = db.Column(db.Integer, nullable=False, default="0")
    social_skills = db.Column(db.Integer, nullable=False, default="0")

    def __repr__(self):
        return '<GetUser %r>' % self.username


class UserSkills(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    Python = db.Column(db.String(100), nullable=False, default="0 0 0")
    HTML = db.Column(db.String(100), nullable=False, default="0 0 0")
    CSS = db.Column(db.String(100), nullable=False, default="0 0 0")
    JavaScript = db.Column(db.String(100), nullable=False, default="0 0 0")

    def __repr__(self):
        return '<UserSkills %r>' % self.email


class Questions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(120), unique=True, nullable=False)
    answer1 = db.Column(db.String(100), nullable=False, default="")
    answer2 = db.Column(db.String(100), nullable=False, default="")
    answer3 = db.Column(db.String(100), nullable=False, default="")
    answer4 = db.Column(db.String(100), nullable=False, default="")

    def __repr__(self):
        return '<Questions %r>' % self.email


db.create_all()


def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/create_user', methods=['POST'])
def create_user():
    data = request.get_json(force=True)
    if User.query.filter_by(username=data['nickname']).first() is not None:
        data = {'status': 'Failed',
                'message': 'Nickname is already used'}
        return jsonify(data), 400
    if User.query.filter_by(email=data['email']).first() is not None:
        data = {'status': 'Failed',
                'message': 'Nickname is already used'}
        return jsonify(data), 400
    else:
        user = User(username=data['nickname'], email=data['email'], password=data['password'], status='user')
        user_info = GetUser(username=data['nickname'], email=data['email'])
        user_stats = UserStats(email=data['email'])
        user_skills = UserSkills(email=data['email'])
        db.session.add(user)
        db.session.add(user_info)
        db.session.add(user_stats)
        db.session.add(user_skills)
        db.session.commit()
        data = {'status': 'Success'}
        return jsonify(data), 200


@app.route('/login_user', methods=['POST'])
def login_user():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data['email']).first()
    user_info = GetUser.query.filter_by(email=data['email']).first()
    user_stats = UserStats.query.filter_by(email=data['email']).first()
    user_skills = UserSkills.query.filter_by(email=data['email']).first()
    if user is not None:
        if user.password == data['password']:
            if user_info is None:
                user_info = GetUser(username=user.username, email=data['email'])
                db.session.add(user_info)
                db.session.commit()
            if user_stats is None:
                user_stats = UserStats(email=data['email'])
                db.session.add(user_stats)
                db.session.commit()
            if user_skills is None:
                user_skills = UserSkills(email=data['email'])
                db.session.add(user_skills)
                db.session.commit()
            data = {'status': 'Success'}
            return jsonify(data), 200
        else:
            data = {'status': 'Failed',
                    'message': 'Password is incorrect'}
            return jsonify(data), 400
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


@app.route('/get_user', methods=['POST'])
def get_user():
    data = request.get_json(force=True)
    user_info = GetUser.query.filter_by(email=data['email']).first()
    if user_info is not None:
        if (int(user_info.experience_act) != 0) and int(user_info.experience_act) % 1000 == 0:
            user_info.user_level = int(user_info.user_level) + 1
            user_info.experience_act = 0
            user_info.experience_next = 1000 + ((int(user_info.user_level) - 1) * int(user_info.experience_next))
            db.session.add(user_info)
            db.session.commit()
        user = {'id': user_info.id,
                'username': user_info.username,
                'email': user_info.email,
                'avatar': user_info.avatar,
                'experience_act': int(user_info.experience_act),
                'experience_next': user_info.experience_next,
                'user_level': user_info.user_level,
                'point_default': user_info.point_default,
                'point_gold': user_info.point_gold}
        data = {'status': 'Success', 'user': user}
        return jsonify(data), 200
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


@app.route('/get_user_stats', methods=['POST'])
def get_user_stats():
    data = request.get_json(force=True)
    user_stats = UserStats.query.filter_by(email=data['email']).first()
    if user_stats is not None:
        stats = {'programming_skills': user_stats.programming_skills,
                 'design_skills': user_stats.design_skills,
                 'social_skills': user_stats.social_skills}
        data = {'status': 'Success', 'stats': stats}
        return jsonify(data), 200
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


@app.route('/get_user_skills', methods=['POST'])
def get_user_skills():
    data = request.get_json(force=True)
    user_skills = UserSkills.query.filter_by(email=data['email']).first()
    if user_skills is not None:
        python = user_skills.Python.strip().split()
        html = user_skills.HTML.strip().split()
        css = user_skills.CSS.strip().split()
        javascript = user_skills.JavaScript.strip().split()
        python_skills = {'label': 'Python',
                         'level': python[0],
                         'experience_current': python[1],
                         'experience_required': python[2]}
        html_skills = {'label': 'HTML',
                       'level': html[0],
                       'experience_current': html[1],
                       'experience_required': html[2]}
        css_skills = {'label': 'CSS',
                      'level': css[0],
                      'experience_current': css[1],
                      'experience_required': css[2]}
        javascript_skills = {'label': 'JavaScript',
                             'level': javascript[0],
                             'experience_current': javascript[1],
                             'experience_required': javascript[2]}
        data = {'status': 'Success', 'skills': {'Python': python_skills, 'HTML': html_skills, 'CSS': css_skills,
                                                'JavaScript': javascript_skills}}
        return jsonify(data), 200
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


@socketio.on('chat_message')
def handle_message(data):
    socketio.emit('chat_message', data)
    user_info = GetUser.query.filter_by(username=data['sender']).first()
    user_info.experience_act = int(user_info.experience_act) + 10
    db.session.add(user_info)
    db.session.commit()
    user_info = GetUser.query.filter_by(username=data['sender']).first()
    print(user_info.experience_act)
    print('received message: ' + data['sender'] + ": " + data['msg'])


@socketio.on('trivia_join')
def user_join(data):
    user_stack.append(data['email'])
    actual_rooms.append(data['email'])
    user_id.append(request.sid)
    print(user_stack)
    print(user_id)
    if len(user_stack) == 2:
        player1 = GetUser.query.filter_by(email=user_stack[0]).first()
        player2 = GetUser.query.filter_by(email=user_stack[1]).first()
        question = Questions.query.filter_by(id=1).first()
        actual_answer.append(question.answer1)
        answers = [question.answer1, question.answer2, question.answer3, question.answer4]
        data = {'game_status': 'start',
                'players': {
                    'player1': {
                        'nickname': player1.username,
                        'level': player1.user_level,
                        'status': 'wait'
                    },
                    'player2': {
                        'nickname': player2.username,
                        'level': player2.user_level,
                        'status': 'wait'
                    }
                },
                'question': {
                    'question': question.description,
                    'answers': answers
                }}
        print(data)
        socketio.emit('trivia_update', data)
        actual_rooms.append(uuid.uuid4())
        join_room(actual_rooms[-1], user_id[0])
        join_room(actual_rooms[-1], user_id[1])
        print(player1.username + ' has entered the room.', actual_rooms[-1])
        print(player2.username + ' has entered the room.', actual_rooms[-1])
        user_stack.clear()
        print('start')
    else:
        data = {'game_status': 'lobby', 'user_count': len(user_stack)}
        socketio.emit('trivia_update', data)
        print('lobby')


@socketio.on('trivia_answer')
def user_answer(data):
    player1 = GetUser.query.filter_by(email=actual_rooms[0]).first()
    player2 = GetUser.query.filter_by(email=actual_rooms[1]).first()
    question = Questions.query.filter_by(id=1).first()
    actual_answer.append(question.answer1)
    answers = [question.answer1, question.answer2, question.answer3, question.answer4]
    data2 = {}
    if data['email'] == player1.email:
        actual_player = player1
    else:
        actual_player = player2
    if actual_player == player1:
        data2 = {'game_status': 'start',
                 'players': {
                     'player1': {
                         'nickname': player1.username,
                         'level': player1.user_level,
                         'status': 'answer'
                     },
                     'player2': {
                         'nickname': player2.username,
                         'level': player2.user_level,
                         'status': 'wait'
                     }
                 },
                 'question': {
                     'question': question.description,
                     'answers': answers
                 }}
    elif actual_player == player2:
        data2 = {'game_status': 'start',
                 'players': {
                     'player1': {
                         'nickname': player1.username,
                         'level': player1.user_level,
                         'status': 'wait'
                     },
                     'player2': {
                         'nickname': player2.username,
                         'level': player2.user_level,
                         'status': 'answer'
                     }
                 },
                 'question': {
                     'question': question.description,
                     'answers': answers
                 }}
    socketio.emit('trivia_update', data2)
    print("data2:", data2)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0")