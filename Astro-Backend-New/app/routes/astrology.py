from flask import Flask, request, jsonify, Blueprint
import asyncio
from datetime import datetime
from services.astro_functions import (
    generate_chart,
    calculate_vimshottari_dasha,
    interpret_dasha_sequence,
    get_life_predictions,
    get_gemstones,
    calculate_numerology,
    get_horoscope,
    get_app_activites_from_dasha,
    get_app_activites_for_each_category,
    see_more_life_predictions,
    see_more_horoscope,
    get_pujas,
    get_gemstone_recommendations,
)
from utils.db import get_db

# Create Flask app and blueprint
app = Flask(__name__)
astro_bp = Blueprint("astro", __name__, url_prefix="/astro")

# Define timezone
TIMEZONE_STR = "Asia/Kolkata"

@astro_bp.route("/astrology", methods=["POST"])
async def astrology_api():
    print("\n=== Starting astrology_api endpoint ===")
    try:
        # Get database connection
        print("Connecting to database...")
        db = get_db()
        astrology_collection = db["astrology_readings"]
        print("Database connection established")
        
        # Extract JSON data from the request
        data = request.get_json()
        print(f"Received request data: {data}")

        # Parse input data
        name = data['name']
        birthday = data['birthDate']
        timeOfBirth = data['timeOfBirth']
        latitude = data['latitude']
        longitude = data['longitude']
        user_id = data.get('user_id')
        chart_type = "Vedic"
        horoscope_type = data.get('horoscope_type', 'daily')

        print(f"Processing birth data for {name}")
        print(f"Birth details - Date: {birthday}, Time: {timeOfBirth}")
        print(f"Location - Lat: {latitude}, Long: {longitude}")

        hour, minute = map(int, timeOfBirth.split(':'))
        birthday_datetime = datetime.fromisoformat(birthday.rstrip('Z'))
        birthday_date = birthday_datetime.date()
        cu_year = datetime.now().year
        
        birth_data = {
            "year": birthday_date.year,
            "month": birthday_date.month,
            "day": birthday_date.day,
            "hour": hour,
            "minute": minute,
            "latitude": latitude,
            "longitude": longitude
        }
        print(f"Formatted birth data: {birth_data}")

        # Generate chart and get initial data
        print("\nGenerating chart...")
        chart_data = await asyncio.to_thread(generate_chart, TIMEZONE_STR, birth_data, chart_type)
        print("Chart generation complete")
        
        response_data = {}

        # Get Dasha information
        print("\nCalculating Dasha information...")
        moon_nakshatra = chart_data["Moon"]["sidereal"]["nakshatra"]
        moon_position = chart_data["Moon"]["sidereal"]["position_in_nakshatra"]
        print(f"Moon Nakshatra: {moon_nakshatra}, Position: {moon_position}")
        
        dasha_sequence = await asyncio.to_thread(calculate_vimshottari_dasha, moon_nakshatra, moon_position)
        print("Dasha sequence calculated")

        # Process Dasha sequence
        print("\nProcessing Dasha sequence...")
        dasha_data = []
        current_dash_lord = None
        current_year = birth_data["year"]
        
        for planet, duration in dasha_sequence:
            start_year = current_year
            end_year = current_year + duration - 1
            if start_year <= cu_year <= end_year:
                current_dash_lord = planet
                print(f"Current Dasha Lord identified: {planet}")
            dasha_data.append({
                "planet": planet,
                "duration": duration,
                "start_year": start_year,
                "end_year": end_year
            })
            current_year = end_year + 1
            
        response_data['current_dasha_lord'] = current_dash_lord
        response_data['dasha_sequence'] = dasha_data

        # Get interpretations
        print("\nGetting Dasha interpretations...")
        dasha_interpretations = await asyncio.to_thread(interpret_dasha_sequence, dasha_sequence, chart_data)
        response_data['dasha_interpretations'] = dasha_interpretations
        print("Dasha interpretations complete")

        # Prepare Vedic chart
        print("\nPreparing Vedic chart...")
        vedic_chart = {}
        for planet, data_item in chart_data.items():
            if planet != "aspects":
                sidereal = data_item["sidereal"]
                vedic_chart[planet] = {
                    "zodiac": sidereal["zodiac"],
                    "position_in_zodiac": sidereal["position_in_zodiac"],
                    "nakshatra": sidereal["nakshatra"],
                    "house": sidereal["house"],
                    "status": sidereal["status"]
                }
        print("Vedic chart preparation complete")

        # Execute parallel tasks
        print("\nExecuting parallel tasks...")
        life_predictions_coro = asyncio.to_thread(get_life_predictions, vedic_chart, name)
        gemstone_coro = asyncio.to_thread(get_gemstones, moon_sign := chart_data["Moon"]["sidereal"]["zodiac"], sun_sign := chart_data["Sun"]["sidereal"]["zodiac"])
        numerology_coro = asyncio.to_thread(calculate_numerology, birthday, name)
        horoscope_coro = asyncio.to_thread(get_horoscope, vedic_chart, horoscope_type.lower(), name)
        activities_coro = asyncio.to_thread(get_app_activites_from_dasha, current_dash_lord)
        
        life_predictions, gemstone, numerology, horoscope, activities = await asyncio.gather(
            life_predictions_coro,
            gemstone_coro,
            numerology_coro,
            horoscope_coro,
            activities_coro
        )
        print("Parallel tasks completed")
        
        try:
            print("\nAttempting to get recommended activities...")
            print("Current dash lord:", current_dash_lord)
            recommended_activities = get_app_activites_for_each_category()
            print("Recommended activities structure:", recommended_activities)
            print("Recommended activities retrieved successfully")
        except Exception as e:
            print(f"Error getting recommended activities: {str(e)}")
            print(f"Error type: {type(e)}")
            recommended_activities = []  # Fallback to empty list on error

        # Prepare complete response
        print("\nPreparing final response...")
        response_data.update({
            'activities': activities,
            'life_predictions': life_predictions,
            'gemstones': gemstone,
            'numerology': numerology,
            'horoscope': horoscope,
            'recommended_activities': recommended_activities,
            'chart_data': chart_data
        })

        # Save reading to database
        print("\nSaving reading to database...")
        reading_doc = {
            "user_id": user_id,
            "name": name,
            "birth_data": birth_data,
            "chart_data": chart_data,
            "response_data": response_data,
            "created_at": datetime.utcnow()
        }
        astrology_collection.insert_one(reading_doc)
        print("Reading saved successfully")

        print("=== astrology_api endpoint completed successfully ===\n")
        return jsonify({"status": "success", "data": response_data}), 200
    except Exception as e:
        print(f"\nERROR in astrology_api: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@astro_bp.route("/seeMore", methods=["POST"])
async def see_more_api():
    print("\n=== Starting see_more_api endpoint ===")
    try:
        print("Connecting to database...")
        db = get_db()
        readings_collection = db["astrology_readings"]
        print("Database connection established")
        
        data = request.get_json()
        print(f"Received request data: {data}")
        
        name = data['name']
        chart_data = data['chart_data']
        previous_content = data['previous_content']
        content_type = data['type']
        id = data['id']
        area = data['area']
        user_id = data.get('user_id')
        
        print(f"Processing 'see more' request for {name}, content type: {content_type}")
        
        if id == 1:
            print(f"Generating additional life predictions for area: {area}")
            content = await asyncio.to_thread(see_more_life_predictions, chart_data, name, previous_content, area)
            
            print("Saving additional life predictions to database...")
            readings_collection.update_one(
                {"user_id": user_id, "name": name},
                {
                    "$push": {
                        "additional_readings": {
                            "type": "life_predictions",
                            "area": area,
                            "content": content,
                            "created_at": datetime.utcnow()
                        }
                    }
                }
            )
            print("Additional life predictions saved")
            
            return jsonify({"status": "success", "data": content}), 200
        else:
            print(f"Generating additional horoscope content of type: {content_type}")
            content = await asyncio.to_thread(see_more_horoscope, chart_data, content_type, name, previous_content)
            
            print("Saving additional horoscope content to database...")
            readings_collection.update_one(
                {"user_id": user_id, "name": name},
                {
                    "$push": {
                        "additional_readings": {
                            "type": "horoscope",
                            "content": content,
                            "created_at": datetime.utcnow()
                        }
                    }
                }
            )
            print("Additional horoscope content saved")
            
            return jsonify({"status": "success", "data": content}), 200
    except Exception as e:
        print(f"\nERROR in see_more_api: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

@astro_bp.route("/pujas", methods=["POST"])
async def pujas_api():
    print("\n=== Starting pujas_api endpoint ===")
    try:
        print("Connecting to database...")
        db = get_db()
        pujas_collection = db["puja_recommendations"]
        print("Database connection established")
        
        data = request.get_json()
        print(f"Received request data: {data}")
        
        name = data['name']
        birthday = data['birthDate']
        timeOfBirth = data['timeOfBirth']
        latitude = data['latitude']
        longitude = data['longitude']
        user_id = data.get('user_id')
        chart_type = "Vedic"

        print(f"Processing puja request for {name}")
        print(f"Birth details - Date: {birthday}, Time: {timeOfBirth}")
        print(f"Location - Lat: {latitude}, Long: {longitude}")

        hour, minute = map(int, timeOfBirth.split(':'))
        birthday_datetime = datetime.fromisoformat(birthday.rstrip('Z'))
        birthday_date = birthday_datetime.date()
        
        birth_data = {
            "year": birthday_date.year,
            "month": birthday_date.month,
            "day": birthday_date.day,
            "hour": hour,
            "minute": minute,
            "latitude": latitude,
            "longitude": longitude
        }
        print(f"Formatted birth data: {birth_data}")

        print("\nGenerating chart...")
        chart_data = generate_chart(TIMEZONE_STR, birth_data, chart_type)
        print("Chart generation complete")

        print("\nCalculating puja and gemstone recommendations...")
        puja_task = asyncio.create_task(asyncio.to_thread(get_pujas, chart_data, name))
        gemstones_task = asyncio.create_task(asyncio.to_thread(get_gemstone_recommendations, chart_data, name))
        
        puja_suggestions, gemstones_suggestions = await asyncio.gather(puja_task, gemstones_task)
        print("Recommendations calculated")
        
        # Save recommendations to database
        print("\nSaving recommendations to database...")
        recommendation_doc = {
            "user_id": user_id,
            "name": name,
            "birth_data": birth_data,
            "puja_suggestions": puja_suggestions,
            "gemstones_suggestions": gemstones_suggestions,
            "created_at": datetime.utcnow()
        }
        pujas_collection.insert_one(recommendation_doc)
        print("Recommendations saved successfully")
        
        print("=== pujas_api endpoint completed successfully ===\n")
        return jsonify({
            "status": "success", 
            "data": puja_suggestions, 
            "gemstones": gemstones_suggestions
        }), 200
    except Exception as e:
        print(f"\nERROR in pujas_api: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

# Register blueprint with the app
app.register_blueprint(astro_bp)

if __name__ == "__main__":
    app.run(debug=True)