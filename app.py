from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from geopy.distance import geodesic  # To calculate distances between two locations
from geopy.geocoders import Nominatim  # To get coordinates from address

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with your actual secret key

# MongoDB connection setup for PyMongo
app.config["MONGO_URI"] = "mongodb+srv://thesevasetufoundation:QDBxMA83Wsiamvyb@sevasetu.qplys.mongodb.net/userDB?retryWrites=true&w=majority&appName=Sevasetu"
mongo = PyMongo(app)

# Additional MongoClient connection for direct access to NGO collection
client = MongoClient('mongodb+srv://thesevasetufoundation:QDBxMA83Wsiamvyb@sevasetu.qplys.mongodb.net/?retryWrites=true&w=majority&appName=Sevasetu')
db = client.userDB
ngo_collection = db.ngos

# Geolocator setup with an increased timeout
geolocator = Nominatim(user_agent="geoapiExercises", timeout=10)


import googlemaps

import requests

def get_coordinates(address):
    # Your API key here
    api_key = 'AIzaSyDIenms8YDVpiOiIQGUc5VNgPqbGDGVgNI'

    # Prepare the request URL
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': address,
        'key': api_key
    }

    # Make the request
    response = requests.get(base_url, params=params)
    
    # Process the response
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            # Extracting latitude and longitude
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Error fetching coordinates for {address}: {data['status']}")
    else:
        print(f"Error: {response.status_code}")


# Function to calculate distance between two addresses
def calculate_distance(user_address, ngo_address):
    user_coords = get_coordinates(user_address)
    ngo_coords = get_coordinates(ngo_address)

    if user_coords and ngo_coords:
        return geodesic(user_coords, ngo_coords).km
    return None


@app.route('/')
def home():
    return render_template('home1.html')  # Landing page

@app.route('/index')
def index_redirect():
    action = request.args.get('action', 'login')  # Default action to 'login'
    return render_template('index.html', action=action)

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('loginEmail')
    password = request.form.get('loginPassword')
    user = mongo.db.users.find_one({"email": email})

    if user and check_password_hash(user['password'], password):
        if email == 'thesevasetufoundation@gmail.com' and password == 'codecrusaders_69':
            session['user_email'] = email
            flash("Admin login successful!", "success")
            return redirect(url_for('admin'))

        session['user_email'] = email
        flash("Login successful!", "success")
        return redirect(url_for('home_page'))
    else:
        flash("Invalid email or password. Please try again.", "danger")
        return redirect(url_for('index_redirect'))

@app.route('/signup', methods=['POST'])
def signup():
    first_name = request.form.get('signupFirstName')
    last_name = request.form.get('signupLastName')
    phone_number = request.form.get('signupPhoneNumber')
    email = request.form.get('signupEmail')
    password = request.form.get('signupPassword')
    confirm_password = request.form.get('signupConfirmPassword')

    if password != confirm_password:
        flash("Passwords do not match. Please try again.", "danger")
        return redirect(url_for('index'))

    if mongo.db.users.find_one({"email": email}):
        flash("Email already registered. Please login.", "warning")
        return redirect(url_for('index'))

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

    mongo.db.users.insert_one({
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "email": email,
        "password": hashed_password,
        "donation_amount": 0  # Initialize donation_amount to 0
    })

    session['user_email'] = email
    flash("Signup successful! Redirecting to home page.", "success")
    
    # Send a thank-you email to the user after signup
    send_email_to_user(email, first_name)
    
    return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    user_email = session.get('user_email')

    if user_email:
        user = mongo.db.users.find_one({"email": user_email})
        ngos = list(mongo.db.ngos.find())

        if user:
            return render_template('home.html', user=user, ngos=ngos)
        else:
            flash("User details not found.", "danger")
            return redirect(url_for('index'))
    else:
        flash("User not logged in.", "warning")
        return redirect(url_for('index'))

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')

    if not query:
        return jsonify({"error": "No query provided"}), 400

    try:
        ngos = mongo.db.ngos.find({"name": {"$regex": query, "$options": "i"}})
        results = []

        for ngo in ngos:
            results.append({
                'name': ngo.get('name'),
                'address': ngo.get('address'),
                'contact_number': ngo.get('contact_number'),
                'description': ngo.get('description'),
                'num_children': ngo.get('num_children'),
                'food_cost': ngo.get('food_cost'),
                'images': ngo.get('carousel_images')
            })

        return jsonify(results)
    except Exception as e:
        print(f"Error fetching results: {e}")
        return jsonify({"error": "An error occurred while fetching results"}), 500

@app.route('/get_users', methods=['GET'])
def get_users():
    users = list(mongo.db.users.find({}, {
        "_id": 0,
        "first_name": 1,
        "last_name": 1,
        "phone_number": 1,
        "email": 1,
        "donation_amount": 1
    }))
    return jsonify(users)

@app.route('/update_address', methods=['POST'])
def update_address():
    # Assuming you have user authentication and can get the user's email or ID
    user_email = session.get('user_email')  # Get the user's email from session
    
    if not user_email:
        return redirect(url_for('login'))  # Redirect to login if session is missing
    
    # Get the address from the form
    new_address = request.form.get('address')
    
    if new_address:  # Ensure the address is provided
        # Update the user's address in the database
        mongo.db.users.update_one(
            {"email": user_email},  # Use user identifier like email
            {"$set": {"address": new_address}}  # Set the new address in the 'address' field
        )
    
    return redirect(url_for('home_page'))  # Redirect to the home page or another route
 

@app.route('/increment_donation', methods=['POST'])
def increment_donation():
    data = request.json
    user_email = data.get('email')
    increment_amount = data.get('amount')

    if not increment_amount or increment_amount <= 0:
        return jsonify({"error": "Invalid donation amount"}), 400

    mongo.db.users.update_one(
        {"email": user_email},
        {"$inc": {"donation_amount": increment_amount}}
    )
    
    return jsonify({"message": "Donation updated successfully"})

@app.route('/get_ngos', methods=['GET'])
def get_ngos():
    ngos = list(ngo_collection.find({}, {'_id': 0}))
    return jsonify(ngos)

@app.route('/ngo_details/<ngo_name>', methods=['GET'])
def ngo_details(ngo_name):
    ngo = ngo_collection.find_one({"name": ngo_name}, {'_id': 0})  # Adjust as needed
    if ngo:
        return jsonify(ngo)
    else:
        return jsonify({'error': 'NGO not found'}), 404

@app.route('/update_ngo', methods=['POST'])
def update_ngo():
    data = request.get_json()
    ngo_name = data.get('name')
    updated_fields = {
        "food_cost": data.get('food_cost'),
        "num_children": data.get('num_children'),
        "donation_amount": data.get('donation_amount')
    }
    
    ngo_collection.update_one(
        {"name": ngo_name},
        {"$set": updated_fields}
    )
    
    return jsonify({"message": "NGO updated successfully"})

@app.route('/sort_ngos', methods=['POST'])
def sort_ngos():
    data = request.get_json()
    sort_option = data.get('sort_option')
    
    ngos = list(mongo.db.ngos.find())  # Fetch all NGOs from the database
    
    # Sort by least funded
    if sort_option == 'least-funded':
        ngos_sorted = sorted(ngos, key=lambda ngo: ngo.get('donation_amount', 0))
    
    # Sort by most funded
    elif sort_option == 'most-funded':
        ngos_sorted = sorted(ngos, key=lambda ngo: ngo.get('donation_amount', 0), reverse=True)
    
    # Sort by nearest NGO
    elif sort_option == 'nearest-ngo':
        user_email = session.get('user_email')
        
        if not user_email:
            return jsonify({"error": "User must be logged in to sort by nearest NGO"}), 403
        
        user = mongo.db.users.find_one({"email": user_email})
        user_address = user.get('address')
        
        if not user_address:
            return jsonify({"error": "User address not found"}), 404
        
        ngos_sorted = sorted(ngos, key=lambda ngo: calculate_distance(user_address, ngo.get('address')) or float('inf'))
    
    else:
        return jsonify({"error": "Invalid sort option"}), 400

    # Prepare the NGO list for the response
    ngo_list = [{
        'name': ngo.get('name'),
        'funding': ngo.get('donation_amount'),
        'distance': calculate_distance(user.get('address'), ngo.get('address')) if sort_option == 'nearest-ngo' else None
    } for ngo in ngos_sorted]

    return jsonify(ngo_list)

# Route to send an email
@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    email = data['email']
    first_name = data['first_name']

    send_email_to_user(email, first_name)
    
    return jsonify({'message': 'Email sent successfully!'})

# Helper function to send an email
def send_email_to_user(email, first_name):
    subject = "Thank You for Your Generous Donation to SevaSetu!"
    body = f"""
    Dear {first_name},
    
    I hope this email finds you well!

    We are thrilled to inform you that your generous donation to SevaSetu has been successfully received. 
    Your support helps us continue our mission to make a positive impact on the lives of those in need, and 
    we are deeply grateful for your contribution.

    To help us improve and ensure that we continue delivering meaningful outcomes, we would love to hear your feedback. 
    Please take a moment to fill out the feedback form below:

    [Insert Feedback Form Link]

    Your insights are invaluable to us, and your feedback will help us enhance our services for both donors and beneficiaries alike.

    Thank you once again for your kindness and support.

    Warm regards,
    SevaSetu Team
    """

    message = MIMEMultipart()
    message['From'] = 'thesevasetufoundation@gmail.com'
    message['To'] = email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('thesevasetufoundation@gmail.com', 'rnri bops ohnz hbbu')  # Replace with your credentials
        server.sendmail(message['From'], message['To'], message.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
