from flask import (Flask, render_template, request, flash, session,
                   redirect, jsonify)
from model import connect_to_db, db, User, User_Itinerary
import crud
import requests, json 
from jinja2 import StrictUndefined

app = Flask(__name__)
app.secret_key = "dev"
app.jinja_env.undefined = StrictUndefined

api_key = 'AIzaSyB958LVVLqjnoPNHpD_-I8Nqg6f_2enjd4'

@app.route('/')
def homepage():
    """View homepage."""

    return render_template('homepage.html')

 
@app.route("/users")
def all_users():
    """"View all users"""

    users = crud.get_users()

    return render_template("all_users.html", users=users)


@app.route("/users", methods=["POST"])
def register_user():
    """"Create a new user"""

    user_name = request.form.get('user_name')
    email = request.form.get('email')
    password = request.form.get('password')

    user = crud.get_user_by_email(email)
    if user:
        flash("Cannot create an account with that email. Try again")
    
    else:
        user = crud.create_user(user_name, email, password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.")

    return redirect("/")


@app.route("/users/<user_id>")
def show_user(user_id):
    """"Show details on a particular user"""""

    user = crud.get_user_by_id(user_id)

    return render_template("user_details.html", user=user)


@app.route("/login", methods=["POST"])
def user_login():

    email = request.form['email']
    password = request.form['password']

    user = crud.get_user_by_email(email)

    if not user:
        flash("Login incorrect")

    elif password != user.password:
        flash("Password incorrect")

    else:
        session['current_user'] = user.email
        flash("Logged in!")
        return redirect("/profile")
    
    return redirect("/")


@app.route("/profile")
def show_profile():

    user = crud.get_user_by_email(session["current_user"])
    #itineraries = Saved_Itinerary.query.filter_by(user_id=user.user_id).all()
    user_itineraries = User_Itinerary.query.filter_by(creator=user.user_id).all()

    # if itineraries is None:
    #     itineraries = []
    
    if user_itineraries is None:
        user_itineraries = []


    return render_template("profile.html", user=user, user_itineraries=user_itineraries)


@app.route("/budget_update", methods=['POST'])
def show_budget():

    budget = request.json.get('new_budget')
    user = crud.get_user_by_email(session["current_user"])
    user.budget = int(budget)
    db.session.commit()
    print(user.budget)
    return jsonify({'budget': budget})    


@app.route("/user_itinerary")
def all_user_itineraries():
    """"View all user itineraries"""

    user_itinerary = crud.get_user_itineraries()

    return render_template("all_user_itinerary.html", user_itinerary=user_itinerary)


@app.route("/delete_itinerary", methods=['POST'])
def delete_itinerary():

        delete_user_itinerary = request.json.get('delete_itinerary')
        del_itinerary = crud.get_user_itinerary_by_id(int(delete_user_itinerary))
        flights = crud.get_flights_by_itinerary_id(del_itinerary.user_itinerary_id)
        for flight in flights:
            db.session.delete(flight)
        hotels = crud.get_hotels_by_itinerary_id(del_itinerary.user_itinerary_id)
        for hotel in hotels:
            db.session.delete(hotel)
        activities = crud.get_activities_by_itinerary_id(del_itinerary.user_itinerary_id)
        for activity in activities:
            db.session.delete(activity)
        db.session.commit()
        db.session.delete(del_itinerary)
        db.session.commit()
        return jsonify({'message': 'Success!'})


@app.route("/user_itinerary/<user_itinerary_id>")
def show_user_itinerary(user_itinerary_id):
    """"Show details on a particular itinerary"""

    user_itinerary = crud.get_user_itinerary_by_id(user_itinerary_id)

    return render_template("user_itinerary_details.html", user_itinerary=user_itinerary)

 
#VIEW ITINERARIES THAT USER CREATED AFTER USER LOG IN:
@app.route("/user_itinerary")
def user_itineraries_details():
    """"View user itineraries details"""

    # If the user isn't logged in, flash a message saying "please log in" and redirect to homepage
    # If the user is logged in, their email is in session['current_user']
    # To get all THAT USER's itineraries:
    #       Look up the user ID for that email
    #           0) The user's email address will be session['current_user']
    #           1) get their email, the use user = crud.get_user_by_email(...)
    #           2) their ID is user.user_id
    #       Find all the user_itineraries that have that ID for their creator
    #           0) User_Itinerary.query.filter_by(creator=user.user_id)
    # Give all those itineraries to the render_template to show in HTML
    
    user = crud.get_user_by_email(session["current_user"])
    itineraries = User_Itinerary.query.filter_by(creator=user.user_id).all()
    
    return render_template("user_itinerary_details.html", user=user, itineraries=itineraries)


@app.route("/search", methods=['POST'])
def search_bar():

    search = request.form['search']
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    query = search #search is what the user typed in
    r = requests.get(url + 'query=' + query +
                        '&key=' + api_key) 
    result = r.json() 
    result_list = result['results'] 
    user = crud.get_user_by_email(session["current_user"])
    itineraries = User_Itinerary.query.filter_by(creator=user.user_id).all()


    return render_template("search.html", result_list=result_list, itineraries=itineraries)


@app.route("/add_to_itinerary", methods=['POST'])
def create_add_hotel():

    user = crud.get_user_by_email(session["current_user"])
    name = request.form['name']
    location = request.form['location']
    user_itinerary_id = request.form['itinerary']
    user_itinerary = crud.get_user_itinerary_by_id(user_itinerary_id) #change this to look up a specific itinerary
    hotelxactivity = request.form['hotelxactivity']
    if hotelxactivity == 'hotel':
        hotel = crud.create_hotel(name, location, None, user_itinerary.user_itinerary_id)
        db.session.add(hotel)
        db.session.commit()
    else: 
        activity = crud.create_activities(name, location, None, user_itinerary.user_itinerary_id)
        db.session.add(activity)
        db.session.commit()

    return render_template("user_itinerary_details.html", user_itinerary=user_itinerary)


@app.route("/new_itinerary", methods=['POST'])
def create_new_itinerary():

    user = crud.get_user_by_email(session["current_user"])
    # creator = crud.create_user_itinerary(creator=user.user_id)
    # places_id = crud.create_user_itinerary(places_id=places_id.places_id)
    user_itinerary_name = request.form['new_itinerary']
    # user_itinerary = crud.get_user_itinerary_by_id(user_itinerary_id)
    new_itinerary = crud.create_user_itinerary(user.user_id, user_itinerary_name) #using user id and itenerary name from form
    db.session.add(new_itinerary)
    db.session.commit()


    return redirect("/profile")
    #in the html, user picks a place, form gets submitted
    #in the server, get the user, so we can get user id, also get place by name or id
    #then use user id and place id to create new itinerary 
    #add and commit the new itinerary
    # redirect to profile route
    
@app.route("/delete_hotel", methods=['POST'])
def delete_hotel():
    delete_hotel = request.json.get('delete_hotel')
    del_hotel = crud.get_hotel_by_id(int(delete_hotel))
    db.session.delete(del_hotel)
    db.session.commit()
    return jsonify({'message': 'Hotel deleted!'})


@app.route("/delete_flight", methods=['POST'])
def delete_flight():
    delete_flight = request.json.get('delete_flight')
    del_flight = crud.get_flight_by_id(int(delete_flight))
    db.session.delete(del_flight)
    db.session.commit()
    return jsonify({'message': 'Flight deleted!'})

@app.route("/delete_activity", methods=['POST'])
def delete_activity():
    delete_activity = request.json.get('delete_activity')
    del_activity = crud.get_activities_by_id(int(delete_activity))
    db.session.delete(del_activity)
    db.session.commit()
    return jsonify({'message': 'Activity deleted!'})

 
if __name__ == "__main__":
    connect_to_db(app)
    app.run(host="0.0.0.0", debug=True)