from flask import Flask, request, escape, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://sudheer:sudheer@cluster0.4agbj.mongodb.net/pawssible?retryWrites=true&w=majority"
mongo = PyMongo(app)


@app.route('/')
def init():                            # this is a comment. You can create your own function name
    return '<h1> {} </h1>'.format(__name__)


# User actions. Login, register, forgot password.

# API to Login
@app.route('/users/login', methods=['POST'])
def performLogin():
    users = mongo.db.users
    # app.logger.info('%s email', request.json)
    # email = request.json['email']
    # password = request.json['password']
    
    output = []
    
    user = users.find_one({'email': request.json['email'],'password':request.json['password']})
    if user == None: 
        return jsonify({'success' : False, "message":"User with email and password doesn't exists. Try Forgot Password or Regsitration for new user if not done already."})
    else:
        return jsonify({'success' : True, "user": serializeUser(user)})
    return jsonify({'success' : False, "message":"Something went wrong"})


# register or create new user
@app.route('/users/register', methods=['POST'])
def performRegistration():
    users = mongo.db.users
    
    email = request.json['email']

    output = []
    
    user = users.find_one({'email': email})
    if user == None: 
        users.insert_one({
            'name': request.json['name'], 
            'email':email,
            'password':request.json['password'], 
            'userType':request.json['userType'],
            'phone':request.json['phone'],
            'address':request.json['address']
        })
        user = users.find_one({'email': email})
        return jsonify({'success' : True, "user": serializeUser(user)})
    else:
        return jsonify({'success' : False, "message":"User with email already exists"})
    return jsonify({'success' : False, "message":"Something went wrong"})
    
# Update or edit user
@app.route('/users/updateuser', methods=['POST'])
def updateUser():
    users = mongo.db.users
    
    userId = request.json['userId']

    output = []
    
    user = users.find_one({'_id': ObjectId(userId)})
    if user == None: 
        return jsonify({'success' : False, "message":"User doesn't exists"})
    else:
        newvalues = { "$set": {
            'phone': request.json['phone'],
            'name': request.json['name'],
            'address': request.json['address'],
            'password': request.json['password']
        } }
        users.update_one({'_id': ObjectId(userId)}, newvalues)
        user = users.find_one({'_id': ObjectId(userId)})
        return jsonify({'success' : True, "user": serializeUser(user)})
    return jsonify({'success' : False})
    
    
# reset password
@app.route('/users/resetpassword', methods=['POST'])
def resetPassword():
    users = mongo.db.users
    
    email = request.json['email']

    output = []
    
    newvalues = { "$set": { 'password': request.json['password'] } }

    user = users.find_one({'email': email})
    if user == None: 
        return jsonify({'success' : False, "message":"User with email Id doesn't exists"})
    else:
        users.update_one({'email': email}, newvalues)
        user = users.find_one({'email': email})
        return jsonify({'success' : True, "user": serializeUser(user)})
    return jsonify({'success' : False, "message":"Something went wrong"})
    
    
# API to get dogs for rent(shows all including active ones) to customers
@app.route('/dogs', methods=['GET'])
def getAllDogs():
    dogs = mongo.db.dogs
    output = []
    for dog in dogs.find({'active':True}):
        output.append(serialize(dog))
    return jsonify({'dogs': output})


@app.route('/dogs/filter/<maxprice>', methods=['GET'])
def getAllDogsFilter(maxprice):
    max=float(maxprice)
    dogs = mongo.db.dogs
    output = []
    # app.logger.info('%s max price', max)
    for dog in dogs.find({ 'hourlyPrice': { '$lt': max }}):
        output.append(serialize(dog))
    return jsonify({'dogs': output})


# API to get dogs of owner(shows all including not active ones)
@app.route('/dogs/<ownerId>', methods=['GET'])
def getOwnerDogs(ownerId):
    dogs = mongo.db.dogs
    output = []
    for dog in dogs.find({'ownerId': ownerId}):
        output.append(serializeDog(dog))
    return jsonify({'dogs': output})
    
    
# API to get all bookings of owner
@app.route('/bookings/ownerbookings/<userId>', methods=['GET'])
def getOwnerBookings(userId):
    output = []
    try:
        bookings = mongo.db.bookings
        for i in bookings.find({'ownerId': userId}):
            output.append(serializeBooking(i))
        return jsonify({'bookings': output})
    except:
        return jsonify({'bookings': output})


# API to get booking requests for owner
@app.route('/bookings/ownerbookingrequests/<userId>', methods=['GET'])
def getOwnerBookingRequests(userId):
    output = []
    try:
        bookings = mongo.db.bookings
        for i in bookings.find({'ownerId': userId,'status':'R'}):
            output.append(serializeBooking(i))
        return jsonify({'bookings': output})
    except:
        return jsonify({'bookings': output})


# status - R - requested, X - Cancelled/Rejected, C - Completed, P - Accepted
# Accept booking request from customer
@app.route('/bookings/acceptbookingrequest/<requestId>', methods=['GET'])
def acceptBookingRequest(requestId):
    output = []
    try:
        bookings = mongo.db.bookings
        requested = bookings.find_one({'_id': ObjectId(requestId),'status':'R'})
        if requested == None: 
            return jsonify({'success' : False, "message":"Booking doesn't exists"})
        else:
            newvalues = { "$set": {
                'status': 'P'
            } }
            bookings.update_one({'_id': ObjectId(requestId)}, newvalues)
        return jsonify({'success' : True, "message": "Accepted the request successfully"})
    except:
        return jsonify({'success' : False})


# Complete the booking after it is done.
@app.route('/bookings/completebooking/<requestId>', methods=['GET'])
def completeBooking(requestId):
    output = []
    try:
        bookings = mongo.db.bookings
        request = bookings.find_one({'_id': ObjectId(requestId),'status':'C'})
        if request == None: 
            return jsonify({'success' : False, "message":"Booking doesn't exists"})
        else:
            newvalues = { "$set": {
                'status': 'C'
            } }
            bookings.update_one({'_id': ObjectId(requestId)}, newvalues)
        return jsonify({'success' : True, "message": "Completed the request successfully"})
    except:
        return jsonify({'success' : False})
  
        
# Reject a booking request
@app.route('/bookings/rejectbookingrequest/<requestId>', methods=['GET'])
def rejectBookingRequest(requestId):
    output = []
    try:
        bookings = mongo.db.bookings
        request = bookings.find_one({'_id': ObjectId(requestId)})
        if request == None: 
            return jsonify({'success' : False, "message":"Booking doesn't exists"})
        else:
            newvalues = { "$set": {
                'status': 'X'
            } }
            bookings.update_one({'_id': ObjectId(requestId)}, newvalues)
        return jsonify({'success' : True, "message": "Rejected the Booking request successfully"})
    except:
        return jsonify({'success' : False})


# API to create new booking
@app.route('/bookings/createBooking', methods=['POST'])
def createBooking():
    try:
        bookings = mongo.db.bookings
        id = bookings.insert_one({
            'ownerId': request.json['ownerId'], 
            'customerId':request.json['customerId'], 
            'dogId':request.json['dogId'],
            'hours':request.json['hours'],
            'total':request.json['total'],
            'status': 'R',
            'timestamp':request.json['timestamp']
        })
        booking = bookings.find_one({'_id': ObjectId(id.inserted_id)})
        return jsonify({'success' : True, "booking": serializeBooking(booking)})
    except:
        return jsonify({'success' : False})


# API to get bookings of customer
@app.route('/bookings/customerbookings/<userId>', methods=['GET'])
def getCustomerBookings(userId):
    output = []
    try:
        bookings = mongo.db.bookings
        for i in bookings.find({'customerId': userId}):
            output.append(serializeBooking(i))
        return jsonify({'bookings': output})
    except:
        return jsonify({'bookings': output})


# API to get current location of dog by owner
@app.route('/dogs/<dogId>', methods=['GET'])
def getDogCurrentLocation(dogId):
    output = []
    try:
        for i in  mongo.db.locations.find({'dogId': dogId}):
            output.append(serializeLocation(i))
        return jsonify({'locationHistory': output})
    except:
        return jsonify({'locationHistory': output})


# Adds current dog location to db
@app.route('/dogs/location', methods=['POST'])
def addDogLocation():
    mongo.db.locations.insert_one({
        "dogId": request.json['dogId'],
        "customerId": request.json['customerId'],
        "lat": request.json['lat'],
        "long": request.json['long'],
        "timestamp": datetime.now()
    })

    return jsonify({'success' : True})


# Adds new dog to db
@app.route('/dogs/addDog', methods=['POST'])
def addDog():
    dogs = mongo.db.dogs
    id = dogs.insert_one({
        'breedname':request.json['breedname'],
        'description':request.json['description'],
        'allergies':request.json['allergies'],
        'likes':request.json['likes'],
        'disLikes':request.json['disLikes'],
        'ageInMonths':request.json['ageInMonths'],
        'hourlyPrice':request.json['hourlyPrice'],
        'ownerId':request.json['ownerId'],
        'photo':request.json['photo'],
        'active':True
    })
    newDog = dogs.find_one({'_id': ObjectId(id.inserted_id)})
    return jsonify({'success' : True, "dog": serializeDog(newDog)})

    
# updates dog to db
@app.route('/dogs/updateDog', methods=['POST'])
def updateDog():
    dogs = mongo.db.dogs
    dogId = request.json['dogId']

    output = []
    dog = dogs.find_one({'_id': ObjectId(dogId)})
    if dog == None: 
        return jsonify({'success' : False, "message":"Dog doesn't exists"})
    app.logger.info('%s max price', request.json['breedname'])
    dogs.update_one({'_id': ObjectId(dogId)}, { "$set": {
        'breedname':request.json['breedname'],
        'description':request.json['description'],
        'allergies':request.json['allergies'],
        'likes':request.json['likes'],
        'disLikes':request.json['disLikes'],
        'ageInMonths':request.json['ageInMonths'],
        'hourlyPrice':request.json['hourlyPrice'],
        'photo':request.json['photo'],
        'active':request.json['active']
    } })

    return jsonify({'success' : True,"dog":serializeDog(dogs.find_one({'_id': ObjectId(dogId)})) })


# Helper Methods for parsing and serializing data to JSON
def serialize(dog):
    ownerId = dog['ownerId'];   
    users = mongo.db.users
    i = users.find_one({'_id': ObjectId(ownerId)})
    name = i['name']
    return {
        "_id" : str(dog['_id']),
        "breedname" : dog['breedname'],
        "description": dog['description'],
        "allergies": dog['allergies'],
        "likes": dog['likes'],
        "active": dog['active'],
        "disLikes": dog['disLikes'],
        "ageInMonths": dog['ageInMonths'],
        "hourlyPrice": dog['hourlyPrice'],
        "ownerId": ownerId,
        "ownerName": name,
        "photo": dog['photo']
    }
    
def serializeDog(dog):
    return {
        "_id" : str(dog['_id']),
        "breedname" : dog['breedname'],
        "description": dog['description'],
        "active": dog['active'],
        "allergies": dog['allergies'],
        "likes": dog['likes'],
        "disLikes": dog['disLikes'],
        "ageInMonths": dog['ageInMonths'],
        "hourlyPrice": dog['hourlyPrice'],
        "ownerId": dog['ownerId'],
        "photo": dog['photo']
    }

def serializeUser(user):
    return {
        "_id" : str(user['_id']),
        "name" : user['name'],
        "email": user['email'],
        "phone": user['phone'],
        "userType": user['userType'],
        "address": user['address']
    }
    
def serializeLocation(location):
    return {
        "_id" : str(location['_id']),
        "dogId" : location['dogId'],
        "customerId": location['customerId'],
        "lat": location['lat'],
        "long": location['long'],
        "timestamp": location['timestamp']
    }
    
def serializeBooking(booking):
    
    ownerId = booking['ownerId'];   
    customerId = booking['customerId'];
    dogId = booking['dogId'];
    
    users = mongo.db.users
    dogs = mongo.db.dogs
    
    user = users.find_one({'_id': ObjectId(ownerId)})
    owner = serializeUser(user)
    user = users.find_one({'_id': ObjectId(customerId)})
    customer = serializeUser(user)
    dog = dogs.find_one({'_id': ObjectId(dogId)})
    dog = serializeDog(dog)
    
    return {
        "_id" : str(booking['_id']),
        "dog" : dog,
        "owner": owner,
        "customer": customer,
        "hours": booking['hours'],
        "totalAmount": booking['total'],
        "timestamp":booking['timestamp'],
        "status":booking['status'] 
    }
    
# status - R - requested, X - cancelled, C - Completed, P - Accepted

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    # app.run(host='10.0.0.182', port=5000, debug=True)
    # app.run(host='0.0.0.0', port=5000, debug=True)
