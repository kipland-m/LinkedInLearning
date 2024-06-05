from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message
from sqlalchemy import Column, Integer, String, Float
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Linking to Database File
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super_secret'

# Creating DB instance
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)

@app.cli.command('db_create')
def db_create():
	db.create_all()
	print('Database created!')

@app.cli.command('db_drop')
def db_drop():
	db.drop_all()
	print('Database dropped.')

@app.cli.command('db_seed')
def db_seed():
	mercury = Planet(planet_name='Mercury',
					 planet_type='Class D',
					 home_star='Sol',
					 mass=3.258e23,
					 radius=1516,
					 distance=35.98e6)
	venus = Planet(planet_name='Venus',
					 planet_type='Class K',
					 home_star='Sol',
					 mass=4.867e24,
					 radius=3760,
					 distance=67.24e6)					 
	earth = Planet(planet_name='Earth',
					 planet_type='Class M',
					 home_star='Sol',
					 mass=5.972e24,
					 radius=3959,
					 distance=92.96e6)		
	db.session.add(mercury)
	db.session.add(venus)
	db.session.add(earth)

	test_user = User(first_name ='William',
					last_name ='Herschel',
					email ='test@test.com',
					password ='P@ssw0rd')

	db.session.add(test_user)
	db.session.commit()
	print("Database seeded!")


@app.route('/')
def hello_world():
	return "Hello."


@app.route('/super_simple')
def super_simple():
	return jsonify(message="Example endpoint. Added some text. Added some more")


@app.route('/not_found')
def not_found():
	return jsonify(message="That resource was not found."), 404


@app.route('/parameters')
def parameters():
	name = request.args.get('name')
	age = int(request.args.get('age'))
	if age < 18:
		return jsonify(message="Sorry "+ name +", you are not old enough to access this resourece."), 401
	else:
		return jsonify(message='Welcome ' + name)
	

@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
	if age < 18:
		return jsonify(message="Sorry "+ name +", you are not old enough to access this resourece."), 401
	else:
		return jsonify(message='Welcome ' + name)


@app.route('/planets', methods=['GET'])
def planets():
	planets_list = Planet.query.all()
	result = planets_schema.dump(planets_list)
	return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
	email = request.form['email']
	test = User.query.filter_by(email=email).first()
	if test:
		return jsonify(message='That email already exists!'), 409
	else:
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		password = request.form['password']
		user = User(first_name=first_name, last_name=last_name, email=email, password=password)
		db.session.add(user)
		db.session.commit()
		return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
	if request.is_json:
		email = request.json['email']
		password = request.json['password']

	else:
		email = request.form['email']
		password = request.form['password']

	# running select statement against User table in database and grabbing first record
	test = User.query.filter_by(email=email, password=password).first()
	if test:
		access_token = create_access_token(identity=email)
		return jsonify(message="Login succeeded!", access_token=access_token)
	else:
		return jsonify(message='Bad email or password'), 401
	

# Creating ORM to interact with DB
class User(db.Model):
	__tablename__ = 'users'
	id = Column(Integer, primary_key=True)
	first_name = Column(String)
	last_name = Column(String)
	email = Column(String, unique=True)
	password = Column(String)


class Planet(db.Model):
	__tablename__ = 'planets'
	planet_id = Column(Integer, primary_key=True)
	planet_name = Column(String)
	planet_type = Column(String)
	home_star = Column(String)
	mass = Column(Float)
	radius = Column(Float)
	distance = Column(Float)


class UserSchema(ma.Schema):
	class Meta:
		fields = ('id', 'first_name', 'email', 'password')


class PlanetSchema(ma.Schema):
	class Meta:
		fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
	app.run()