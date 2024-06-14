from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/api/run_algorithm', methods=['POST'])
def run_algorithm():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    result = barbanel_brams(preferences, cake_size)
    
    return jsonify({'result': result})

def barbanel_brams(preferences, cake_size):
    # Placeholder algorithm logic, replace with actual implementation
    return cake_size * len(preferences)

if __name__ == '__main__':
    app.run(debug=True)