import swisseph as swe  # type: ignore
from datetime import datetime
import functools
import pytz
import anthropic  # type: ignore
import math
import re
from geopy.geocoders import Nominatim  # type: ignore
from dotenv import load_dotenv
import os
import xml.etree.ElementTree as ET
import re
import pandas as pd
from helper.query_helper import connect_to_db, get_query_data
from data.static import SIGN_GEMSTONES_RECCOMMENDED, RECCOMENDED_ACTIVITES,numerology_interpretations
import random
import logging

load_dotenv()

client = anthropic.Anthropic(
    # defaults to os.environ.get("ANTHROPIC_API_KEY")
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)


# Configure the logger (if not already configured)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

def truncate(obj, max_length=100):
    obj_str = str(obj)
    if len(obj_str) > max_length:
        return obj_str[:max_length] + '... [truncated]'
    return obj_str

def log_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Truncate args and kwargs for logging
        truncated_args = tuple(truncate(arg) for arg in args)
        truncated_kwargs = {k: truncate(v) for k, v in kwargs.items()}
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Exception in function '{func.__name__}': {e}", exc_info=True)
            raise
    return wrapper
# Define the gemstone mapping for each Moon sign (Rashi)
SIGN_GEMSTONES = {
    "Aries": ("Red Coral", "Mars"),
    "Taurus": ("Emerald", "Venus"),
    "Gemini": ("Emerald", "Mercury"),
    "Cancer": ("Pearl", "Moon"),
    "Leo": ("Ruby", "Sun"),
    "Virgo": ("Emerald", "Mercury"),
    "Libra": ("Diamond", "Venus"),
    "Scorpio": ("Red Coral", "Mars"),
    "Sagittarius": ("Yellow Sapphire", "Jupiter"),
    "Capricorn": ("Blue Sapphire", "Saturn"),
    "Aquarius": ("Blue Sapphire", "Saturn"),
    "Pisces": ("Yellow Sapphire", "Jupiter"),
}


def extract_text_between_patterns(text, pattern):
    """
    Extracts text between the specified opening and closing tags.

    Parameters:
    - text (str): The input text containing the tags.
    - pattern (str): The tag name to search for.

    Returns:
    - str or None: The text between the tags if found; otherwise, None.
    """
    # Use regex to find text between the opening and closing tags of the given pattern
    regex_pattern = fr"<{pattern}>(.*?)</{pattern}>"
    match = re.search(regex_pattern, text, re.DOTALL)
    return match.group(1).strip() if match else None

# Vimshottari Dasha Periods (years)
dasha_periods = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

# Nakshatra Rulers
nakshatra_rulers = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]

# Nakshatra to Ruler Mapping
nakshatra_to_ruler = {
    "Ashwini": "Ketu",
    "Bharani": "Venus",
    "Krittika": "Sun",
    "Rohini": "Moon",
    "Mrigashira": "Mars",
    "Ardra": "Rahu",
    "Punarvasu": "Jupiter",
    "Pushya": "Saturn",
    "Ashlesha": "Mercury",
    "Magha": "Ketu",
    "Purva Phalguni": "Venus",
    "Uttara Phalguni": "Sun",
    "Hasta": "Moon",
    "Chitra": "Mars",
    "Swati": "Rahu",
    "Vishakha": "Jupiter",
    "Anuradha": "Saturn",
    "Jyeshtha": "Mercury",
    "Mula": "Ketu",
    "Purva Ashadha": "Venus",
    "Uttara Ashadha": "Sun",
    "Shravana": "Moon",
    "Dhanishta": "Mars",
    "Shatabhisha": "Rahu",
    "Purva Bhadrapada": "Jupiter",
    "Uttara Bhadrapada": "Saturn",
    "Revati": "Mercury",
}

# Define the planets with their Swiss Ephemeris IDs
planets = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN,
    'Rahu': swe.TRUE_NODE,  # North Node
    # Ketu will be calculated as opposite to Rahu
}

# Define exaltation and debilitation signs for planets
exaltation_signs = {
    'Sun': 'Aries',
    'Moon': 'Taurus',
    'Mars': 'Capricorn',
    'Mercury': 'Virgo',
    'Jupiter': 'Cancer',
    'Venus': 'Pisces',
    'Saturn': 'Libra',
    'Rahu': 'Taurus',
    'Ketu': 'Scorpio',
}

debilitation_signs = {
    'Sun': 'Libra',
    'Moon': 'Scorpio',
    'Mars': 'Cancer',
    'Mercury': 'Pisces',
    'Jupiter': 'Capricorn',
    'Venus': 'Virgo',
    'Saturn': 'Aries',
    'Rahu': 'Scorpio',
    'Ketu': 'Taurus',
}

# Zodiac signs
zodiac_signs = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

df = pd.read_csv('data/dasha_data_mapper.csv')

@log_function
def get_app_activites_from_dasha(current_dasha):
    activities = []
    for index, row in df.iterrows():
        if current_dasha == row['dasha']:
            activities.append(row['id'])
    
    recommended_activities = get_query_data(f'''SELECT id, name, thumbnail_new_url, activity_url FROM app_activities WHERE id IN ({", ".join(map(str, activities))}) LIMIT 3''')

    return recommended_activities

@log_function
def get_app_activites_for_each_category():
    activities_by_category = {}
    all_selected_ids = []
    category_activity_map = {}
    
    # First, select activities and keep track of their categories
    for category in RECCOMENDED_ACTIVITES:
        category_activities = RECCOMENDED_ACTIVITES[category]
        # Randomly select 2 activities from the category
        selected = random.sample(category_activities, 2)
        selected_ids = [activity['id'] for activity in selected]
        all_selected_ids.extend(selected_ids)
        category_activity_map[category] = selected_ids
    
    # Fetch all activities data from database in a single query
    activities_data = get_query_data(f'''SELECT id, name, thumbnail_new_url, activity_url 
                                       FROM app_activities 
                                       WHERE id IN ({", ".join(map(str, all_selected_ids))})''')
    
    # Create a lookup dictionary for quick access to activity data
    activity_lookup = {activity['id']: activity for activity in activities_data}
    
    # Organize activities by category with full details
    for category, activity_ids in category_activity_map.items():
        activities_by_category[category] = [activity_lookup[aid] for aid in activity_ids]
    
    return activities_by_category

@log_function
def generate_chart(user_tz, birth_data, chart_type='Vedic'):
    planet_tropical_positions, planet_sidereal_positions, houses = create_birth_chart(
        user_tz, birth_data
    )
    user_data = {}
    if chart_type == 'Vedic':
        # Sidereal calculations
        for planet, position in planet_sidereal_positions.items():
            user_data[planet] = {"sidereal": {}}
            nakshatra, position_in_nakshatra = degree_to_nakshatra(position)
            zodiac, position_in_zodiac = degree_to_zodiac(position)
            pada = calculate_pada(position_in_nakshatra)
            house = find_house(position, houses)

            # Check for exaltation, debilitation
            status = check_exaltation_debilitation(planet, zodiac)

            user_data[planet]["sidereal"] = {
                "nakshatra": nakshatra,
                "position_in_nakshatra": round(position_in_nakshatra, 2),
                "zodiac": zodiac,
                "position_in_zodiac": round(position_in_zodiac, 2),
                "pada": pada,
                "house": house,
                "status": status,
            }

        # Calculate aspects
        aspects = calculate_aspects(planet_sidereal_positions)

        user_data['aspects'] = aspects
        return user_data
    else:
        # Tropical calculations
        for planet, position in planet_tropical_positions.items():
            user_data[planet] = {"tropical": {}}
            nakshatra, position_in_nakshatra = degree_to_nakshatra(position)
            zodiac, position_in_zodiac = degree_to_zodiac(position)
            pada = calculate_pada(position_in_nakshatra)
            house = find_house(position, houses)

            # Check for exaltation, debilitation
            status = check_exaltation_debilitation(planet, zodiac)

            user_data[planet]["tropical"] = {
                "nakshatra": nakshatra,
                "position_in_nakshatra": round(position_in_nakshatra, 2),
                "zodiac": zodiac,
                "position_in_zodiac": round(position_in_zodiac, 2),
                "pada": pada,
                "house": house,
                "status": status,
            }

        # Calculate aspects
        aspects = calculate_aspects(planet_tropical_positions)

        user_data['aspects'] = aspects
        return user_data

@log_function
def create_birth_chart(user_tz, birth_data):
    # Convert local time to UTC
    local_datetime = datetime(
        birth_data["year"],
        birth_data["month"],
        birth_data["day"],
        birth_data["hour"],
        birth_data["minute"],
    )
    local_datetime = pytz.timezone(user_tz).localize(local_datetime)
    utc_datetime = local_datetime.astimezone(pytz.UTC)

    # Convert UTC time to Julian Day for Swiss Ephemeris
    julian_day = swe.utc_to_jd(
        utc_datetime.year,
        utc_datetime.month,
        utc_datetime.day,
        utc_datetime.hour,
        utc_datetime.minute,
        int(utc_datetime.second),
    )[0]

    # Define observer location
    latitude = birth_data["latitude"]
    longitude = birth_data["longitude"]

    # Planetary positions
    planet_tropical_positions = {}
    planet_sidereal_positions = {}

    # Set ayanamsa for Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Calculate the houses
    house_system = 'W'  # Whole Sign House System
    houses, ascmc = swe.houses_ex(julian_day, latitude, longitude, house_system.encode())
    # houses[0] to houses[11] contain the cusp positions of houses 1 to 12
    # ascmc[0] is the Ascendant

    # Add the Ascendant to the results
    ascendant_tropical = ascmc[0]  # Ascendant in tropical
    ascendant_sidereal = (ascendant_tropical - swe.get_ayanamsa_ut(julian_day)) % 360  # Adjust for sidereal
    planet_tropical_positions["Ascendant"] = ascendant_tropical
    planet_sidereal_positions["Ascendant"] = ascendant_sidereal

    for name, planet_id in planets.items():
        # Get tropical position
        tropical_position, _ = swe.calc_ut(
            julian_day, planet_id, swe.FLG_SWIEPH
        )
        planet_tropical_positions[name] = tropical_position[0]  # Only the longitude is needed

        # Get sidereal position
        sidereal_position, _ = swe.calc_ut(
            julian_day, planet_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        )
        planet_sidereal_positions[name] = sidereal_position[0]

    # Adjust Ketu's position to be opposite Rahu
    planet_tropical_positions["Ketu"] = (planet_tropical_positions["Rahu"] + 180) % 360
    planet_sidereal_positions["Ketu"] = (planet_sidereal_positions["Rahu"] + 180) % 360

    return planet_tropical_positions, planet_sidereal_positions, houses

@log_function
def degree_to_nakshatra(degree):
    # There are 27 Nakshatras each covering 13 degrees 20 minutes (13.3333 degrees)
    nakshatra_list = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
        'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
        'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
        'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati'
    ]
    nakshatra_degree = 13 + (20 / 60)  # 13 degrees 20 minutes
    index = int(degree / nakshatra_degree) % 27
    position_in_nakshatra = degree % nakshatra_degree
    return nakshatra_list[index], position_in_nakshatra

@log_function
def degree_to_zodiac(degree):
    zodiac_signs = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]
    index = int(degree / 30) % 12
    position_in_zodiac = degree % 30
    return zodiac_signs[index], position_in_zodiac

@log_function
def calculate_pada(position_in_nakshatra):
    # Each Nakshatra is divided into 4 padas (quarters)
    pada = int(position_in_nakshatra / (13.3333 / 4)) + 1
    return pada

@log_function
def find_house(planet_degree, houses):
    # houses[] contains cusps of houses 1 to 12
    # We need to find in which house the planet's degree falls
    for i in range(12):
        house_start = houses[i]
        house_end = houses[(i + 1) % 12]
        if house_end < house_start:
            house_end += 360  # Adjust for wrap-around
        planet_pos = planet_degree
        if planet_pos < house_start:
            planet_pos += 360
        if house_start <= planet_pos < house_end:
            return i + 1  # Houses are numbered from 1 to 12
    return None

@log_function
def check_exaltation_debilitation(planet, zodiac_sign):
    if planet in exaltation_signs and exaltation_signs[planet] == zodiac_sign:
        return 'Exalted'
    elif planet in debilitation_signs and debilitation_signs[planet] == zodiac_sign:
        return 'Debilitated'
    else:
        return 'Normal'

@log_function
def calculate_aspects(planet_positions):
    aspects = {}
    # Vedic aspects
    for planet, degree in planet_positions.items():
        aspects[planet] = []
        for other_planet, other_degree in planet_positions.items():
            if planet == other_planet:
                continue
            aspect_info = check_aspect(planet, degree, other_planet, other_degree)
            if aspect_info:
                aspects[planet].append(aspect_info)
    return aspects

@log_function
def check_aspect(planet, degree, other_planet, other_degree):
    # In Vedic astrology, all planets aspect the 7th house from their position
    # Some planets have special aspects
    aspect_degrees = []
    if planet == 'Mars':
        aspect_degrees = [(degree + 120) % 360,  # 4th house aspect
                          (degree + 180) % 360,  # 7th house aspect
                          (degree + 210) % 360]  # 8th house aspect
    elif planet == 'Jupiter':
        aspect_degrees = [(degree + 150) % 360,  # 5th house aspect
                          (degree + 180) % 360,  # 7th house aspect
                          (degree + 210) % 360]  # 9th house aspect
    elif planet == 'Saturn':
        aspect_degrees = [(degree + 90) % 360,   # 3rd house aspect
                          (degree + 180) % 360,  # 7th house aspect
                          (degree + 270) % 360]  # 10th house aspect
    else:
        aspect_degrees = [(degree + 180) % 360]  # 7th house aspect

    # Check if other_planet is within orb of aspect degrees
    orb = 5  # degree orb for aspects
    for aspect_degree in aspect_degrees:
        diff = abs(aspect_degree - other_degree)
        if diff > 180:
            diff = 360 - diff
        if diff <= orb:
            # Return aspect information
            return {
                'aspecting_planet': planet,
                'aspected_planet': other_planet,
                'aspect_type': 'Full' if planet not in ['Mars', 'Jupiter', 'Saturn'] else 'Special',
                'orb': diff
            }
    return None

@log_function
def calculate_life_path_number(birthdate):
    # Sum the digits of day, month, and year
    numbers = [int(char) for char in birthdate if char.isdigit()]
    total = sum(numbers)

    # Reduce to a single-digit number or master number
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    return total

@log_function
def calculate_expression_number(name):
    # Pythagorean numerology letter values
    letter_values = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }
    name = name.upper()
    total = sum(letter_values[char] for char in name if char.isalpha())

    # Reduce to single-digit or master number
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    return total

@log_function
def calculate_soul_urge_number(name):
    vowels = "AEIOU"
    letter_values = {"A": 1, "E": 5, "I": 9, "O": 6, "U": 3}
    name = name.upper()
    total = sum(letter_values[char] for char in name if char in vowels)

    # Reduce to single-digit or master number
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    return total

@log_function
def calculate_personality_number(name):
    vowels = "AEIOU"
    letter_values = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
        "G": 7,
        "H": 8,
        "I": 9,
        "J": 1,
        "K": 2,
        "L": 3,
        "M": 4,
        "N": 5,
        "O": 6,
        "P": 7,
        "Q": 8,
        "R": 9,
        "S": 1,
        "T": 2,
        "U": 3,
        "V": 4,
        "W": 5,
        "X": 6,
        "Y": 7,
        "Z": 8,
    }
    name = name.upper()
    total = sum(
        letter_values[char] for char in name if char.isalpha() and char not in vowels
    )

    # Reduce to single-digit or master number
    while total > 9 and total not in [11, 22, 33]:
        total = sum(int(digit) for digit in str(total))

    return total

@log_function
def calculate_numerology(birthdate, name):
    return {
        "Life Path": numerology_interpretations["Life Path"][
            calculate_life_path_number(birthdate)
        ],
        "Expression": numerology_interpretations["Expression"][
            calculate_expression_number(name)
        ],
        "Soul Urge": numerology_interpretations["Soul Urge"][
            calculate_soul_urge_number(name)
        ],
        "Personality": numerology_interpretations["Personality"][
            calculate_personality_number(name)
        ],
        "Precautions": numerology_interpretations["Precautions"][
            calculate_personality_number(name)
        ],
    }

@log_function
def calculate_vimshottari_dasha(moon_nakshatra, moon_position_in_nakshatra):
    """
    Calculate the Vimshottari Dasha sequence based on the Moon's Nakshatra and its position within that Nakshatra.

    Parameters:
    - moon_nakshatra (str): Name of the Moon's Nakshatra at the time of birth.
    - moon_position_in_nakshatra (float): Position of the Moon within the Nakshatra in degrees (0 - 13.3333).

    Returns:
    - list of tuples: A list of tuples where each tuple contains the Dasha lord and the Dasha period in years.
    """

    # Constants
    NAKSHATRA_DEGREES = 13 + (20 / 60)  # 13 degrees 20 minutes (13.3333 degrees)
    TOTAL_DASHA_YEARS = 120
    EPSILON = 1e-6  # Small value to handle floating-point precision

    # Validate inputs
    if not (0 <= moon_position_in_nakshatra <= NAKSHATRA_DEGREES):
        raise ValueError("moon_position_in_nakshatra must be between 0 and 13.3333 degrees.")

    # List of Nakshatras in order
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
        "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
        "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]

    # Sequence of Nakshatra rulers in Vimshottari Dasha order
    nakshatra_rulers_sequence = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
    ]

    # Mapping of Nakshatras to their ruling planets
    nakshatra_to_ruler = {}
    for i, nakshatra in enumerate(nakshatras):
        ruler = nakshatra_rulers_sequence[i % len(nakshatra_rulers_sequence)]
        nakshatra_to_ruler[nakshatra] = ruler

    # Dasha periods in years for each planet
    dasha_periods = {
        "Ketu": 7,
        "Venus": 20,
        "Sun": 6,
        "Moon": 10,
        "Mars": 7,
        "Rahu": 18,
        "Jupiter": 16,
        "Saturn": 19,
        "Mercury": 17
    }

    # Get the starting Dasha lord based on the Moon's Nakshatra
    starting_dasha_lord = nakshatra_to_ruler.get(moon_nakshatra)
    if starting_dasha_lord is None:
        raise ValueError(f"Invalid moon_nakshatra: {moon_nakshatra}")

    starting_dasha_period = dasha_periods[starting_dasha_lord]

    # Calculate remaining period for the starting Dasha lord
    remaining_period = starting_dasha_period * (
        1 - (moon_position_in_nakshatra / NAKSHATRA_DEGREES)
    )
    remaining_period = max(0, remaining_period)  # Ensure it's not negative

    # Generate the full Dasha sequence
    dasha_sequence = []
    current_dasha_lord = starting_dasha_lord
    years_left_in_cycle = TOTAL_DASHA_YEARS - remaining_period

    # Add the remaining period of the starting Dasha
    if remaining_period > EPSILON:
        dasha_sequence.append((current_dasha_lord, round(remaining_period, 2)))

    # Get the starting index for dasha sequence
    start_index = nakshatra_rulers_sequence.index(current_dasha_lord) + 1

    # Loop through the Vimshottari sequence to complete the cycle
    while years_left_in_cycle > EPSILON:
        next_dasha_lord = nakshatra_rulers_sequence[start_index % len(nakshatra_rulers_sequence)]
        dasha_period = dasha_periods[next_dasha_lord]

        # Adjust the last period if necessary
        if years_left_in_cycle < dasha_period:
            dasha_period = years_left_in_cycle

        years_left_in_cycle -= dasha_period
        dasha_sequence.append((next_dasha_lord, round(dasha_period, 2)))
        start_index += 1

    return dasha_sequence

@log_function
def calculate_pada(position_in_nakshatra):
    if 0 <= position_in_nakshatra < 3.3333:
        return 1
    elif 3.3333 <= position_in_nakshatra < 6.6666:
        return 2
    elif 6.6666 <= position_in_nakshatra < 10:
        return 3
    elif 10 <= position_in_nakshatra <= 13.3333:
        return 4

@log_function
def get_gemstones(moon_sign, sun_sign, ascendant_sign=None):
    """
    Recommend gemstones based on Moon sign, Sun sign, and optionally Ascendant sign.

    Parameters:
    - moon_sign (str): The user's Moon sign.
    - sun_sign (str): The user's Sun sign.
    - ascendant_sign (str, optional): The user's Ascendant (Lagna) sign.

    Returns:
    - list of dicts: A list containing recommended gemstones with detailed information.
    """

    # Mapping of zodiac signs to gemstones and planetary influences


    recommendations = []

    # Helper function to get gemstone info
    def get_gemstone_info(sign, preferred_sign):
        gem_info = SIGN_GEMSTONES_RECCOMMENDED.get(sign)
        if gem_info:
            return {
                "Preferred Sign": preferred_sign,
                "Sign": sign,
                "Recommended Gemstone": gem_info["gemstone"],
                "Planetary Influence": gem_info["planet"],
                "Properties": gem_info["properties"],
                "Why":gem_info["why"]
            }
        else:
            return None

    # Prioritize Moon sign
    moon_recommendation = get_gemstone_info(moon_sign, "Moon Sign")
    if moon_recommendation:
        recommendations.append(moon_recommendation)

    # Check Sun sign if Moon sign recommendation isn't available or as additional info
    if sun_sign != moon_sign:
        sun_recommendation = get_gemstone_info(sun_sign, "Sun Sign")
        if sun_recommendation:
            recommendations.append(sun_recommendation)

    # Consider Ascendant sign as an additional option
    if ascendant_sign and ascendant_sign not in [moon_sign, sun_sign]:
        ascendant_recommendation = get_gemstone_info(ascendant_sign, "Ascendant Sign")
        if ascendant_recommendation:
            recommendations.append(ascendant_recommendation)

    # If no recommendations found
    if not recommendations:
        return [
            {
                "Message": "No specific gemstone recommendation found for your signs.",
                "Suggestion": "Consider consulting a professional astrologer for personalized guidance.",
            }
        ]

    return recommendations

@log_function
def interpret_dasha_sequence(dasha_sequence, chart_data):
    """
    Interpret the Vimshottari Dasha sequence based on the Dasha lords and the user's chart data.

    Parameters:
    - dasha_sequence (list of tuples): Each tuple contains the Dasha lord (str) and the Dasha period in years (float).
    - chart_data (dict): The user's chart data generated by the generate_chart function.

    Returns:
    - list of dicts: A list where each dictionary contains the Dasha lord, period, and interpretation.
    """
    # General significations of planets
    planet_significations = {
        "Sun": "authority, vitality, leadership",
        "Moon": "emotions, mind, family",
        "Mars": "energy, courage, action",
        "Mercury": "communication, intellect, business",
        "Jupiter": "wisdom, expansion, prosperity",
        "Venus": "love, relationships, art",
        "Saturn": "discipline, responsibility, challenges",
        "Rahu": "desires, materialism, unexpected events",
        "Ketu": "spirituality, detachment, introspection"
    }

    interpretations = []

    planetary_data = chart_data  # The chart data now includes all necessary details

    for dasha_lord, period in dasha_sequence:
        # Retrieve information about the Dasha lord from the chart data
        planet_info = planetary_data.get(dasha_lord, {}).get('sidereal', {})
        house = planet_info.get('house', 'unknown house')
        zodiac = planet_info.get('zodiac', 'unknown sign')
        nakshatra = planet_info.get('nakshatra', 'unknown nakshatra')
        pada = planet_info.get('pada', 'unknown pada')
        status = planet_info.get('status', 'Normal')

        # Retrieve aspects involving the Dasha lord
        aspects = chart_data.get('aspects', {}).get(dasha_lord, [])

        # Begin interpretation
        interpretation = f"**{dasha_lord} Dasha ({period} years):**\n"
        interpretation += f"- **Placement**: {dasha_lord} is in the {house} house, in the sign of {zodiac}.\n"
        interpretation += f"- **Nakshatra**: {nakshatra}, Pada {pada}.\n"
        interpretation += f"- **Status**: {status}.\n"

        # Add aspects
        if aspects:
            aspected_planets = [aspect['aspected_planet'] for aspect in aspects]
            interpretation += f"- **Aspects**: {dasha_lord} aspects {', '.join(aspected_planets)}.\n"

        # General significations
        significations = planet_significations.get(dasha_lord, "various areas of life")
        interpretation += f"- **General Influences**: This period influences {significations}.\n"

        # Include personalized insights
        interpretation += "- **Personalized Insights**: "

        # Example personalized insights based on house placement
        house = str(house)  # Ensure house is a string for comparison
        if house == '1':
            interpretation += "Focus on self-development, health, and personal endeavors. "
        elif house == '2':
            interpretation += "Emphasis on finances, family values, and speech. "
        elif house == '3':
            interpretation += "Enhancement of communication skills, courage, and sibling relationships. "
        elif house == '4':
            interpretation += "Matters related to home, mother, and inner peace may prevail. "
        elif house == '5':
            interpretation += "Creative pursuits, education, and children could be significant. "
        elif house == '6':
            interpretation += "Attention to health, service, and overcoming obstacles. "
        elif house == '7':
            interpretation += "Relationships and partnerships may take center stage. "
        elif house == '8':
            interpretation += "Transformation, research, and dealing with shared resources. "
        elif house == '9':
            interpretation += "Spirituality, higher learning, and long journeys may be prominent. "
        elif house == '10':
            interpretation += "Career advancements and public image are likely to be highlighted. "
        elif house == '11':
            interpretation += "Gains, social networks, and fulfillment of desires could occur. "
        elif house == '12':
            interpretation += "Focus on introspection, expenses, and possibly foreign connections. "
        else:
            interpretation += f"Influences related to house {house}. "

        # Include status in interpretation
        if status == 'Exalted':
            interpretation += f"{dasha_lord} is exalted, potentially bringing positive and strong results. "
        elif status == 'Debilitated':
            interpretation += f"{dasha_lord} is debilitated, which may present challenges requiring extra effort. "

        # Consider aspects in interpretation
        if aspects:
            for aspect in aspects:
                aspected_planet = aspect['aspected_planet']
                aspect_type = aspect['aspect_type']
                orb = aspect['orb']
                interpretation += f"{dasha_lord} {aspect_type.lower()} aspects {aspected_planet} within {orb} degrees. This connection can influence matters related to {aspected_planet}'s significations. "

        # Finish the interpretation
        interpretation += "\n"

        # Append to the interpretations list
        interpretations.append({
            'dasha_lord': dasha_lord,
            'period': period,
            'interpretation': interpretation
        })

    return interpretations

@log_function
def suggest_pujas_with_reasoning(data, pujas, user_preferences=None):
    try:
        """
        Suggests up to 5 relevant Pujas based on the user's astrological chart with personalized reasoning.

        Parameters:
        - data (dict): The JSON data containing astrological information.
            Expected structure based on provided input.
        - pujas (list of dicts): List of Puja details.
        - user_preferences (list, optional): User-specified focus areas (e.g., ["wealth", "health"]).

        Returns:
        - suggestions (list of dicts): Up to 5 Puja suggestions with personalized reasons.
        """

        suggestions = []
        # Extract relevant chart data
        chart_data = data.get('chart_data', {})
        current_dasha_lord = data.get('current_dasha_lord', None)
        planet_status = {}
        house_placements = {}
        afflicted_planets = []

        # Compile planetary statuses and house placements
        for planet, details in chart_data.items():
            if planet == "aspects":
                continue  # Skip aspects for now
            sidereal = details.get('sidereal', {})
            status = sidereal.get('status', 'Normal')
            house = sidereal.get('house', None)
            planet_status[planet] = status
            if house:
                house_placements[planet] = house
            if status in ['Debilitated', 'Afflicted']:
                afflicted_planets.append(planet)
        # Function to calculate Puja relevance score
        def calculate_score(puja):
            score = 0
            reasons = []
            # 1. Dasha Lord Match
            if current_dasha_lord and current_dasha_lord in puja.get('Associated Planets', []):
                score += 3
                reasons.append(f"Aligns with your current **{current_dasha_lord} Dasha**, enhancing its effectiveness.")

            # 2. Planetary Status Match
            for planet in puja.get('Associated Planets', []):
                status = planet_status.get(planet, "Normal")
                if status == 'Exalted' and puja.get('Special Conditions', {}).get('Exaltation', False):
                    score += 2
                    reasons.append(f"**{planet}** is exalted, amplifying the benefits of this Puja.")
                elif status == 'Debilitated' and puja.get('Special Conditions', {}).get('Debilitation', False):
                    score += 2
                    reasons.append(f"**{planet}** is debilitated, and this Puja can help mitigate its effects.")

            # 3. House Placement Match
            for house in puja.get('Associated Houses', []):
                for planet, planet_house in house_placements.items():
                    if planet_house == house:
                        score += 1
                        reasons.append(f"**{planet}** occupies your **{house}th house**, resonating with this Puja's purpose.")
                        break  # Avoid multiple matches for the same house

            # 4. Afflicted Planets Match
            for planet in puja.get('Associated Planets', []):
                if planet in afflicted_planets:
                    score += 2
                    reasons.append(f"**{planet}** is currently afflicted, and this Puja can help alleviate its negative impacts.")

            # 5. User Preferences Match
            if user_preferences:
                puja_purpose = puja.get('Life Aspect', '').lower()
                matched_preferences = [pref for pref in user_preferences if pref.lower() in puja_purpose]
                if matched_preferences:
                    score += len(matched_preferences)  # More matches, higher score
                    prefs = ', '.join([f"**{pref}**" for pref in matched_preferences])
                    reasons.append(f"Supports your focus on {prefs}, aiding in your personal goals.")

            return score, reasons

        # Score each Puja and collect reasons
        puja_scores = []
        for puja in pujas['Selected Pujas']:
            score, reasons = calculate_score(puja)
            if score > 0:
                puja_scores.append({
                    'Puja': puja,
                    'Score': score,
                    'Reasons': reasons
                })

        # Sort Pujas by score in descending order
        puja_scores_sorted = sorted(puja_scores, key=lambda x: x['Score'], reverse=True)

        # Select top 5 Pujas
        top_pujas = puja_scores_sorted[:5]

        # Generate suggestions with personalized reasons
        for puja_entry in top_pujas:
            puja = puja_entry['Puja']
            reasons = puja_entry['Reasons']
            puja_name = puja.get("Puja Name", "Unnamed Puja")
            purpose = puja.get("Life Aspect", "")

            # Craft the reason narrative
            reason_paragraph = " ".join(reasons)
            personalized_message = f"Based on your astrological chart, we recommend the following Puja to address your current life aspects:\n\n**{puja_name}**: {reason_paragraph} Engaging in this Puja can help harmonize your energies and support your personal growth."

            suggestions.append({
                'Puja Name': puja_name,
                'Reason': personalized_message
            })

        return suggestions
    except Exception as e:
        print(f"Error in suggest_pujas_with_reasoning: {e}")
        return []


pujas = pujas = [
    {
        "Puja Name": "Rudrabhishek Puja",
        "Deity": "Lord Shiva",
        "Benefits": "Enhances inner strength, removes obstacles, and provides divine protection.",
        "Ideal For": "Individuals seeking resilience and protection from negative influences."
    },
    {
        "Puja Name": "Satyanarayan Puja",
        "Deity": "Lord Satyanarayan",
        "Benefits": "Invokes prosperity, peace, and fulfillment of desires.",
        "Ideal For": "Families and individuals aiming for overall well-being and prosperity."
    },
    {
        "Puja Name": "Maha Ganpati Homa",
        "Deity": "Lord Ganesha",
        "Benefits": "Removes obstacles, seeks wisdom, and ensures success in endeavors.",
        "Ideal For": "Individuals facing challenges in personal or professional life."
    },
    {
        "Puja Name": "Ganesh Chaturthi Puja",
        "Deity": "Lord Ganesha",
        "Benefits": "Celebrates Lord Ganesha's birth, bringing prosperity and removing barriers.",
        "Ideal For": "Communities and families celebrating Ganesh Chaturthi."
    },
    {
        "Puja Name": "Navagraha Puja",
        "Deity": "Navagrahas",
        "Benefits": "Balances the energies of all nine planets, ensuring harmony and prosperity.",
        "Ideal For": "Individuals seeking overall planetary balance and harmony."
    },
    {
        "Puja Name": "Lakshmi Puja",
        "Deity": "Goddess Lakshmi",
        "Benefits": "Invokes Goddess Lakshmi for wealth, prosperity, and abundance.",
        "Ideal For": "Individuals and families seeking financial stability and growth."
    },
    {
        "Puja Name": "Surya Puja",
        "Deity": "Surya (Sun God)",
        "Benefits": "Enhances vitality, authority, and leadership qualities by honoring the Sun.",
        "Ideal For": "Individuals aiming to boost confidence and leadership skills."
    },
    {
        "Puja Name": "Shani Shanti Puja and Jaap",
        "Deity": "Shani (Saturn)",
        "Benefits": "Mitigates the malefic effects of Saturn, seeking peace and stability.",
        "Ideal For": "Individuals experiencing challenges related to Saturn in their chart."
    },
    {
        "Puja Name": "Durga Puja",
        "Deity": "Goddess Durga",
        "Benefits": "Celebrates the victory of Goddess Durga over evil, seeking strength and protection.",
        "Ideal For": "Individuals seeking empowerment and protection from negative forces."
    },
    {
        "Puja Name": "Saraswati Puja",
        "Deity": "Goddess Saraswati",
        "Benefits": "Invokes Goddess Saraswati for wisdom, knowledge, and artistic talents.",
        "Ideal For": "Students, educators, and artists seeking intellectual and creative enhancement."
    },
    {
        "Puja Name": "Maha Shivratri Puja",
        "Deity": "Lord Shiva",
        "Benefits": "Celebrates Lord Shiva's cosmic dance, seeking spiritual growth and liberation.",
        "Ideal For": "Individuals pursuing spiritual enlightenment and inner peace."
    },
    {
        "Puja Name": "Hanuman Chalisa Path",
        "Deity": "Lord Hanuman",
        "Benefits": "Seeks strength, courage, and protection by reciting the Hanuman Chalisa.",
        "Ideal For": "Individuals seeking mental and physical strength and protection from negative forces."
    },
    {
        "Puja Name": "Vastu Shanti Puja",
        "Deity": "Navagrahas",
        "Benefits": "Harmonizes the energies of living or workspace, ensuring peace and prosperity.",
        "Ideal For": "Individuals or businesses looking to align their environment with cosmic energies."
    },
    {
        "Puja Name": "Navaratri Durga Puja",
        "Deity": "Goddess Durga",
        "Benefits": "Seeks Goddess Durga's blessings for strength, courage, and success during Navaratri.",
        "Ideal For": "Individuals seeking empowerment and success during the Navaratri festival."
    },
    {
        "Puja Name": "Mangal Shanti Puja",
        "Deity": "Lord Hanuman and Lord Mangal",
        "Benefits": "Alleviates the malefic effects of Mars, seeking harmony and peace.",
        "Ideal For": "Individuals experiencing challenges related to Mars in their chart."
    },
    {
        "Puja Name": "Pitru Paksha Puja",
        "Deity": "Pitrs (Ancestors)",
        "Benefits": "Honors and appeases ancestors, seeking their blessings and peace.",
        "Ideal For": "Individuals wishing to honor their forefathers and seek their blessings."
    },
    {
        "Puja Name": "Dhanteras Puja",
        "Deity": "Lord Dhanvantari and Goddess Lakshmi",
        "Benefits": "Seeks wealth and prosperity, inaugurating new ventures or purchases.",
        "Ideal For": "Individuals starting new business ventures or making significant purchases."
    },
    {
        "Puja Name": "Diwali Lakshmi Puja",
        "Deity": "Goddess Lakshmi",
        "Benefits": "Celebrates Diwali by worshipping Goddess Lakshmi for wealth and prosperity.",
        "Ideal For": "Individuals and families celebrating Diwali, seeking prosperity and dispelling negativity."
    },
    {
        "Puja Name": "Saraswati Vidya Ganpati Homa",
        "Deity": "Goddess Saraswati and Lord Ganesha",
        "Benefits": "Invokes knowledge, wisdom, and removal of obstacles in learning and creativity.",
        "Ideal For": "Students, educators, and creative individuals seeking intellectual growth."
    }
]

@log_function
def see_more_life_predictions(birth_chart, name, previous_content, area):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        temperature=0.1,
        system="""You are an AI astrologer specializing in providing detailed life predictions based on a user's birth chart. When provided with the name of an area, the user's birth chart, their name, and the previously generated content for that area, generate additional insights and practical advice to enhance the existing information.

                **Instructions:**

                1. **Input Data**: You will receive the following inputs:
                    - **Name**: The user's name.
                    - **Birth Chart**: Detailed astrological data enclosed between `<birth_chart>` and `</birth_chart>` tags.
                    - **Area**: The specific area to update (e.g., Personality, Relationships, Career, Learning, Personal Growth).
                    - **Previous Content**: The existing content for the specified area enclosed within `<previous_content>` and `</previous_content>` tags.

                2. **Generate Additional Content**:
                    - **Intro Expansion**: Provide further insights related to the specified area, building upon the previous introduction. Maintain a balanced outlook by highlighting both positive and challenging aspects.
                    - **Additional Improvements**: Suggest 2 to 3 new practical steps or advice to enhance the user's experience in the specified area.

                3. **Guidelines**:
                    - Use astrological terminology with brief explanations for clarity.
                    - Maintain a respectful and supportive tone, avoiding absolute statements.
                    - Present astrology as a tool for self-reflection and personal growth.
                    - Ensure the additional content seamlessly integrates with the existing content.
                    - Avoid overloading the user with too much information. 
                    - There should not be any duplication of information from the previous content.

                4. **Length Constraint**: Limit the total output for the additional content to 500 characters.

                **Output Format:**
                <predictions>
                <additional_content>
                    <improvements>[2 to 3 additional steps to improve the user area]</improvements>
                </additional_content>
                </predictions>
                """,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>.\nToday's date is {datetime.today().strftime('%Y-%m-%d')}\n<previous_content>{previous_content}</previous_content>",
                    }
                ],
            }
        ],
    )
    print(
        "For See More Life Predictions, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    data = extract_text_between_patterns(message.content[0].text, "predictions")
    # Parse the XML data
    root = ET.fromstring(f"<root>{data}</root>")  # Wrapping with a root tag to ensure well-formed XML

    # Initialize the final dictionary
    life_predictions = {}

    # Iterate over each main section
    for section in root:
        section_name = section.tag.replace('_', ' ')  # Replace underscores with spaces if any
        improvements_text = section.find('improvements').text.strip()
        improvements = extract_improvements(improvements_text)
        
        # Add to the dictionary
        life_predictions[section_name] = {
            "improvements": improvements
        }
    return life_predictions


# Function to extract improvements as a list
@log_function
def extract_improvements(improvements_text):
    # Use regex to find all numbered points
    pattern = r'\d+\.\s+(.*?)(?=\n\d+\.|$)'
    matches = re.findall(pattern, improvements_text, re.DOTALL)
    # Strip any leading/trailing whitespace from each improvement
    improvements = [match.strip() for match in matches]
    return improvements

@log_function
def get_life_predictions(birth_chart, name):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        temperature=0.1,
        system="""You are an AI astrologer. Analyze the user's birth chart provided between `<birth_chart>` and `</birth_chart>` tags to generate a balanced life prediction.
        Instructions:
        1. **Chart Analysis**: Enclose a concise interpretation within `<chart_analysis>` tags, including:
        - Key planetary positions in signs and houses
        - Major aspects between planets
        - Significant patterns or configurations
        2. Life Predictions: For each area below, provide:
        - Relevant astrological interpretations
        - A balanced outlook (positive and challenging aspects)
        - Practical advice or suggestions
        Areas:
        - Personality
        - Relationships
        - Family
        - Social
        - Career
        - Learning
        - Personal Growth

        3. Guidelines:
        - Use astrological terms with brief explanations for clarity
        - Be respectful and avoid absolute statements
        - Present astrology as a tool for self-reflection
        - Keep the tone simple and user friendly

        4. Length Constraint: Limit the total output to 1500 characters.

        Output Format:
        ```
        <chart_analysis>
        [Concise interpretation of the birth chart]
        </chart_analysis>

        <predictions>
            <name_of_area>
                <intro>[Brief interpretation of the user area]</intro>
                <improvements>1. [First improvement]\n2. [Second improvement]\n3. [Third improvement]</improvements>
            </name_of_area>
        </predictions>
        ```
        Ensure each section is substantive. If information is lacking, infer from related astrological factors.""",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>.\nToday's date is {datetime.today().strftime('%Y-%m-%d')}",
                    }
                ],
            }
        ],
    )
    print(
        "For Life Prediction, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    data = extract_text_between_patterns(message.content[0].text, "predictions")
    # Parse the XML data
    root = ET.fromstring(f"<root>{data}</root>")  # Wrapping with a root tag to ensure well-formed XML

    # Initialize the final dictionary
    life_predictions = {}

    # Iterate over each main section
    for section in root:
        section_name = section.tag.replace('_', ' ')  # Replace underscores with spaces if any
        intro = section.find('intro').text.strip()
        improvements_text = section.find('improvements').text.strip()
        improvements = extract_improvements(improvements_text)
        
        # Add to the dictionary
        life_predictions[section_name] = {
            "intro": intro,
            "improvements": improvements
        }
    return life_predictions

dosh_knowledge_graph = {
  "Mangal Dosha": {
      "CausedBy": "Placement of Mars in specific houses",
      "SpecificHouses": ["1st", "2nd (South Indian charts)", "4th", "7th", "8th", "12th"],
      "OtherNames": ["Kuja Dosha", "Manglik Dosh"],
      "Description": "Occurs when Mars is not in a favorable position in the Kundli, impacting married life.",
      "Impacts": "Imbalance and challenges in married life.",
      "Remedies": ["Marry a banana tree", "Perform specific pujas to mitigate dosh"]
    },
    "Kaal Sarp Dosha": {
      "CausedBy": "All planets positioned between Rahu and Ketu",
      "Description": "Brings struggles and is considered highly challenging, leading to failures and misfortunes.",
      "Impacts": "Series of failures and misfortunes in life.",
      "ExampleAlignment": {
        "Rahu": "Aries",
        "Ketu": "Scorpio",
        "OtherPlanets": ["Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra"]
      },
      "Remedies": ["Perform pujas to alleviate the effects", "Seek astrological guidance"]
    },
    "Nadi Dosha": {
      "CausedBy": "Same Nadi in both individuals of a potential couple",
      "NadiTypes": ["Aadi", "Madhya", "Antya"],
      "Description": "Affects aspects related to children, health, and genetics in marriage.",
      "Impacts": "Issues related to children in the couple's life.",
      "Remedies": ["Specific matchmaking pujas", "Perform remedies to balance nadis"]
    },
    "Pitru Dosha": {
      "CausedBy": "Placement of Sun or Moon in conjunction/aspect with Rahu or Ketu",
      "SignificantHouses": ["1st", "5th", "8th", "9th"],
      "Description": "Linked to karmic debts of ancestors, causing suffering and disruptions.",
      "Impacts": "Personal issues, relationship problems with family and society.",
      "Remedies": ["Perform Pitru Shanti pujas", "Offer prayers to ancestors"]
    },
    "Guru Chandal Dosh": {
      "CausedBy": "Placement of Jupiter with Rahu or Ketu",
      "Description": "Overrides the positive effects of Jupiter, causing instability.",
      "Impacts": "Hindrance in wealth, education, and optimism.",
      "Remedies": ["Perform Guru Chandal Dosha mitigation pujas", "Strengthen Jupiter through rituals"]
    },
    "Gandmool Dosh": {
      "CausedBy": "Birth in Nakshatras ruled by Mercury and Ketu",
      "AffectedNakshatras": ["Ashwin", "Ashlesha", "Magha", "Jyestha", "Moola", "Revati"],
      "Description": "Affects the closest family members, especially parents.",
      "Impacts": "Misfortunes for closest family members.",
      "Remedies": ["Perform Gandmool Dosh specific pujas", "Offer remedies to appease Mercury and Ketu"]
    },
    "Shani Dosh": {
      "CausedBy": "Placement of Saturn in malefic houses",
      "Forms": ["Sade Saati", "Shani Dhaiya", "Mahadasha of Shani"],
      "Description": "Can bring adversities if Saturn is malefic in the Kundli.",
      "Impacts": "Severe challenges depending on Saturn's placement.",
      "Remedies": ["Shani Shanti pujas", "Worship Lord Shani", "Wear specific gemstones"]
    },
    "Shrapit Dosh": {
      "CausedBy": "Conjunction of Saturn and Rahu in a single house",
      "Description": "Brings obstacles and delays in achieving success.",
      "Impacts": "Series of obstacles and delays in life goals.",
      "Remedies": ["Perform Shrapit Dosh mitigation pujas", "Seek astrological remedies to balance Saturn and Rahu"]
    },
    "Chandra Dosh": {
      "CausedBy": "Moon in conjunction/aspect with Rahu or Ketu",
      "Description": "Leads to unwanted thoughts, pessimism, and depression.",
      "Impacts": "Mental hardships like depression and pessimism.",
      "Remedies": ["Wear a Pearl gemstone", "Perform Chandra Shanti pujas"]
    },
    "Kemadruma Dosh": {
      "CausedBy": "Moon with both neighboring houses (2nd and 12th) vacant",
      "Description": "Causes misfortune unless countered by specific planetary placements.",
      "Impacts": "Potential misfortunes based on other planetary influences.",
      "Remedies": ["Perform Kemadruma Dosh specific pujas", "Seek guidance from an experienced astrologer"]
    }
}

@log_function
async def get_pujas(birth_chart, name):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1800,
        temperature=0.1,
        system="""You are an AI Pujas Suggestor specializing in Indian Astrology. Analyze the user's birth chart provided between `<birth_chart>` and `</birth_chart>` tags to generate a list of Pujas that will help the user improve their life.

                **Instructions:**

                1. **Chart Analysis**: Enclose a concise interpretation within `<chart_analysis>` tags, including:
                    - Key planetary positions in signs and houses
                    - Major aspects between planets
                    - Significant patterns or configurations
                    - **Dosh Analysis**: Identify and describe any dosh (e.g., Mangal Dosha, Shani Dosha) present in the kundali. If dosh exists, explain its potential impacts on the user's life. For analysis of dosh, use the following knowledge graph: {dosh_knowledge_graph}
                2. **Pujas Suggestion**: Enclose the suggestions within `<puja_details>` tags in HTML format.
                    - **If Dosh Exists**:
                        - Emphasize pujas that specifically address and mitigate the identified dosh to enhance their effectiveness.
                    - **If No Dosh Exists**:
                        - Provide general pujas aimed at overall spiritual well-being and life improvement.
                    - **Give me one puja for each of the following areas**:
                        - **Career**
                        - **Family**
                        - **Love**
                        - **Social**
                        - **Self**
                    - **For Each Puja**, include the following details:
                        1. **Puja Name**
                        2. **Puja Description**
                        3. **Why this Puja is important for the user**
                        4. **When to perform this Puja**
                        5. **How to perform this Puja**
                        6. **Puja Benefits**
                        7. **Puja Duration**
                3. **Guidelines:**
                    - Use user-friendly language, tone, and style.
                    - Be respectful and avoid absolute statements.
                    - Address the user by their name in the first person or call them you dont use terms like "user".
                    - Present this with a hint of caution.
                    - Ensure that the pujas are not harmful to the user and are rooted in authentic Indian Astrology.
                    - Maintain the output in valid HTML format.

                4. **Length Constraint**: Limit the total output to 2000 characters.

                **Output Format:**
                <chart_analysis> [Concise interpretation of the birth chart, including dosh analysis if applicable] </chart_analysis>

                <puja_details>
                1.[Puja Name]
                - Puja Area
                - Puja Description
                - Why this Puja is important for the user
                - Puja Benefits
                ...
                </puja_details>
                """,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>.\nToday's date is {datetime.today().strftime('%Y-%m-%d')}",
                    }
                ],
            }
        ],
    )
    print(
        "Pujas, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    return extract_text_between_patterns(message.content[0].text, "puja_details")

@log_function
async def get_gemstone_recommendations(birth_chart, name):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1800,
        temperature=0.1,
        system="""You are an AI Gemstone Suggestor specializing in Indian Astrology. Analyze the user's birth chart provided between `<birth_chart>` and `</birth_chart>` tags to generate a list of Gemstones that will help the user improve their life.

                **Instructions:**

                1. **Chart Analysis**: Enclose a concise interpretation within `<chart_analysis>` tags, including:
                    - Key planetary positions in signs and houses
                    - Major aspects between planets
                    - Significant patterns or configurations
                2. **Gemstone Suggestion**: Enclose the suggestions within `<gemstone_details>` tags in HTML format.
                    - **Give me one gemstone for each of the following areas**:
                        - **Career**
                        - **Family**
                        - **Love**
                        - **Social**
                        - **Self**
                    - **For Each Gemstone**, include the following details:
                        1. **Gemstone Name**
                        2. **Gemstone Description**
                        3. **Why this Gemstone is important for the user**
                        4. **Gemstone Benefits**
                3. **Guidelines:**
                    - Use user-friendly language, tone, and style.
                    - Be respectful and avoid absolute statements.
                    - Address the user by their name in the first person or call them you dont use terms like "user".
                    - Present this with a hint of caution.
                    - Ensure that the gemstones are not harmful to the user and are rooted in authentic Indian Astrology.
                    - Maintain the output in valid HTML format.

                4. **Length Constraint**: Limit the total output to 2000 characters.

                **Output Format:**
                <chart_analysis> [Concise interpretation of the birth chart, including dosh analysis if applicable] </chart_analysis>

                <gemstone_details>
                1.[Gemstone Name]
                - Gemstone Area
                - Gemstone Description
                - Why this Gemstone is important for the user
                - Gemstone Benefits
                ...
                </gemstone_details>
                """,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>.\nToday's date is {datetime.today().strftime('%Y-%m-%d')}",
                    }
                ],
            }
        ],
    )
    print(
        "GemStone, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    return extract_text_between_patterns(message.content[0].text, "gemstone_details")

@log_function
def see_more_horoscope(birth_chart, type, name, previous_content):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        temperature=0.1,
        system="""You are an AI Astrologer. Generate a personalized horoscope for the user based on their birth chart provided between `<birth_chart>` and `</birth_chart>` tags, and the type of horoscope they request between `<horoscope_type>` and `</horoscope_type>` tags. Additionally, review any previous horoscope content provided between `<previous_content>` and `</previous_content>` tags to enhance and expand the horoscope with more options and perspectives.
                Instructions:

                1. **User Input**:
                    - The user will specify the type of horoscope they want: daily, monthly, or yearly.

                2. **Data Analysis**:
                    - Analyze the user's birth chart.
                    - Consider current planetary transits and their interactions with the user's natal chart.
                    - Review any `<previous_content>` to understand existing insights.

                3. **Horoscope Generation**:
                    - Generate the horoscope according to the type specified by the user:

                        - **Daily Horoscope**:
                            - Focus on immediate influences and opportunities for the day.
                            - Keep it uplifting and actionable.
                            - Length: Up to 500 characters.

                        - **Monthly Horoscope**:
                            - Highlight key themes and potential events for the month.
                            - Mention significant astrological events (e.g., new/full moons, retrogrades).
                            - Length: Up to 800 characters.

                        - **Yearly Horoscope**:
                            - Outline major trends and developments for the year.
                            - Emphasize long-term growth, challenges, and opportunities.
                            - Length: Up to 1,200 characters.

                4. **Content Enhancement**:
                    - Review the `<previous_content>` and identify areas where additional insights or alternative viewpoints can be provided.
                    - Introduce new perspectives or deeper analysis to enrich the existing horoscope.
                    - Offer "see more options" by presenting alternative predictions or strategies for each relevant area.

                5. **Content Guidelines**:
                    - Cover areas that excite the user:
                        - Career
                        - Relationships
                        - Health
                        - Finance
                        - Personal Growth
                        - Spirituality
                        - Provide 3 to 5 steps that will help the user improve their life in the respective area.
                    - Use positive and encouraging language.
                    - Offer practical advice and suggestions.
                    - Avoid absolute predictions; present astrology as guidance.

                6. **Style Guidelines**:
                    - Use clear and engaging language.
                    - Briefly explain any astrological terms used.
                    - Be respectful and empathetic.

                7. **Guidelines**:
                    - Use astrological terms with brief explanations for clarity.
                    - Be respectful and avoid absolute statements.
                    - Present astrology as a tool for self-reflection.

                8. **Length Constraint**:
                    - Adhere to the specified character limits based on horoscope type.
                    - Ensure additional content fits within an overall reasonable length (e.g., up to 1,500 characters for enhanced content).

                9. **Output Format**:
                    - Provide the horoscope within the appropriate tags based on the user's request:
                        - `<daily_horoscope> ... </daily_horoscope>`
                        - `<monthly_horoscope> ... </monthly_horoscope>`
                        - `<yearly_horoscope> ... </yearly_horoscope>`
                    - Only include the horoscope type(s) requested by the user.
                    - For enhanced content, include additional sections such as:
                        - `[Additional insights or alternative perspectives]`
                        - `[See more options with alternative strategies]`

                Ensure each section is substantive and builds upon any existing `<previous_content>`. If information is lacking, infer from related astrological factors to provide comprehensive and enriched horoscopes.""",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>\n<horoscope_type>{type}</horoscope_type>\nToday's date is {datetime.today().strftime('%Y-%m-%d')}\n<previous_content>{previous_content}</previous_content>",
                    }
                ],
            }
        ],
    )
    print(
        "For See More Horoscope, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    return extract_text_between_patterns(message.content[0].text, f"{type}_horoscope")

@log_function
def get_horoscope(birth_chart, type, name):
    # Replace placeholders like {{BIRTHCHART}} with real values,
    # because the SDK does not support variables.
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1500,
        temperature=0.1,
        system="""You are an AI Astrologer. Generate a personalized horoscope for the user based on their birth chart provided between `<birth_chart>` and `</birth_chart>` tags, and the type of horoscope they request which will be between `<horoscope_type>` and `</horoscope_type>` tags

            Instructions:

            1. User Input:

            - The user will specify the type of horoscope they want: daily, monthly, or yearly.

            2. Data Analysis:

            - Analyze the user's birth chart.
            - Consider current planetary transits and their interactions with the user's natal chart.

            3. Horoscope Generation:

            - Generate the horoscope according to the type specified by the user:

                - Daily Horoscope:
                - Focus on immediate influences and opportunities for the day.
                - Keep it uplifting and actionable.
                - Length: Up to 500 characters.

                - Monthly Horoscope:
                - Highlight key themes and potential events for the month.
                - Mention significant astrological events (e.g., new/full moons, retrogrades).
                - Length: Up to 800 characters.

                - Yearly Horoscope:
                - Outline major trends and developments for the year.
                - Emphasize long-term growth, challenges, and opportunities.
                - Length: Up to 1,200 characters.

            4. Content Guidelines:

            - Cover areas that excite the user:
                - Career
                - Relationships
                - Health
                - Finance
                - Personal Growth
                - Spirituality
                -Write 3 to 5 steps that will help the user to improve their life in the respective area

            - Use positive and encouraging language.
            - Offer practical advice and suggestions.
            - Avoid absolute predictions; present astrology as guidance.

            5. Style Guidelines:

            - Use clear and engaging language.
            - Briefly explain any astrological terms used.
            - Be respectful and empathetic.

            6. Output Format:

            - Provide the horoscope within the appropriate tags based on the user's request:
                - `<daily_horoscope> ... </daily_horoscope>`
                - `<monthly_horoscope> ... </monthly_horoscope>`
                - `<yearly_horoscope> ... </yearly_horoscope>`

            - Only include the horoscope type(s) requested by the user.""",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"My name is {name}.\n<birth_chart>{birth_chart}</birth_chart>\n<horoscope_type>{type}</horoscope_type>\nToday's date is {datetime.today().strftime('%Y-%m-%d')}",
                    }
                ],
            }
        ],
    )
    print(
        "For Horoscope, Tokens = (",
        message.usage.input_tokens,
        message.usage.output_tokens,
        ")\nPrice: $",
        (message.usage.input_tokens / 1000000) * 0.25
        + (message.usage.output_tokens / 1000000) * 1.25,
    )
    return extract_text_between_patterns(message.content[0].text, f"{type}_horoscope")
