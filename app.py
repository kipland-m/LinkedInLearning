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
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '8998ef984104a0'
app.config['MAIL_PASSWORD'] = 'e22bb9b6a3b2c1'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# Creating DB instance
db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


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
	

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
	user = User.query.filter_by(email=email).first()
	if user:
		msg = Message("Your planetary API password is " + user.password,
				sender="admin.planetary-api.com",
				recipients=[email])
		mail.send(msg)
		return jsonify(message="Password sent to " + email)
	else:
		return jsonify(message="That email doesn't exist"), 401
	

@app.route('/planet_details/<int:planet_id>', methods=['GET'])
def planet_details(planet_id: int):
	# this queries the Planet table in our database for our planet_id that is passed through the URL
	planet = Planet.query.filter_by(planet_id=planet_id).first()
	# if a planet was found, this will return true
	if planet:
		result = planet_schema.dump(planet)
		return jsonify(result)
	else:
		return jsonify(message="That planet does not exist"), 404
	
# This route does not work. I am stumped.
# Instead of wasting hours and hours debugging a tutorial flask project for my work,
# I am going to skip this as the code makes sense to me and I understand
# How to implement a route that allows you to create new database entries through forms.
@app.route('/add_planet', methods=['POST'])
# this jwt required decorator makes it so you have to be authorized in order to POST data through this endpoint.
# you will provide a username and password that the database has in it, then receive a bearer token.
# Then in postman you would change your authorization to bearer token and paste the given token there.
@jwt_required()
def add_planet():
	planet_name = request.form['planet_name']
	test = Planet.query.filter_by(planet_name=planet_name).first()
	if test:
		return jsonify("This is already a planet by that name!"), 409
	else:
		planet_type = request.form['planet_type']
		home_star = request.form['home_star']
		mass = float(request.form['mass'])
		radius = float(request.form['radius'])
		distance = float(request.form['distance'])

	new_planet = Planet(planet_name=planet_name,
					 planet_type=planet_type,
					 home_star=home_star,
					 mass=mass,
					 radius=radius,
					 distance=distance)	
	
	db.session.add(new_planet)
	db.session.commit()
	return jsonify(message="You added a planet."), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required()
def update_planet():
	planet_id = int(request.form['planet_id'])
	planet = Planet.query.filter_by(planet_id=planet_id).first()
	if planet:
		planet.planet_name = request.form['planet_name']
		planet.planet_type = request.form['planet_type']
		planet.home_star = request.form['home_star']
		planet.mass = float(request.form['mass'])
		planet.radius = float(request.form['radius'])
		planet.distance = float(request.form['distance'])
		db.session.commit()
		return jsonify(message='You updated a planet'), 202
	
	else:
		return jsonify(message='That planet does not exist'), 404
	

@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_planet(planet_id: int):
	planet = Planet.query.filter_by(planet_id=planet_id).first()
	if planet:
		db.session.delete(planet)
		db.session.commit()
		return jsonify(message="You deleted a planet."), 202
	else:
		return jsonify(message="That planet could not be found."), 404
	

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
