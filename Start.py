from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres:123@localhost/py_hack'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


db.create_all()


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
        db.session.add(user)
        db.session.commit()
        data = {'status': 'Success'}
        return jsonify(data), 200


@app.route('/login_user', methods=['POST'])
def login_user():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data['email']).first()
    if user is not None:
        if user.password == data['password']:
            data = {'status': 'Success'}
            return jsonify(data), 200
        else:
            data = {'status': 'Failed',
                    'message': 'Password is incorrect'}
            return jsonify(data), 400
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0')
