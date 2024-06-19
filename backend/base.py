from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np

epsilon = 0.0025

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/api/run_algorithm', methods=['POST'])
def run_algorithm():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    result = branzei_nisan(preferences, cake_size)
    
    return jsonify({'result': result})

def branzei_nisan(prefs, cakeSize, epsilon):
    #preferences = one_lipschitz(prefs, cakeSize)
    equipartition, alpha_lower_bound = compute_equipartition_three_agents(prefs, epsilon)
    if check_equipartition_envy_free(prefs, alpha_lower_bound, epsilon) == True:
        return equipartition
    alpha_upper_bound = 1
    alpha_bounds = Bounds(alpha_lower_bound, alpha_upper_bound)
    while abs(alpha_bounds.upper - alpha_bounds.lower) > ((epsilon/10)**4)/12:
        alpha = alpha_bounds.midpoint()
        if check_invariant_three_agents(prefs, alpha, epsilon)[0] == True:
            alpha_bounds.lower = alpha
        else:
            alpha_bounds.upper = alpha
    return division_three_agents(prefs, alpha_bounds.lower, epsilon)


if __name__ == '__main__':
    app.run(debug=True)