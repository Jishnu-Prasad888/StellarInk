from flask import Flask, request, jsonify
from flask_cors import CORS
from star_utils import StarConstellationGenerator
import json

app = Flask(__name__)
CORS(app)

# Initialize the star generator
star_gen = StarConstellationGenerator()

@app.route('/api/constellation', methods=['POST'])
def generate_constellation():
    """Generate a constellation from a name and location"""
    data = request.json
    
    name = data.get('name', 'JISHNU').upper()
    lat = float(data.get('latitude', 13.0))  # Default: Bangalore area
    lon = float(data.get('longitude', 77.7))
    date = data.get('date', '2026-03-15')
    time = data.get('time', '20:00')
    
    # Get visible stars
    stars = star_gen.get_visible_stars(lat, lon, date, time)
    
    # Create constellation from name
    constellation_stars, connections = star_gen.create_constellation_from_text(
        stars, name, width=800, height=600
    )
    
    # Prepare response
    response = {
        'name': name,
        'location': {
            'lat': lat,
            'lon': lon
        },
        'datetime': f"{date} {time}",
        'total_visible_stars': len(stars),
        'constellation_stars': constellation_stars,
        'connections': connections,
        'star_count': len(constellation_stars)
    }
    
    return jsonify(response)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'stars_loaded': len(star_gen.stars_df)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)