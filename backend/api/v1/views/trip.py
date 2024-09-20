#!/usr/bin/python3
"""Module handles all authentications"""
import logging
from api.v1.views import app_views
from models import Place
from models import PlanTrip
from models import storage
from flask import jsonify, request
from api.v1.utils.utils import (
    get_weather_info,
    get_place_info,
    get_current_user,
    load_information,
)
from flask_jwt_extended import jwt_required

log = logging.getLogger()


@app_views.route("/plan_trip", methods=["POST"], strict_slashes=False)
@jwt_required()
def plan_trip():
    """
    Plan trip to places
    """
    data = request.get_json()

    user = get_current_user()

    city = data.get("city")
    start_date = data.get("startDate")
    end_date = data.get("endDate")
    no_of_people = int(data.get("numberOfPeople")["number"])
    accommodation_name = data.get("accommodation")["name"]
    accommodation_price = float(data.get("accommodation")["price"])
    flight_departure_price = float(data.get("flights")["departure"]["price"])
    flight_return_price = float(data.get("flights")["return"]["price"])
    transport_cost = float(data.get("transport")["cost"])
    meals_snack_price = float(data.get("meals")["price"])
    activities = float(data.get("activities")["price"])
    total_budget = float(data.get("totalBudget"))

    try:
        plan_trip = PlanTrip(
            city=city,
            start_date=start_date,
            end_date=end_date,
            number_of_people=no_of_people,
            accommodation_name=accommodation_name,
            accommodation_price=accommodation_price,
            flight_departure_price=flight_departure_price,
            flight_return_price=flight_return_price,
            transport_cost=transport_cost,
            meals_snack_price=meals_snack_price,
            activities_tourist_sport_price=activities,
            total_budget=total_budget,
            user_id=user.id,
        )

        storage.new(plan_trip)
        storage.save()
        # print(plan_trip)
        return jsonify("Trip saved successfully"), 200
    except Exception as e:
        log.error(f"Unable to save trip: {e}")
        return jsonify(f"Error while saving Trip {e}"), 500


@app_views.route("/save_place", methods=["POST"], strict_slashes=False)
def save_place():
    """
            Save information of a place

    Returns:
            Message - Status (information has been saved)
    """

    data = request.get_json()
    city_name = data.get("city")

    log.info(f"Saving info about {city_name}")

    try:
        place = storage.get_place(city_name)
        match place:
            case None:
                place_info = get_place_info(city_name)
                assert place_info is not None
                place = Place(
                    city=city_name,
                    latitude=place_info["latitude"],
                    longitude=place_info["longitude"],
                    description=place_info["description"],
                    keywords=place_info["keywords"],
                    url_link=place_info["url_link"],
                )
                place.save()
                log.info(f"{city_name} information saved")
            case _:
                latitude = place.latitude
                longitude = place.longitude
                get_weather_info(latitude, longitude, city_name)

        return jsonify({"mesage": "Information saved"}), 200
    except Exception as e:
        log.error(f"Unable to save information about {city_name}: {e}")
        return (jsonify({"mesage": "Unable to save information"}), 500)


@app_views.route("/load_place", methods=["GET"], strict_slashes=False)
def load_place():
    """
    Load Information about place
    """
    place = request.args.get("city")
    log.info(f"Loading information about {place}")
    data = load_information(place)
    if data is None:
        return (jsonify({"message": "No information"}), 200)

    log.info(f"Loaded information about {place}")
    return (jsonify(data), 200)


@app_views.route("/dashboard", methods=["GET"], strict_slashes=False)
@jwt_required()
def dashboard():
    """Get all trips and weather data associated to a user

    Returns:
                    json: a list of trips and their weather condition
                    as of when user made request
    """
    user = get_current_user()
    log.info(f"Getting all the planned trips of {user.username}")

    try:
        planned_trips = storage.all_trips_user(user.id)
        match planned_trips:
            case None:
                return (
                    jsonify(
                        {"error": "No user trip found, try creating a trip"},
                        status=404,
                    ),
                )
            case _:
                planned_trips = planned_trips.values()
                places = [planned_trip.city for planned_trip in planned_trips]
                places_info = [
                    storage.get_place(place).to_dict() for place in places
                ]
                [
                    place_info.update(
                        get_weather_info(
                            place_info["latitude"],
                            place_info["longitude"],
                            place_info["city"],
                        )
                    )
                    for place_info in places_info
                ]
                return jsonify(places_info), 200

    except Exception as e:
        log.error(f"Unable to get planned trips of {user.username}: {e}")
