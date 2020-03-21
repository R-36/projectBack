from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://xowmwjmfoeodaa:f3314bbaaf7d787f03149e86c4d23cdc531e12e2b717716c0' \
                                        'b391d3ea6ef79fd@ec2-54-246-89-234.eu-west-1.compute.amazonaws.com:' \
                                        '5432/d6u6hpm1v38eq4'
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


class GetUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), unique=True, nullable=False)
    email = db.Column(db.String(120), db.ForeignKey('user.email'), unique=True, nullable=False)
    avatar = db.Column(db.String(120), nullable=False, default="")
    experience_act = db.Column(db.Integer, nullable=False, default="0")
    experience_next = db.Column(db.Integer, nullable=False, default="0")
    user_level = db.Column(db.Integer, nullable=False, default="1")
    point_default = db.Column(db.Integer, nullable=True, default="0")
    point_gold = db.Column(db.Integer, nullable=True, default="0")
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

    def __repr__(self):
        return '<GetUser %r>' % self.username


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
        user_info = GetUser(username=data['nickname'], email=data['email'])
        db.session.add(user)
        db.session.add(user_info)
        db.session.commit()
        data = {'status': 'Success'}
        return jsonify(data), 200


@app.route('/login_user', methods=['POST'])
def login_user():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data['email']).first()
    user_info = GetUser.query.filter_by(email=data['email']).first()
    if user is not None:
        if user.password == data['password']:
            if user_info is None:
                user_info = GetUser(username=data['nickname'], email=data['email'])
                db.session.add(user_info)
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
        user = {'id': user_info.id,
                'username': user_info.username,
                'email': user_info.email,
                'avatar': user_info.avatar,
                'experience_act': user_info.experience_act,
                'experience_next': user_info.experience_next,
                'user_level': user_info.user_level,
                'point_default': user_info.point_default,
                'point_gold': user_info.point_gold}
        data = {'status': 'Success', 'user': jsonify(user)}
        return jsonify(data), 200
    data = {'status': 'Failed',
            'message': 'User not found'}
    return jsonify(data), 400


if __name__ == '__main__':
    app.run()
