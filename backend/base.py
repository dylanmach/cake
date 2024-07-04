from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

MAX_VALUATION = 10
epsilon = 0.0025 / MAX_VALUATION

@app.route('/api/three_agent', methods=['POST'])
def three_agent():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    # result = branzei_nisan(preferences, cake_size)
    # result_as_dict = [result.left, result.right]
    # return jsonify({'result': result_as_dict})
    return branzei_nisan(preferences, cake_size)

@app.route('/api/four_agent', methods=['POST'])
def four_agent():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    #result = hollender_rubinstein(preferences, cake_size)
    #result_as_dict = [result.left, result.middle, result.right]
    #return jsonify({'result': result_as_dict})
    # division, assignment = hollender_rubinstein(preferences, cake_size)
    # return jsonify({'division': division,
    #                 'assignment': assignment})
    return hollender_rubinstein(preferences, cake_size)

#Preprocessing Below

def normalization(prefs):
    '''
    Ensures that each agents values the
    '''
    #Need to change.
    for agents in prefs:
        for segments in agents:
            segments['startValue'] /= MAX_VALUATION
            segments['endValue'] /= MAX_VALUATION
    return prefs#, normalizationConstants
        

def change_bounds(prefs, cakeSize):
    for agents in prefs:
        for segments in agents:
            app.logger.debug("hello")
            app.logger.debug(type(segments))
            app.logger.debug(segments)
            segments['start'] /= cakeSize
            segments['end'] /= cakeSize
    return prefs


def one_lipschitz(prefs, cakeSize):
    #Remember to scale by L at end.
    prefs = change_bounds(prefs, cakeSize)
    #prefs, normalizationConstants = normalization(prefs)
    prefs = normalization(prefs)
    return prefs#, normalizationConstants
#Preprocessing above

#ValueQuery Stuff below

def interpolate(segment, x_coordinate):
    '''
    Uses the linear interpolation formula to find the associated y-coordinate for a 
    given x-coordinate on a line between two points with known x and y coordinates.
    '''
    if segment['startValue'] == segment['endValue']:
        y_coordinate = segment['startValue']
        return y_coordinate
    if segment['startValue'] != segment['endValue']:
        y_coordinate = ((segment['startValue'] * (segment['end'] - x_coordinate) +
                         segment['endValue'] * (x_coordinate - segment['start'])) / 
                        (segment['end'] - segment['start']))                
        return y_coordinate
    


def find_partial_value(segment, partial_segment_end):
    segment_width = partial_segment_end - segment['start']
    partial_segment_end_value = interpolate(segment, partial_segment_end)
    if segment['startValue'] == segment['endValue']:
        value = segment['startValue'] * segment_width
        return value
    if segment['startValue'] != segment['endValue']:
        value = 0.5 * (segment['startValue'] + partial_segment_end_value) * \
                segment_width
        return value
    

def find_full_value(segment):
    segment_width = segment['end'] - segment['start']
    if segment['startValue'] == segment['endValue']:
        value = segment['startValue'] * segment_width
        return value
    if segment['startValue'] != segment['endValue']:
        value = 0.5 * (segment['startValue'] + segment['endValue']) * segment_width
        return value
    

def one_sided_query(agent, prefs, end):
    segments = np.size(prefs[agent])
    value = 0
    for i in range(segments):
        if end > prefs[agent][i]['end']:
            value += find_full_value(prefs[agent][i])
        if end <= prefs[agent][i]['end']:
            value += find_partial_value(prefs[agent][i], end)
            return value
        

def check_valid_bounds(start,end):
    assert (start >= 0 and start <= 1 and end >= 0 and end <= 1), \
        "invalid bounds. start and end should be between 0 and 1."
    

def value_query_initial(agent, prefs, start, end):
    if end <= start:
        value = 0
    else:
        value = one_sided_query(agent, prefs, end) - \
                one_sided_query(agent, prefs, start)
    return value
    

def value_query_hungry(agent, prefs, start, end, epsilon):
    initial_value = value_query_initial(agent, prefs, start, end)
    value = initial_value / 2 + epsilon * (end - start)
    return value


def intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                     end_bounds, epsilon):
    query_one = value_query_hungry(agent, prefs, start_bounds.lower, 
                                end_bounds.lower, epsilon)
    query_two = value_query_hungry(agent, prefs, start_bounds.lower, 
                                end_bounds.upper, epsilon)
    query_three = value_query_hungry(agent, prefs, start_bounds.upper, 
                                  end_bounds.lower, epsilon)
    return query_one, query_two, query_three


def intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                     end_bounds, epsilon):
    query_one = value_query_hungry(agent, prefs, start_bounds.upper, 
                                   end_bounds.upper, epsilon)
    query_two = value_query_hungry(agent, prefs, start_bounds.lower, 
                                   end_bounds.upper, epsilon)
    query_three = value_query_hungry(agent, prefs, start_bounds.upper, 
                                     end_bounds.lower, epsilon)
    return query_one, query_two, query_three


def piecewise_linear_bounds(start, end, epsilon):
    if start != 1:
        start_lower_bound = (start // epsilon) * epsilon
        start_upper_bound = start_lower_bound + epsilon 
    else:
        start_lower_bound = 1 - epsilon
        start_upper_bound = 1
    if end != 1:
        end_lower_bound = (end // epsilon) * epsilon
        end_upper_bound = end_lower_bound + epsilon
    else:
        end_lower_bound = 1 - epsilon
        end_upper_bound = 1

    start_bounds = Bounds(start_lower_bound, start_upper_bound)
    end_bounds = Bounds(end_lower_bound, end_upper_bound)

    return start_bounds, end_bounds


def value_query_variant_one(agent, prefs, start, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                            end_bounds, epsilon)
    component_one = (((start_bounds.upper - start) - (end - end_bounds.lower)) / 
                    epsilon) * queries[0]
    component_two = ((end - end_bounds.lower) / epsilon) * queries[1]
    component_three = ((start - start_bounds.lower) / epsilon) * queries[2]
    return component_one + component_two + component_three


def value_query_variant_two(agent, prefs, start, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                               end_bounds, epsilon)
    component_one = (((end - end_bounds.lower) - (start_bounds.upper - start)) / 
                    epsilon) * queries[0]
    component_two = ((start_bounds.upper - start) / epsilon) * queries[1]
    component_three = ((end_bounds.upper - end) / epsilon) * queries[2]
    return component_one + component_two + component_three


def value_query(agent, prefs, start, end, epsilon):
    '''
    Linear interpolation on epsilon grid.
    '''
    check_valid_bounds(start,end)
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    
    if start_bounds.upper - start >= end - end_bounds.lower:
        return value_query_variant_one(agent, prefs, start, end, epsilon)
    if start_bounds.upper - start < end - end_bounds.lower:
        return value_query_variant_two(agent, prefs, start, end, epsilon)
    
#Value Query stuff above

#Cut Query Stuff Below
    
def start_cut_query(agent, prefs, end, value, epsilon):
    start_cut_bounds = Bounds(0, end)
    while abs(start_cut_bounds.upper - start_cut_bounds.lower) > 1e-15:
        start_cut_bounds = start_cut_bounds_update(prefs, end, start_cut_bounds, 
                                                   value, epsilon)
    start_cut = start_cut_bounds.midpoint()
    return start_cut


def start_cut_bounds_update(prefs, end, start_cut_bounds, 
                            value, epsilon):
    start_cut = start_cut_bounds.midpoint()
    queried_value = value_query(0, prefs, start_cut, end, epsilon)
    if queried_value <= value:
        start_cut_bounds.upper  = start_cut
    if queried_value > value:
        start_cut_bounds.lower = start_cut
    return start_cut_bounds


def end_cut_query(agent, prefs, start, value, epsilon):
    end_cut_bounds = Bounds(start, 1)
    while abs(end_cut_bounds.upper - end_cut_bounds.lower) > 1e-15:
        end_cut_bounds = end_cut_bounds_update(prefs, start, end_cut_bounds, 
                                               value, epsilon)
    end_cut = end_cut_bounds.midpoint()
    return end_cut


def end_cut_bounds_update(prefs, start, end_cut_bounds, 
                          value, epsilon):
    end_cut = end_cut_bounds.midpoint()
    queried_value = value_query(0, prefs, start, end_cut, epsilon)
    if queried_value <= value:
        end_cut_bounds.lower  = end_cut
    if queried_value > value:
        end_cut_bounds.upper = end_cut
    return end_cut_bounds


def cut_query(agent, prefs, initial_cut, value, epsilon, end_cut = True):
    #Must add functionality that returns if there is no cut.
    if end_cut == True:
        queried_cut = end_cut_query(agent, prefs, initial_cut, value, epsilon)
    else:
        queried_cut = start_cut_query(agent, prefs, initial_cut, value, epsilon)
    return queried_cut


def bisection_cut_query(agent, prefs, start, end, epsilon):
    bisection_cut_bounds = Bounds(start, end)
    while abs(bisection_cut_bounds.upper - bisection_cut_bounds.lower) > 1e-15:
        bisection_cut_bounds = \
            bisection_cut_bounds_update(agent, prefs, start, end,
                                        bisection_cut_bounds, epsilon)
    bisection_cut = bisection_cut_bounds.midpoint()
    return bisection_cut


def bisection_cut_bounds_update(agent, prefs, start, end, 
                                bisection_cut_bounds, epsilon):
    bisection_cut = bisection_cut_bounds.midpoint()
    left_segment_value = value_query(agent, prefs, start, bisection_cut, epsilon)
    right_segment_value = value_query(agent, prefs, bisection_cut, end, epsilon)
    bisection_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                        bisection_cut_bounds) 
    return bisection_cut_bounds

#Cut Query Stuff above


#Equipartition Stuff Below

def bounds_shift(left_slice_value, right_slice_value, cut_bounds):
    cut = cut_bounds.midpoint()
    if left_slice_value >= right_slice_value:
        cut_bounds.upper = cut
    if left_slice_value < right_slice_value:
        cut_bounds.lower = cut
    return cut_bounds


def equipartition_cut(prefs, cut_bounds, agent_numbers,
                      epsilon, cut_bounds_update):
    while abs(cut_bounds.upper - cut_bounds.lower) > 1e-15:
        cut_bounds = cut_bounds_update(prefs, cut_bounds, agent_numbers, epsilon)
    return cut_bounds.midpoint()


def exact_equipartition_cuts(prefs, left_cut_bounds, middle_cut_bounds, 
                             right_cut_bounds, agents_number, epsilon):
    left_cut = equipartition_cut(prefs, left_cut_bounds, agents_number, epsilon,
                                 left_cut_bounds_update)
    right_cut= equipartition_cut(prefs, right_cut_bounds, agents_number, epsilon,
                                 right_cut_bounds_update)
    if agents_number == 3:
        equipartition = ThreeAgentPortion(left_cut, right_cut)
    if agents_number == 4:
        middle_cut= equipartition_cut(prefs, middle_cut_bounds, agents_number, 
                                      epsilon, middle_cut_bounds_update)
        equipartition = FourAgentPortion(left_cut, middle_cut, right_cut)
    alpha = value_query(0, prefs, 0, left_cut, epsilon)
    return equipartition, alpha


def find_epsilon_interval(bounds, epsilon):
    value_within_interval = bounds.midpoint()
    lower_bound_of_interval = (value_within_interval // epsilon) * epsilon
    upper_bound_of_interval = lower_bound_of_interval + epsilon 
    epsilon_interval = Bounds(lower_bound_of_interval, upper_bound_of_interval)
    return epsilon_interval


def left_cut_bounds_right_segment_value_three_agent(prefs, left_cut, 
                                                    left_segment_value,
                                                    epsilon):
    right_cut = cut_query(0, prefs, left_cut, left_segment_value, 
                        epsilon, end_cut = True)
    right_segment_value = value_query(0, prefs, right_cut, 1, epsilon)
    return right_segment_value


def left_cut_bounds_right_segment_value_four_agent(prefs, left_cut, 
                                                   left_segment_value,
                                                   epsilon):
    middle_cut = cut_query(0, prefs, left_cut, left_segment_value, 
                               epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, middle_cut, left_segment_value, 
                              epsilon, end_cut = True)
    right_segment_value = value_query(0, prefs, right_cut, 1, epsilon)
    return right_segment_value


def left_cut_bounds_update(prefs, left_cut_bounds, agents_number, epsilon):
    left_cut = left_cut_bounds.midpoint()
    left_segment_value = value_query(0, prefs, 0, left_cut, epsilon)
    if agents_number == 3:
        right_segment_value = \
            left_cut_bounds_right_segment_value_three_agent(prefs, left_cut, 
                                                            left_segment_value,
                                                            epsilon)
    if agents_number == 4:
        right_segment_value = \
            left_cut_bounds_right_segment_value_four_agent(prefs, left_cut, 
                                                           left_segment_value,
                                                           epsilon)
    left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                   left_cut_bounds)
    return left_cut_bounds


def middle_cut_bounds_update(prefs, middle_cut_bounds, agents_number, epsilon):
    middle_cut = middle_cut_bounds.midpoint()
    left_cut = bisection_cut_query(0, prefs, 0, middle_cut, epsilon)
    right_cut = bisection_cut_query(0, prefs, middle_cut, 1, epsilon)
    left_segment_value = value_query(0, prefs, 0, left_cut, epsilon)
    right_segment_value = value_query(0, prefs, right_cut, 1, epsilon)
    middle_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                     middle_cut_bounds)
    return middle_cut_bounds


def right_cut_bounds_left_segment_value_three_agent(prefs, right_cut, 
                                                    right_segment_value,
                                                    epsilon):
    left_cut = cut_query(0, prefs, right_cut, right_segment_value, 
                        epsilon, end_cut = False)
    left_segment_value = value_query(0, prefs, 0, left_cut, epsilon)
    return left_segment_value


def right_cut_bounds_left_segment_value_four_agent(prefs, right_cut, 
                                                   right_segment_value,
                                                   epsilon):
    middle_cut = cut_query(0, prefs, right_cut, right_segment_value, 
                        epsilon, end_cut = False)
    left_cut = cut_query(0, prefs, middle_cut, right_segment_value, 
                        epsilon, end_cut = False)
    left_segment_value = value_query(0, prefs, 0, left_cut, epsilon)
    return left_segment_value


def right_cut_bounds_update(prefs, right_cut_bounds, agents_number, epsilon):
    right_cut = right_cut_bounds.midpoint()
    right_segment_value = value_query(0, prefs, right_cut, 1, epsilon)
    if agents_number == 3:
        left_segment_value = \
            right_cut_bounds_left_segment_value_three_agent(prefs, right_cut, 
                                                            right_segment_value,
                                                            epsilon)
    if agents_number == 4:
        left_segment_value = \
            right_cut_bounds_left_segment_value_four_agent(prefs, right_cut, 
                                                            right_segment_value,
                                                            epsilon)
    right_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                    right_cut_bounds)
    return right_cut_bounds


def find_cut_epsilon_interval(prefs, agents_number, epsilon, cut_bounds_update):
    #make agents_number optional.
    cut_bounds = Bounds(0, 1)
    while (cut_bounds.upper // epsilon) != (cut_bounds.lower // epsilon):
        cut_bounds = cut_bounds_update(prefs, cut_bounds, agents_number, epsilon)
    cut_epsilon_interval = find_epsilon_interval(cut_bounds, epsilon)
    return cut_epsilon_interval


def compute_equipartition(prefs, agents_number, epsilon):
    left_cut_bounds = find_cut_epsilon_interval(prefs, agents_number, epsilon,
                                                left_cut_bounds_update)
    if agents_number == 3:
        middle_cut_bounds = None
    if agents_number == 4:
        middle_cut_bounds = \
            find_cut_epsilon_interval(prefs, agents_number, epsilon,
                                      middle_cut_bounds_update)
    right_cut_bounds = find_cut_epsilon_interval(prefs, agents_number, epsilon,
                                                 right_cut_bounds_update)
    
    equipartition = \
        exact_equipartition_cuts(prefs, left_cut_bounds, middle_cut_bounds,
                                 right_cut_bounds, agents_number, epsilon)
    return equipartition

#Equipartition stuff above

def check_valid_agents_value(agents_number):
    assert agents_number == 3 or agents_number == 4, \
        "invalid number of agents. Please input either 3 or 4."
    
#slice value stuff below. Could be improved."
def find_middle_slice_values(agent, prefs, division, agents_number, epsilon):
    if agents_number == 3:
        middle_slice_values = np.array([value_query(agent, prefs, division.left, 
                                                    division.right, epsilon)])
    if agents_number == 4:
        slice_two_value = value_query(agent, prefs, division.left, 
                                      division.middle, epsilon)
        slice_three_value = value_query(agent, prefs, division.middle, 
                                      division.right, epsilon)
        middle_slice_values = np.array([slice_two_value, slice_three_value])
    return middle_slice_values


def slice_values(agent, prefs, division, agents_number, epsilon):
    check_valid_agents_value(agents_number)
    left_slice_value = np.array([value_query(agent, prefs, 0, division.left, 
                                             epsilon)])
    middle_slice_values = find_middle_slice_values(agent, prefs, division, 
                                                   agents_number, epsilon)
    right_slice_value = np.array([value_query(agent, prefs, division.right, 1, 
                                              epsilon)])
    return np.concatenate([left_slice_value, middle_slice_values, 
                           right_slice_value])

#slice value stuff above

#3 agent invariant checks below. need to add isclose
def invariant_three_agent_check(slice, prefs, division, epsilon):
    agent_one_slice_values = slice_values(1, prefs, division, 3, epsilon)
    agent_two_slice_values = slice_values(2, prefs, division, 3, epsilon)
    
    if  ((agent_one_slice_values[slice-1] == np.max(agent_one_slice_values)) and \
        (agent_two_slice_values[slice-1] == np.max(agent_two_slice_values))):
        return True
    else:
        return False
    

def invariant_three_agents_slice_one_preferred(prefs, alpha, epsilon):
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    left_cut = cut_query(0, prefs, right_cut, alpha, 
                         epsilon, end_cut = False)
    division = ThreeAgentPortion(left_cut,right_cut)
    return invariant_three_agent_check(1, prefs, division, epsilon)
    

def invariant_three_agents_slice_two_preferred(prefs, alpha, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    division = ThreeAgentPortion(left_cut,right_cut)
    return invariant_three_agent_check(2, prefs, division, epsilon)


def invariant_three_agents_slice_three_preferred(prefs, alpha, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    right_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
    division = ThreeAgentPortion(left_cut,right_cut)
    return invariant_three_agent_check(3, prefs, division, epsilon)


def check_invariant_three_agents(prefs, alpha, epsilon):
    if invariant_three_agents_slice_one_preferred(prefs, alpha, epsilon) == True:
        return True, 1
    if invariant_three_agents_slice_two_preferred(prefs, alpha, epsilon) == True:
        return True, 2
    if invariant_three_agents_slice_three_preferred(prefs, alpha, epsilon) == True:
        return True, 3
    else:
        return False, 0


def division_three_agents(prefs, alpha, epsilon):
    #Can be refactored out.
    if check_invariant_three_agents(prefs, alpha, epsilon)[1] == 1:
        right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
        left_cut = cut_query(0, prefs, right_cut, alpha, 
                             epsilon, end_cut = False)
    if check_invariant_three_agents(prefs, alpha, epsilon)[1] == 2:
        left_cut = cut_query(0, prefs, 0, alpha, epsilon)
        right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
        
    if check_invariant_three_agents(prefs, alpha, epsilon)[1] == 3:
        left_cut = cut_query(0, prefs, 0, alpha, epsilon)
        right_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
    division = ThreeAgentPortion(left_cut,right_cut)
    return division
    
#3 agent invariant checks above

# envy freeness checks below.

def check_unique_preferences_three_agent(agent_one_slice_values,
                                         agent_two_slice_values):
    for i in range(3):
        for j in range(3):
            if j == i:
                continue
            if  ((agent_one_slice_values[i] == np.max(agent_one_slice_values)) and \
                 (agent_two_slice_values[j] == np.max(agent_two_slice_values))):
                return True
    return False


def check_equipartition_envy_free_three_agents(prefs, alpha, 
                                               agents_number, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    right_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
    division = ThreeAgentPortion(left_cut,right_cut)
    agent_one_slice_values = slice_values(1, prefs, division, agents_number,
                                          epsilon)
    agent_two_slice_values = slice_values(2, prefs, division, agents_number,
                                          epsilon)
    is_envy_free = check_unique_preferences_three_agent(agent_one_slice_values,
                                                        agent_two_slice_values)
    return is_envy_free


def check_unique_preferences_four_agent(agent_one_slice_values,
                                        agent_two_slice_values,
                                        agent_three_slice_values):
    for i in range(4):
        for j in range(4):
            for k in range(4):
                if (k == j) or (k == i) or (j == i):
                    continue
                if  (agent_one_slice_values[i] == np.max(agent_one_slice_values)) and \
                    (agent_two_slice_values[j] == np.max(agent_two_slice_values)) and \
                    (agent_three_slice_values[k] == np.max(agent_three_slice_values)):
                    return True
    return False


def check_equipartition_envy_free_four_agents(prefs, alpha, agents_number, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon)
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    agent_one_slice_values = slice_values(1, prefs, division, agents_number, epsilon)
    agent_two_slice_values = slice_values(2, prefs, division, agents_number, epsilon)
    agent_three_slice_values = slice_values(3, prefs, division, agents_number, epsilon)
    is_envy_free = check_unique_preferences_four_agent(agent_one_slice_values,
                                                       agent_two_slice_values,
                                                       agent_three_slice_values)
    return is_envy_free

#envy freeness checks above.

#condition A checks below.

def check_valid_division(division):
    if ((division.right >= division.middle) and (division.middle >= division.left)):
        return True
    else:
        return False


def condition_a_check(slice, prefs, alpha, division, epsilon):
    agents_number = 4
    slices_number = 4
    agent_slice_values = np.zeros((agents_number,slices_number))
    for k in range(agents_number):
        agent_slice_values[k] = slice_values(k, prefs, division, 4, epsilon)
    for i in range(1, agents_number):
        for j in range(1, agents_number):
            if j == i:
                continue
            if (np.isclose(agent_slice_values[i][slice-1], 
                           np.max(agent_slice_values[i]), rtol = 0, atol = epsilon / 12) and \
                np.isclose(agent_slice_values[j][slice-1], 
                           np.max(agent_slice_values[j]), rtol = 0, atol = epsilon / 12) and \
                (agent_slice_values[0][slice-1] <= alpha)):
                return True
    return False
            

def condition_a_slice_one_preferred(prefs, alpha, epsilon, return_division = False):
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(1, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        return division
    else:
        return check_value
    

def condition_a_slice_two_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(2, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        return division
    else:
        return check_value
    

def condition_a_slice_three_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(3, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        return division
    else:
        return check_value
    

def condition_a_slice_four_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(4, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        return division
    else:
        return check_value
    

def check_condition_a(prefs, alpha, epsilon, return_division = False):
    if condition_a_slice_one_preferred(prefs, alpha, epsilon) == True:
        return condition_a_slice_one_preferred(prefs, alpha, epsilon, return_division)
    if condition_a_slice_two_preferred(prefs, alpha, epsilon) == True:
        return condition_a_slice_two_preferred(prefs, alpha, epsilon, return_division)
    if condition_a_slice_three_preferred(prefs, alpha, epsilon) == True:
        return condition_a_slice_three_preferred(prefs, alpha, epsilon, return_division)
    if condition_a_slice_four_preferred(prefs, alpha, epsilon) == True:
        return condition_a_slice_four_preferred(prefs, alpha, epsilon, return_division)
    else:
        return False
    
#condition A checks above.

#condition B checks below.

def condition_b_check(slices, prefs, alpha, division, epsilon):
    #remove doubles
    agents_number = 4
    slices_number = 4
    agent_slice_values = np.zeros((agents_number,slices_number))
    slice_check = np.zeros(2)
    for k in range(agents_number):
        agent_slice_values[k] = slice_values(k, prefs, division, 4, epsilon)
    for s in range(2):
        for i in range(1, agents_number):
            for j in range(1, agents_number):
                if j == i:
                    continue
                if (np.isclose(agent_slice_values[i][slices[s]-1], 
                               np.max(agent_slice_values[i]), rtol = 0, atol = epsilon / 12) and \
                    (np.isclose(agent_slice_values[j][slices[s]-1], 
                                np.max(agent_slice_values[j]), rtol = 0, atol = epsilon / 12) and \
                    (agent_slice_values[0][slices[s]-1] <= alpha))):
                    slice_check[s] = True
    if (slice_check[0] == True and slice_check[1] == True):
        return True
    else: 
        return False
    

def condition_b_slice_one_two_preferred(prefs, alpha, epsilon, return_division = False):
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    for i in range(1,4):
        left_cut = bisection_cut_query(i, prefs, 0, middle_cut, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,2], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_two_three_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    for i in range(1,4):
        middle_cut = bisection_cut_query(i, prefs, left_cut, right_cut, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([2,3], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_three_four_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    for i in range(1,4):
        right_cut = bisection_cut_query(i, prefs, middle_cut, 1, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([3,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_adjacent_slices_preferred(prefs, alpha, epsilon, return_division = False):
    if condition_b_slice_one_two_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_one_two_preferred(prefs, alpha, epsilon, return_division)
    if condition_b_slice_two_three_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_two_three_preferred(prefs, alpha, epsilon, return_division)
    if condition_b_slice_three_four_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_three_four_preferred(prefs, alpha, epsilon, return_division)
    else:
        return False


def leftmost_cut_bounds_one_apart_update(agent, prefs, leftmost_cut_bounds, 
                                         alpha, left_bound, right_bound,
                                         epsilon):
    leftmost_cut = leftmost_cut_bounds.midpoint()
    left_segment_value = value_query(agent, prefs, left_bound, leftmost_cut,
                                     epsilon)
    rightmost_cut = cut_query(0, prefs, leftmost_cut, alpha, epsilon, 
                              end_cut = True)
    right_segment_value = value_query(agent, prefs, rightmost_cut, right_bound,
                                      epsilon)
    leftmost_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                       leftmost_cut_bounds)
    return leftmost_cut_bounds


def rightmost_cut_bounds_one_apart_update(agent, prefs, rightmost_cut_bounds, 
                                          alpha, left_bound, right_bound, 
                                          epsilon):
    rightmost_cut = rightmost_cut_bounds.midpoint()
    right_segment_value = value_query(agent, prefs, rightmost_cut, 
                                      right_bound, epsilon)
    leftmost_cut = cut_query(0, prefs, rightmost_cut, alpha, epsilon, 
                             end_cut = False)
    left_segment_value = value_query(agent, prefs, left_bound, 
                                     leftmost_cut, epsilon)
    rightmost_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                        rightmost_cut_bounds)
    return rightmost_cut_bounds


def non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, left_bound, 
                                right_bound, epsilon, cut_bounds_update):
    cut_bounds = Bounds(left_bound, right_bound)
    while (cut_bounds.upper // epsilon) != (cut_bounds.lower // epsilon):
        cut_bounds = \
            cut_bounds_update(indifferent_agent, prefs, 
                              cut_bounds, alpha, left_bound,
                              right_bound, epsilon)
    cut_epsilon_interval = find_epsilon_interval(cut_bounds, epsilon)
    while abs(cut_bounds.upper - cut_bounds.lower) > 1e-15:
        cut_bounds = cut_bounds_update(indifferent_agent, prefs, 
                                       cut_bounds, alpha, left_bound,
                                       right_bound, epsilon)
    return cut_bounds.midpoint()


def one_apart_slice_cuts(indifferent_agent, prefs, alpha, left_bound, 
                         right_bound, epsilon):
    leftmost_unknown_cut = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
                                       alpha, left_bound, right_bound, epsilon,
                                       leftmost_cut_bounds_one_apart_update)
    rightmost_unknown_cut = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
                                       alpha, left_bound, right_bound, epsilon,
                                       rightmost_cut_bounds_one_apart_update)
    return leftmost_unknown_cut, rightmost_unknown_cut


def condition_b_slice_one_three_preferred(prefs, alpha, epsilon, return_division = False):
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    for i in range(1,4):
        left_cut, middle_cut = \
            one_apart_slice_cuts(i, prefs, alpha, 0, right_cut, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,3], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_two_four_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    for i in range(1,4):
        middle_cut, right_cut = \
            one_apart_slice_cuts(i, prefs, alpha, left_cut, 1, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([2,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_one_apart_slices_preferred(prefs, alpha, epsilon, return_division = False):
    if condition_b_slice_one_three_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_one_three_preferred(prefs, alpha, epsilon, return_division)
    if condition_b_slice_two_four_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_two_four_preferred(prefs, alpha, epsilon, return_division)
    else:
        return False
    

def left_cut_bounds_two_apart_update(agent, prefs, 
                                     left_cut_bounds, alpha, left_bound,
                                     right_bound, epsilon):
    left_cut = left_cut_bounds.midpoint()
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
    left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                   left_cut_bounds)
    return left_cut_bounds 


def middle_cut_bounds_two_apart_update(agent, prefs, 
                                       middle_cut_bounds, alpha, left_bound,
                                       right_bound, epsilon):
    middle_cut = middle_cut_bounds.midpoint()
    left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
    left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    middle_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                     middle_cut_bounds)
    return middle_cut_bounds


def right_cut_bounds_two_apart_update(agent, prefs, 
                                      right_cut_bounds, alpha, left_bound,
                                      right_bound, epsilon):
    right_cut = right_cut_bounds.midpoint()
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
    left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    right_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                    right_cut_bounds)
    return right_cut_bounds


def two_apart_slice_cuts(indifferent_agent, prefs, alpha, left_bound, 
                         right_bound, epsilon):
    left_cut = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, left_cut_bounds_two_apart_update)
    middle_cut = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, middle_cut_bounds_two_apart_update)
    
    right_cut = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, right_cut_bounds_two_apart_update)
    return left_cut, middle_cut, right_cut


def condition_b_slice_one_four_preferred(prefs, alpha, epsilon, return_division = False):
    for i in range(1,4):
        left_cut, middle_cut, right_cut = \
            two_apart_slice_cuts(i, prefs, alpha, 0, 1, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            return division
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_two_apart_slices_preferred(prefs, alpha, epsilon, return_division = False):
    if condition_b_slice_one_four_preferred(prefs, alpha, epsilon) == True:
        return condition_b_slice_one_four_preferred(prefs, alpha, epsilon, return_division)
    else:
        return False
    

def check_condition_b(prefs, alpha, epsilon, return_division = False):
    if condition_b_adjacent_slices_preferred(prefs, alpha, epsilon) == True:
        return condition_b_adjacent_slices_preferred(prefs, alpha, epsilon, return_division)
    if condition_b_one_apart_slices_preferred(prefs, alpha, epsilon) == True:
        return condition_b_one_apart_slices_preferred(prefs, alpha, epsilon, return_division)
    if condition_b_two_apart_slices_preferred(prefs, alpha, epsilon) == True:
        return condition_b_two_apart_slices_preferred(prefs, alpha, epsilon, return_division)
    else:
        return False
    
#condition B stuff above

def check_invariant_four_agents(prefs, alpha, epsilon, return_division = False):
    if check_condition_a(prefs, alpha, epsilon) == True:
        #print("a")
        return check_condition_a(prefs, alpha, epsilon, return_division)
    elif check_condition_b(prefs, alpha, epsilon) == True:
        #print("b")
        return check_condition_b(prefs, alpha, epsilon, return_division)
    else:
        return False
    
def assign_slices(division, prefs, agents_number, epsilon):
    if agents_number == 3:
        agents = [0,1,2]
        slices = [1,2,3]
    if  agents_number == 4:
        agents = [0,1,2,3]
        slices = [1,2,3,4]
    agent_slice_values = np.zeros((len(agents),len(slices)))
    for i in range(agents_number):
        agent_slice_values[i] = slice_values(i, prefs, division, agents_number, epsilon)
    assignments = {}  # To store the assignments of slices to agents

    while len(agents) > 1:
        max_difference = -1
        chosen_agent = None
        chosen_slice = None

        # Find the agent with the maximum difference between their top two best slices
        for agent in agents:
            # Sort the agent's valuations and get the indices of the top two values
            valuations = pd.DataFrame({"slices": slices,
                                       "values": agent_slice_values[agent]})
            sorted_valuations = valuations.sort_values(by ='values' , ascending=False).reset_index(drop=True)
            top_value = sorted_valuations["values"][0]
            second_value = sorted_valuations["values"][1]
            difference = top_value - second_value
            value_for_print = sorted_valuations["slices"][0]

            if difference > max_difference:
                max_difference = difference
                chosen_agent = agent
                chosen_slice = sorted_valuations["slices"][0]

        # Assign the chosen slice to the chosen agent
        assignments[int(chosen_slice)] = chosen_agent

        # Remove the chosen agent and slice
        agents.remove(chosen_agent)
        slice_index = slices.index(chosen_slice)
        slices.remove(chosen_slice)
        agent_slice_values = [np.concatenate([val[:slice_index], val[slice_index+1:]]) for val in agent_slice_values]

    # Assign the remaining slice to the remaining agent
    assignments[int(slices[0])] = agents[0]

    return assignments

def raw_division(division, cakeSize, agents_number):
    left_cut = float(division.left * cakeSize)
    right_cut = float(division.right * cakeSize)
    if agents_number == 3:
        return {"left": left_cut, "right": right_cut}
    if agents_number == 4:
        middle_cut = float(division.middle * cakeSize)
        return {"left": left_cut, "middle": middle_cut,
                "right": right_cut}
    

def branzei_nisan(raw_prefs, cakeSize):
    prefs = one_lipschitz(raw_prefs, cakeSize)
    equipartition, alpha_lower_bound = compute_equipartition(prefs, 3, epsilon)
    if check_equipartition_envy_free_three_agents(prefs, alpha_lower_bound, 3,
                                                  epsilon) == True:
        slice_assignments = assign_slices(equipartition, prefs, 3, epsilon)
        raw_envy_free_division = raw_division(equipartition, cakeSize, 3)
        return jsonify({'division': raw_envy_free_division,
                        'assignment': slice_assignments})
    alpha_upper_bound = 1
    alpha_bounds = Bounds(alpha_lower_bound, alpha_upper_bound)
    while abs(alpha_bounds.upper - alpha_bounds.lower) > ((epsilon)**4)/12:
        alpha = alpha_bounds.midpoint()
        if check_invariant_three_agents(prefs, alpha, epsilon)[0] == True:
            alpha_bounds.lower = alpha
        else:
            alpha_bounds.upper = alpha
    envy_free_division = division_three_agents(prefs, alpha_bounds.lower, epsilon)
    slice_assignments = assign_slices(envy_free_division, prefs, 3, epsilon)
    raw_envy_free_division = raw_division(envy_free_division, cakeSize, 3)
    return jsonify({'division': raw_envy_free_division,
                    'assignment': slice_assignments})


def hollender_rubinstein(raw_prefs, cakeSize):
    prefs = one_lipschitz(raw_prefs, cakeSize)
    equipartition, alpha_lower_bound = compute_equipartition(prefs, 4, epsilon)
    if check_equipartition_envy_free_four_agents(prefs, alpha_lower_bound, 4,
                                                 epsilon) == True:
        slice_assignments = assign_slices(equipartition, prefs, 4, epsilon)
        raw_envy_free_division = raw_division(equipartition, cakeSize, 4)
        return jsonify({'division': raw_envy_free_division,
                        'assignment': slice_assignments})
    alpha_upper_bound = 1
    alpha_bounds = Bounds(alpha_lower_bound, alpha_upper_bound)
    while abs(alpha_bounds.upper - alpha_bounds.lower) > ((epsilon)**4)/12:
        alpha = alpha_bounds.midpoint()
        if check_invariant_four_agents(prefs, alpha, epsilon) == True:
            alpha_bounds.lower = alpha
        else:
            alpha_bounds.upper = alpha
    envy_free_division = check_invariant_four_agents(prefs, alpha_bounds.lower, epsilon,
                                                     return_division = True)
    slice_assignments = assign_slices(envy_free_division, prefs, 4, epsilon)
    raw_envy_free_division = raw_division(envy_free_division, cakeSize, 4)
    return jsonify({'division': raw_envy_free_division,
                    'assignment': slice_assignments})
    #return raw_envy_free_division, slice_assignments


class Bounds:
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def midpoint(self):
        return (self.lower + self.upper) / 2


class ThreeAgentPortion:
    def __init__(self, left_cut, right_cut):
        self.left = left_cut
        self.right = right_cut


class FourAgentPortion:
    def __init__(self, left_cut, middle_cut, right_cut):
        self.left = left_cut
        self.middle = middle_cut
        self.right = right_cut

        
if __name__ == '__main__':
    app.run(debug=True, port=5000)
