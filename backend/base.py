from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import pandas as pd
from timeit import default_timer as timer
import itertools
from scipy.optimize import minimize
from scipy.optimize import linear_sum_assignment

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

MAX_VALUATION = 10
epsilon = 0.0025 / MAX_VALUATION

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
    


def find_partial_value_right_side(segment, partial_segment_end):
    segment_width = partial_segment_end - segment['start']
    partial_segment_start_value = segment['startValue']
    partial_segment_end_value = interpolate(segment, partial_segment_end)
    return area_under_curve(segment, partial_segment_start_value,
                            partial_segment_end_value, segment_width)
    
def find_partial_value_left_side(segment, partial_segment_start):
    segment_width = segment['end'] - partial_segment_start
    partial_segment_start_value = interpolate(segment, partial_segment_start)
    partial_segment_end_value = segment['endValue']
    return area_under_curve(segment, partial_segment_start_value,
                            partial_segment_end_value, segment_width)
    
def find_partial_value_two_sided(segment, partial_segment_start, partial_segment_end):
    segment_width = partial_segment_end - partial_segment_start
    partial_segment_start_value = interpolate(segment, partial_segment_start)
    partial_segment_end_value = interpolate(segment, partial_segment_end)
    return area_under_curve(segment, partial_segment_start_value,
                            partial_segment_end_value, segment_width)
    
def area_under_curve(segment, start_value, end_value, width):
    if segment['startValue'] == segment['endValue']:
        value = start_value * width
        return value
    if segment['startValue'] != segment['endValue']:
        value = 0.5 * (start_value + end_value) * width
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
            value += find_partial_value_right_side(prefs[agent][i], end)
            return value
        

def check_valid_bounds(start,end):
    assert (start >= 0 and start <= 1 and end >= 0 and end <= 1), \
        "invalid bounds. start and end should be between 0 and 1."
    

# def value_query_initial(agent, prefs, start, end):
#     if end <= start:
#         value = 0
#     else:
#         value = one_sided_query(agent, prefs, end) - \
#                 one_sided_query(agent, prefs, start)
#     return value

def value_query_initial(agent, prefs, start, end):
    if end <= start:
        value = 0
        return value
    else:
        segments = np.size(prefs[agent])
        value = 0
        for i in range(segments):
            if start >= prefs[agent][i]['end']:
                continue
            if start >= prefs[agent][i]['start'] and end <= prefs[agent][i]['end']:
                value = find_partial_value_two_sided(prefs[agent][i], start, end)
                return value
            if start >= prefs[agent][i]['start'] and end > prefs[agent][i]['end']:
                value += find_partial_value_left_side(prefs[agent][i], start)
                continue
            if start < prefs[agent][i]['start'] and end > prefs[agent][i]['end']:
                value += find_full_value(prefs[agent][i])
            if start < prefs[agent][i]['start'] and end <= prefs[agent][i]['end']:
                value += find_partial_value_right_side(prefs[agent][i], end)
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


def value_query_variant_one(agent, prefs, start, end, queries, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                                   end_bounds, epsilon)
    component_one = (((start_bounds.upper - start) - (end - end_bounds.lower)) / 
                    epsilon) * queries[0]
    component_two = ((end - end_bounds.lower) / epsilon) * queries[1]
    component_three = ((start - start_bounds.lower) / epsilon) * queries[2]
    return component_one + component_two + component_three


def value_query_variant_two(agent, prefs, start, end, queries, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                                   end_bounds, epsilon)
    component_one = (((end - end_bounds.lower) - (start_bounds.upper - start)) / 
                    epsilon) * queries[0]
    component_two = ((start_bounds.upper - start) / epsilon) * queries[1]
    component_three = ((end_bounds.upper - end) / epsilon) * queries[2]
    return component_one + component_two + component_three


def value_query(agent, prefs, start, end, epsilon, queries = [None, None]):
    '''
    Linear interpolation on epsilon grid.
    '''
    check_valid_bounds(start,end)
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    
    if start_bounds.upper - start >= end - end_bounds.lower:
        return value_query_variant_one(agent, prefs, start, end, queries[0], epsilon)
    if start_bounds.upper - start < end - end_bounds.lower:
        return value_query_variant_two(agent, prefs, start, end, queries[1], epsilon)
    
#Value Query stuff above

#Cut Query Stuff Below
    
# def start_cut_query(agent, prefs, end, value, epsilon):
#     start_cut_bounds = Bounds(0, end)
#     #TODO
#     while abs(start_cut_bounds.upper - start_cut_bounds.lower) > 1e-15:
#         start_cut_bounds = start_cut_bounds_update(agent, prefs, end, start_cut_bounds, 
#                                                    value, epsilon)
#     start_cut = start_cut_bounds.midpoint()
#     return start_cut

# def start_cut_query(agent, prefs, end, value, epsilon):
#     start_cut_bounds = Bounds(0, end)
#     while (start_cut_bounds.upper // epsilon) != (start_cut_bounds.lower // epsilon):
#         start_cut_bounds = start_cut_bounds_update(agent, prefs, end, start_cut_bounds, 
#                                                    value, epsilon)
#     start = start_cut_bounds.midpoint()
#     start_cut = find_start_cut(agent, prefs, start, end, value, epsilon)
#     return start_cut

# def find_start_cut(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     start_cut = find_start_cut_variant_one(agent, prefs, start, end, value, epsilon)
#     if (start_cut is not None) and (start_bounds.upper - start_cut >= end - end_bounds.lower):
#         assert abs(value_query(agent, prefs, start_cut, end, epsilon) - value) < 1e-10
#         return start_cut
#     start_cut = find_start_cut_variant_two(agent, prefs, start, end, value, epsilon)
#     if (start_cut is not None) and (start_bounds.upper - start_cut <= end - end_bounds.lower):
#         assert abs(value_query(agent, prefs, start_cut, end, epsilon) - value) < 1e-10
#         return start_cut
#     else:
#         return None
        
# def find_start_cut_variant_one(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
#                                                end_bounds, epsilon)
#     component_one = -((end - end_bounds.lower) / 
#                       epsilon) * queries[0]
#     component_two = ((end - end_bounds.lower) / epsilon) * queries[1]
#     component_three = (start_bounds.upper / epsilon) * queries[0]
#     component_four = - (start_bounds.lower / epsilon) * queries[2]
#     denominator = (queries[2] - queries[0]) / epsilon
#     start_cut = (value - component_one - component_two - 
#                  component_three - component_four) / denominator
#     if (start_cut >= start_bounds.lower) and (start_cut <= start_bounds.upper):
#         return start_cut
#     else:
#         return None
    
# def find_start_cut_variant_two(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
#                                                end_bounds, epsilon)
#     component_one = ((end - end_bounds.lower) / 
#                     epsilon) * queries[0]
#     component_two = ((end_bounds.upper - end) / epsilon) * queries[2]
#     component_three = -((queries[0] - queries[1]) / epsilon) * start_bounds.upper
#     denominator = (queries[0] - queries[1]) / epsilon
#     start_cut = (value - component_one - component_two - 
#                  component_three) / denominator
#     if (start_cut >= start_bounds.lower) and (start_cut <= start_bounds.upper):
#         return start_cut
#     else:
#         return None

def start_cut_query(agent, prefs, end, value, epsilon, bounds, queries):
    if bounds is None:
        start_cut_bounds = Bounds(0, end)
        while (start_cut_bounds.upper // epsilon) != (start_cut_bounds.lower // epsilon):
            start_cut_bounds = start_cut_bounds_update(agent, prefs, end, start_cut_bounds, 
                                                    value, epsilon)
    else:
        start_cut_bounds = bounds
    start = start_cut_bounds.midpoint()
    start_cut = find_start_cut(agent, prefs, start, end, value, epsilon, queries)
    return start_cut

def find_start_cut(agent, prefs, start, end, value, epsilon, queries):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is not None:
        start_cut = find_start_cut_variant_one(agent, prefs, start, end, value, epsilon, queries[0])
    else:
        start_cut = find_start_cut_variant_one(agent, prefs, start, end, value, epsilon)
    if (start_cut is not None) and (start_bounds.upper - start_cut >= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start_cut, end, epsilon) - value) < 1e-10
        return start_cut
    if queries is not None:
        start_cut = find_start_cut_variant_two(agent, prefs, start, end, value, epsilon, queries[1])
    else:
        start_cut = find_start_cut_variant_two(agent, prefs, start, end, value, epsilon)
    if (start_cut is not None) and (start_bounds.upper - start_cut <= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start_cut, end, epsilon) - value) < 1e-10
        return start_cut
    else:
        return None
        
def find_start_cut_variant_one(agent, prefs, start, end, value, epsilon, queries = None):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                                   end_bounds, epsilon)
    component_one = -((end - end_bounds.lower) / 
                      epsilon) * queries[0]
    component_two = ((end - end_bounds.lower) / epsilon) * queries[1]
    component_three = (start_bounds.upper / epsilon) * queries[0]
    component_four = - (start_bounds.lower / epsilon) * queries[2]
    denominator = (queries[2] - queries[0]) / epsilon
    start_cut = (value - component_one - component_two - 
                 component_three - component_four) / denominator
    if (start_cut >= start_bounds.lower) and (start_cut <= start_bounds.upper):
        return start_cut
    else:
        return None
    
def find_start_cut_variant_two(agent, prefs, start, end, value, epsilon, queries = None):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                                   end_bounds, epsilon)
    component_one = ((end - end_bounds.lower) / 
                    epsilon) * queries[0]
    component_two = ((end_bounds.upper - end) / epsilon) * queries[2]
    component_three = -((queries[0] - queries[1]) / epsilon) * start_bounds.upper
    denominator = (queries[0] - queries[1]) / epsilon
    start_cut = (value - component_one - component_two - 
                 component_three) / denominator
    if (start_cut >= start_bounds.lower) and (start_cut <= start_bounds.upper):
        return start_cut
    else:
        return None


def start_cut_bounds_update(agent, prefs, end, start_cut_bounds, 
                            value, epsilon):
    start_cut = start_cut_bounds.midpoint()
    queried_value = value_query(agent, prefs, start_cut, end, epsilon)
    if queried_value <= value:
        start_cut_bounds.upper  = start_cut
    if queried_value > value:
        start_cut_bounds.lower = start_cut
    return start_cut_bounds


# def end_cut_query(agent, prefs, start, value, epsilon):
#     end_cut_bounds = Bounds(start, 1)
#     #TODO
#     while abs(end_cut_bounds.upper - end_cut_bounds.lower) > 1e-15:
#         end_cut_bounds = end_cut_bounds_update(agent, prefs, start, end_cut_bounds, 
#                                                value, epsilon)
#     end_cut = end_cut_bounds.midpoint()
#     return end_cut

# def end_cut_query(agent, prefs, start, value, epsilon):
#     end_cut_bounds = Bounds(start, 1)
#     while (end_cut_bounds.upper // epsilon) != (end_cut_bounds.lower // epsilon):
#         end_cut_bounds = end_cut_bounds_update(agent, prefs, start, end_cut_bounds, 
#                                                value, epsilon)
#     end = end_cut_bounds.midpoint()
#     end_cut = find_end_cut(agent, prefs, start, end, value, epsilon)
#     return end_cut

# def find_end_cut(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     end_cut = find_end_cut_variant_one(agent, prefs, start, end, value, epsilon)
#     if (end_cut is not None) and (start_bounds.upper - start >= end_cut - end_bounds.lower):
#         assert abs(value_query(agent, prefs, start, end_cut, epsilon) - value) < 1e-10
#         return end_cut
#     end_cut = find_end_cut_variant_two(agent, prefs, start, end, value, epsilon)
#     if (end_cut is not None) and (start_bounds.upper - start <= end_cut - end_bounds.lower):
#         assert abs(value_query(agent, prefs, start, end_cut, epsilon) - value) < 1e-10
#         return end_cut
#     else:
#         return None
        
# def find_end_cut_variant_one(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
#                                                end_bounds, epsilon)
#     component_one = ((start_bounds.upper - start) / epsilon) * queries[0]
#     component_two = ((start - start_bounds.lower) / epsilon) * queries[2]
#     component_three = -((queries[1] - queries[0]) / epsilon) * end_bounds.lower
#     denominator = (queries[1] - queries[0]) / epsilon
#     end_cut = (value - component_one - component_two - component_three) / denominator
#     if (end_cut >= end_bounds.lower) and (end_cut <= end_bounds.upper):
#         return end_cut
#     else:
#         return None
    
# def find_end_cut_variant_two(agent, prefs, start, end, value, epsilon):
#     start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
#     queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
#                                                end_bounds, epsilon)
#     component_one = -((start_bounds.upper - start) / 
#                     epsilon) * queries[0]
#     component_two = ((start_bounds.upper - start) / epsilon) * queries[1]
#     component_three = -((end_bounds.lower) / epsilon) * queries[0]
#     component_four = ((end_bounds.upper) / epsilon) * queries[2]
#     denominator = (queries[0] - queries[2]) / epsilon
#     end_cut = (value - component_one - component_two - 
#                component_three - component_four) / denominator
#     if (end_cut >= end_bounds.lower) and (end_cut <= end_bounds.upper):
#         return end_cut
#     else:
#         return None

def end_cut_query(agent, prefs, start, value, epsilon, bounds, queries):
    if bounds is None:
        end_cut_bounds = Bounds(start, 1)
        while (end_cut_bounds.upper // epsilon) != (end_cut_bounds.lower // epsilon):
            end_cut_bounds = end_cut_bounds_update(agent, prefs, start, end_cut_bounds, 
                                                value, epsilon)
    else:
        end_cut_bounds = bounds
    end = end_cut_bounds.midpoint()
    end_cut = find_end_cut(agent, prefs, start, end, value, epsilon, queries)
    return end_cut

def find_end_cut(agent, prefs, start, end, value, epsilon, queries):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is not None:
        end_cut = find_end_cut_variant_one(agent, prefs, start, end, value, epsilon, queries[0])
    else:
        end_cut = find_end_cut_variant_one(agent, prefs, start, end, value, epsilon)
    if (end_cut is not None) and (start_bounds.upper - start >= end_cut - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, end_cut, epsilon) - value) < 1e-10
        return end_cut
    if queries is not None:
        end_cut = find_end_cut_variant_two(agent, prefs, start, end, value, epsilon, queries[1])
    else:
        end_cut = find_end_cut_variant_two(agent, prefs, start, end, value, epsilon)
    if (end_cut is not None) and (start_bounds.upper - start <= end_cut - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, end_cut, epsilon) - value) < 1e-10
        return end_cut
    else:
        return None
        
def find_end_cut_variant_one(agent, prefs, start, end, value, epsilon, queries = None):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                                end_bounds, epsilon)
    component_one = ((start_bounds.upper - start) / epsilon) * queries[0]
    component_two = ((start - start_bounds.lower) / epsilon) * queries[2]
    component_three = -((queries[1] - queries[0]) / epsilon) * end_bounds.lower
    denominator = (queries[1] - queries[0]) / epsilon
    end_cut = (value - component_one - component_two - component_three) / denominator
    if (end_cut >= end_bounds.lower) and (end_cut <= end_bounds.upper):
        return end_cut
    else:
        return None
    
def find_end_cut_variant_two(agent, prefs, start, end, value, epsilon, queries = None):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    if queries is None:
        queries = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                                end_bounds, epsilon)
    component_one = -((start_bounds.upper - start) / 
                    epsilon) * queries[0]
    component_two = ((start_bounds.upper - start) / epsilon) * queries[1]
    component_three = -((end_bounds.lower) / epsilon) * queries[0]
    component_four = ((end_bounds.upper) / epsilon) * queries[2]
    denominator = (queries[0] - queries[2]) / epsilon
    end_cut = (value - component_one - component_two - 
               component_three - component_four) / denominator
    if (end_cut >= end_bounds.lower) and (end_cut <= end_bounds.upper):
        return end_cut
    else:
        return None


def end_cut_bounds_update(agent, prefs, start, end_cut_bounds, 
                          value, epsilon):
    end_cut = end_cut_bounds.midpoint()
    queried_value = value_query(agent, prefs, start, end_cut, epsilon)
    if queried_value <= value:
        end_cut_bounds.lower  = end_cut
    if queried_value > value:
        end_cut_bounds.upper = end_cut
    return end_cut_bounds

def cut_query(agent, prefs, initial_cut, value, epsilon, end_cut = True, 
              bounds = None, queries = None):
    #Must add functionality that returns if there is no cut.
    if end_cut == True:
        queried_cut = end_cut_query(agent, prefs, initial_cut, value, epsilon, bounds, queries)
    else:
        queried_cut = start_cut_query(agent, prefs, initial_cut, value, epsilon, bounds, queries)
    return queried_cut


# def bisection_cut_query(agent, prefs, start, end, epsilon):
#     bisection_cut_bounds = Bounds(start, end)
#     #TODO
#     while abs(bisection_cut_bounds.upper - bisection_cut_bounds.lower) > 1e-15:
#         bisection_cut_bounds = \
#             bisection_cut_bounds_update(agent, prefs, start, end,
#                                         bisection_cut_bounds, epsilon)
#     bisection_cut = bisection_cut_bounds.midpoint()
#     return bisection_cut

def bisection_cut_query(agent, prefs, start, end, epsilon):
    if start == end:
        return start
    bisection_cut_bounds = Bounds(start, end)
    #TODO
    while (bisection_cut_bounds.upper // epsilon) != (bisection_cut_bounds.lower // epsilon):
        bisection_cut_bounds = \
            bisection_cut_bounds_update(agent, prefs, start, end,
                                        bisection_cut_bounds, epsilon)
    bisection_cut = find_bisection_cut(agent, prefs, start, bisection_cut_bounds, end, epsilon)
    return bisection_cut

def bisection_cut_bounds_update(agent, prefs, start, end, 
                                bisection_cut_bounds, epsilon):
    bisection_cut = bisection_cut_bounds.midpoint()
    left_segment_value = value_query(agent, prefs, start, bisection_cut, epsilon)
    right_segment_value = value_query(agent, prefs, bisection_cut, end, epsilon)
    bisection_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                        bisection_cut_bounds) 
    return bisection_cut_bounds

def find_bisection_cut(agent, prefs, start, bisection_cut_bounds, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    bisection_bounds = find_epsilon_interval(bisection_cut_bounds, epsilon)
    bisection_cut = find_bisection_cut_variant_one_one(agent, prefs, start, bisection_bounds, end, epsilon)
    if (bisection_cut is not None) and (start_bounds.upper - start >= bisection_cut - bisection_bounds.lower) and \
        (bisection_bounds.upper - bisection_cut >= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, bisection_cut, epsilon) - 
                   value_query(agent, prefs, bisection_cut, end, epsilon)) < 1e-10
        return bisection_cut
    bisection_cut = find_bisection_cut_variant_one_two(agent, prefs, start, bisection_bounds, end, epsilon)
    if (bisection_cut is not None) and (start_bounds.upper - start >= bisection_cut - bisection_bounds.lower) and \
        (bisection_bounds.upper - bisection_cut <= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, bisection_cut, epsilon) - 
                   value_query(agent, prefs, bisection_cut, end, epsilon)) < 1e-10
        return bisection_cut
    bisection_cut = find_bisection_cut_variant_two_one(agent, prefs, start, bisection_bounds, end, epsilon)
    if (bisection_cut is not None) and (start_bounds.upper - start <= bisection_cut - bisection_bounds.lower) and \
        (bisection_bounds.upper - bisection_cut >= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, bisection_cut, epsilon) - 
                   value_query(agent, prefs, bisection_cut, end, epsilon)) < 1e-10
        return bisection_cut
    bisection_cut = find_bisection_cut_variant_two_two(agent, prefs, start, bisection_bounds, end, epsilon)
    if (bisection_cut is not None) and (start_bounds.upper - start <= bisection_cut - bisection_bounds.lower) and \
        (bisection_bounds.upper - bisection_cut <= end - end_bounds.lower):
        assert abs(value_query(agent, prefs, start, bisection_cut, epsilon) - 
                   value_query(agent, prefs, bisection_cut, end, epsilon)) < 1e-10
        return bisection_cut
    else:
        return None
    
def find_bisection_cut_variant_one_one(agent, prefs, start, bisection_bounds, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries_left = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                                    bisection_bounds, epsilon)
    queries_right = intermediate_queries_variant_one(agent, prefs, bisection_bounds, 
                                                     end_bounds, epsilon)
    
    component_one_left = ((start_bounds.upper - start) / 
                          epsilon) * queries_left[0]
    component_two_left = ((start - start_bounds.lower) / epsilon) * queries_left[2]
    component_three_left = ((queries_left[0] - queries_left[1]) / epsilon) * bisection_bounds.lower 

    component_one_right = -((end - end_bounds.lower) / 
                            epsilon) * queries_right[0]
    component_two_right = ((end - end_bounds.lower) / epsilon) * queries_right[1]
    component_three_right = (bisection_bounds.upper / epsilon) * queries_right[0]
    component_four_right = -(bisection_bounds.lower / epsilon) * queries_right[2]

    left_hand_side = (component_one_left + component_two_left + component_three_left)
    right_hand_side = (component_one_right + component_two_right + 
                       component_three_right + component_four_right)
    numerator = left_hand_side - right_hand_side

    left_multiple = (queries_left[1] - queries_left[0]) / epsilon
    right_multiple = (queries_right[2] - queries_right[0]) / epsilon
    denominator = right_multiple - left_multiple

    bisection_cut = numerator / denominator
    if (bisection_cut >= bisection_bounds.lower) and (bisection_cut <= bisection_bounds.upper):
        return bisection_cut
    else:
        return None
    
def find_bisection_cut_variant_one_two(agent, prefs, start, bisection_bounds, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries_left = intermediate_queries_variant_one(agent, prefs, start_bounds, 
                                                    bisection_bounds, epsilon)
    queries_right = intermediate_queries_variant_two(agent, prefs, bisection_bounds, 
                                                     end_bounds, epsilon)
    
    component_one_left = ((start_bounds.upper - start) / 
                          epsilon) * queries_left[0]
    component_two_left = ((start - start_bounds.lower) / epsilon) * queries_left[2]
    component_three_left = ((queries_left[0] - queries_left[1]) / epsilon) * bisection_bounds.lower 

    component_one_right = ((end - end_bounds.lower) / 
                           epsilon) * queries_right[0]
    component_two_right = ((end_bounds.upper - end) / epsilon) * queries_right[2]
    component_three_right = ((queries_right[1] - queries_right[0]) / epsilon) * bisection_bounds.upper

    left_hand_side = (component_one_left + component_two_left + component_three_left)
    right_hand_side = (component_one_right + component_two_right + component_three_right)
    numerator = left_hand_side - right_hand_side

    left_multiple = (queries_left[1] - queries_left[0]) / epsilon
    right_multiple = (queries_right[0] - queries_right[1]) / epsilon
    denominator = right_multiple - left_multiple

    bisection_cut = numerator / denominator
    if (bisection_cut >= bisection_bounds.lower) and (bisection_cut <= bisection_bounds.upper):
        return bisection_cut
    else:
        return None

def find_bisection_cut_variant_two_one(agent, prefs, start, bisection_bounds, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries_left = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                                    bisection_bounds, epsilon)
    queries_right = intermediate_queries_variant_one(agent, prefs, bisection_bounds, 
                                                     end_bounds, epsilon)
    
    component_one_left = -((start_bounds.upper - start) / 
                           epsilon) * queries_left[0]
    component_two_left = ((start_bounds.upper - start) / epsilon) * queries_left[1]
    component_three_left = -(bisection_bounds.lower / epsilon) * queries_left[0]
    component_four_left = (bisection_bounds.upper / epsilon) * queries_left[2] 

    component_one_right = -((end - end_bounds.lower) / 
                            epsilon) * queries_right[0]
    component_two_right = ((end - end_bounds.lower) / epsilon) * queries_right[1]
    component_three_right = (bisection_bounds.upper / epsilon) * queries_right[0]
    component_four_right = -(bisection_bounds.lower / epsilon) * queries_right[2]

    left_hand_side = (component_one_left + component_two_left + 
                      component_three_left + component_four_left)
    right_hand_side = (component_one_right + component_two_right + 
                       component_three_right + component_four_right)
    numerator = left_hand_side - right_hand_side

    left_multiple = (queries_left[0] - queries_left[2]) / epsilon
    right_multiple = (queries_right[2] - queries_right[0]) / epsilon
    denominator = right_multiple - left_multiple

    bisection_cut = numerator / denominator
    if (bisection_cut >= bisection_bounds.lower) and (bisection_cut <= bisection_bounds.upper):
        return bisection_cut
    else:
        return None
    
def find_bisection_cut_variant_two_two(agent, prefs, start, bisection_bounds, end, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start, end, epsilon)
    queries_left = intermediate_queries_variant_two(agent, prefs, start_bounds, 
                                                    bisection_bounds, epsilon)
    queries_right = intermediate_queries_variant_two(agent, prefs, bisection_bounds, 
                                                     end_bounds, epsilon)
    
    component_one_left = -((start_bounds.upper - start) / 
                           epsilon) * queries_left[0]
    component_two_left = ((start_bounds.upper - start) / epsilon) * queries_left[1]
    component_three_left = -(bisection_bounds.lower / epsilon) * queries_left[0]
    component_four_left = (bisection_bounds.upper / epsilon) * queries_left[2] 

    component_one_right = ((end - end_bounds.lower) / 
                           epsilon) * queries_right[0]
    component_two_right = ((end_bounds.upper - end) / epsilon) * queries_right[2]
    component_three_right = ((queries_right[1] - queries_right[0]) / epsilon) * bisection_bounds.upper

    left_hand_side = (component_one_left + component_two_left + 
                      component_three_left + component_four_left)
    right_hand_side = (component_one_right + component_two_right + component_three_right)
    numerator = left_hand_side - right_hand_side

    left_multiple = (queries_left[0] - queries_left[2]) / epsilon
    right_multiple = (queries_right[0] - queries_right[1]) / epsilon
    denominator = right_multiple - left_multiple

    bisection_cut = numerator / denominator
    if (bisection_cut >= bisection_bounds.lower) and (bisection_cut <= bisection_bounds.upper):
        return bisection_cut
    else:
        return None

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
    #TODO
    while abs(cut_bounds.upper - cut_bounds.lower) > 1e-15:
        cut_bounds = cut_bounds_update(prefs, cut_bounds, agent_numbers, epsilon)
    return cut_bounds.midpoint()


def exact_equipartition_cuts(prefs, left_cut_bounds, middle_cut_bounds, 
                             right_cut_bounds, agents_number, epsilon):
    #start = timer()
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
    #end = timer()
    #print(end - start)
    return equipartition, alpha


def equipartition_queries_four_agents(prefs, left_cut_bounds, middle_cut_bounds, 
                                      right_cut_bounds, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(0, 1, epsilon)
    first_slice_queries_one = intermediate_queries_variant_one(0, prefs, start_bounds, 
                                                               left_cut_bounds, epsilon)
    first_slice_queries_two = intermediate_queries_variant_two(0, prefs, start_bounds, 
                                                               left_cut_bounds, epsilon)
    second_slice_queries_one = intermediate_queries_variant_one(0, prefs, left_cut_bounds, 
                                                                middle_cut_bounds, epsilon)
    second_slice_queries_two = intermediate_queries_variant_two(0, prefs, left_cut_bounds, 
                                                                middle_cut_bounds, epsilon)
    third_slice_queries_one = intermediate_queries_variant_one(0, prefs, middle_cut_bounds, 
                                                                right_cut_bounds, epsilon)
    third_slice_queries_two = intermediate_queries_variant_two(0, prefs, middle_cut_bounds, 
                                                                right_cut_bounds, epsilon)
    fourth_slice_queries_one = intermediate_queries_variant_one(0, prefs, right_cut_bounds, 
                                                                end_bounds, epsilon)
    fourth_slice_queries_two = intermediate_queries_variant_two(0, prefs, right_cut_bounds, 
                                                                end_bounds, epsilon)
    
    queries = [
        [
            first_slice_queries_one, first_slice_queries_two
        ],
        [
            second_slice_queries_one, second_slice_queries_two
        ],
        [
            third_slice_queries_one, third_slice_queries_two
        ],
        [
            fourth_slice_queries_one, fourth_slice_queries_two
        ]
    ]
    return queries


def exact_equipartition_cuts_four_agents(prefs, left_cut_bounds, middle_cut_bounds, 
                                         right_cut_bounds, epsilon):
    #start = timer()
    left_cut = left_cut_bounds.midpoint()
    queries = equipartition_queries_four_agents(prefs, left_cut_bounds, middle_cut_bounds, 
                                                right_cut_bounds, epsilon)
    while abs(left_cut_bounds.upper - left_cut_bounds.lower) > 1e-15:
        left_cut = left_cut_bounds.midpoint()
        left_segment_value = value_query(0, prefs, 0, left_cut, 
                                         epsilon, queries[0])
        
        middle_cut = cut_query(0, prefs, left_cut, left_segment_value, 
                               epsilon, True,
                               middle_cut_bounds, queries[1])
        if middle_cut is None:
            #By intermediate value theorem, the cut bounds must be all
            #containcuts that return slices less than or all contain cuts that
            #return slices greater than the desired value.
            middle_cut = middle_cut_bounds.midpoint()
            right_segment_value = value_query(0, prefs, left_cut, middle_cut, 
                                              epsilon, queries[1])
            left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                           left_cut_bounds)
            continue
                
        right_cut = cut_query(0, prefs, middle_cut, left_segment_value, 
                              epsilon, True,
                              right_cut_bounds, queries[2])
        if right_cut is None:
            right_cut = right_cut_bounds.midpoint()
            right_segment_value = value_query(0, prefs, middle_cut, right_cut, 
                                              epsilon, queries[2])
            left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                           left_cut_bounds)
            continue
        right_segment_value = value_query(0, prefs, right_cut, 1, 
                                          epsilon, queries[3])

        left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                       left_cut_bounds)
    left_cut = left_cut_bounds.midpoint()
    equipartition = FourAgentPortion(left_cut, middle_cut, right_cut)
    alpha = value_query(0, prefs, 0, left_cut, epsilon, queries[0])
    #end = timer()
    #print(end - start)
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
    if right_cut is None:
        return 0
    right_segment_value = value_query(0, prefs, right_cut, 1, epsilon)
    return right_segment_value


def left_cut_bounds_right_segment_value_four_agent(prefs, left_cut, 
                                                   left_segment_value,
                                                   epsilon):
    middle_cut = cut_query(0, prefs, left_cut, left_segment_value, 
                               epsilon, end_cut = True)
    if middle_cut is None:
        return 0
    right_cut = cut_query(0, prefs, middle_cut, left_segment_value, 
                              epsilon, end_cut = True)
    if right_cut is None:
        return 0
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
    if left_cut is None:
        return 0
    left_segment_value = value_query(0, prefs, 0, left_cut, epsilon)
    return left_segment_value


def right_cut_bounds_left_segment_value_four_agent(prefs, right_cut, 
                                                   right_segment_value,
                                                   epsilon):
    middle_cut = cut_query(0, prefs, right_cut, right_segment_value, 
                        epsilon, end_cut = False)
    if middle_cut is None:
        return 0
    left_cut = cut_query(0, prefs, middle_cut, right_segment_value, 
                        epsilon, end_cut = False)
    if left_cut is None:
        return 0
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
    #start = timer()
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
    
    if agents_number == 3:
        equipartition = \
            exact_equipartition_cuts(prefs, left_cut_bounds, middle_cut_bounds,
                                     right_cut_bounds, 3, epsilon)
        
    if agents_number == 4:
        equipartition = \
            exact_equipartition_cuts_four_agents(prefs, left_cut_bounds, middle_cut_bounds,
                                                 right_cut_bounds, epsilon)
    #end = timer()
    #print(end - start)
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

def check_valid_division_three_agent(division):
    if (division.right >= division.left):
        return True
    else:
        return False
    
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
    if right_cut is None:
        return False
    left_cut = cut_query(0, prefs, right_cut, alpha, 
                         epsilon, end_cut = False)
    if left_cut is None:
        return False
    division = ThreeAgentPortion(left_cut,right_cut)
    if check_valid_division_three_agent(division) == False:
        return False
    else:
        return invariant_three_agent_check(1, prefs, division, epsilon)
    

def invariant_three_agents_slice_two_preferred(prefs, alpha, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    if left_cut is None:
        return False
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    if right_cut is None:
        return False
    division = ThreeAgentPortion(left_cut,right_cut)
    if check_valid_division_three_agent(division) == False:
        return False
    else:
        return invariant_three_agent_check(2, prefs, division, epsilon)


def invariant_three_agents_slice_three_preferred(prefs, alpha, epsilon):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon)
    if left_cut is None:
        return False
    right_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
    if right_cut is None:
        return False
    division = ThreeAgentPortion(left_cut,right_cut)
    if check_valid_division_three_agent(division) == False:
        return False
    else:
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
        slices = 1
    if check_invariant_three_agents(prefs, alpha, epsilon)[1] == 2:
        left_cut = cut_query(0, prefs, 0, alpha, epsilon)
        right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
        slices = 2
    if check_invariant_three_agents(prefs, alpha, epsilon)[1] == 3:
        left_cut = cut_query(0, prefs, 0, alpha, epsilon)
        right_cut = cut_query(0, prefs, left_cut, alpha, epsilon)
        slices = 3
    division = ThreeAgentPortion(left_cut,right_cut)
    return division, slices
    
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
    if right_cut is None:
        return False
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    if middle_cut is None:
        return False
    left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
    if left_cut is None:
        return False
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(1, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        info = pd.DataFrame({'condition': 1,
                             'slices': [1],
                             'indifferent_agent': None})
        return division, info
    else:
        return check_value
    

def condition_a_slice_two_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    if right_cut is None:
        return False
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    if middle_cut is None:
        return False
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(2, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        info = pd.DataFrame({'condition': 1,
                             'slices': [2],
                             'indifferent_agent': None})
        return division, info
    else:
        return check_value
    

def condition_a_slice_three_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    if middle_cut is None:
        return False
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    if right_cut is None:
        return False
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(3, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        info = pd.DataFrame({'condition': 1,
                             'slices': [3],
                             'indifferent_agent': None})
        return division, info
    else:
        return check_value
    

def condition_a_slice_four_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    if middle_cut is None:
        return False
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
    if right_cut is None:
        return False
    division = FourAgentPortion(left_cut, middle_cut, right_cut)
    if check_valid_division(division) == False:
        return False
    check_value = condition_a_check(4, prefs, alpha, division, epsilon)
    if (check_value == True) and (return_division == True):
        info = pd.DataFrame({'condition': 1,
                             'slices': [4],
                             'indifferent_agent': None})
        return division, info
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
    if right_cut is None:
        return False
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    if middle_cut is None:
        return False
    for i in range(1,4):
        left_cut = bisection_cut_query(i, prefs, 0, middle_cut, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,2], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [1,2],
                                 'indifferent_agent': i})
            return division, info
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_two_three_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    if right_cut is None:
        return False
    for i in range(1,4):
        middle_cut = bisection_cut_query(i, prefs, left_cut, right_cut, epsilon)
        if middle_cut is None:
            return False
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([2,3], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [2,3],
                                 'indifferent_agent': i})
            return division, info
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_three_four_preferred(prefs, alpha, epsilon, return_division = False):
    if np.isclose(alpha, 0.08135672927733817, rtol = 0, atol = 1e-15):
        x = 1
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, end_cut = True)
    if middle_cut is None:
        return False
    for i in range(1,4):
        right_cut = bisection_cut_query(i, prefs, middle_cut, 1, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([3,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [3,4],
                                 'indifferent_agent': i})
            return division, info
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
    if rightmost_cut is None:
        right_segment_value = 0
    else:
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
    if leftmost_cut is None:
        left_segment_value = 0
    else:
        left_segment_value = value_query(agent, prefs, left_bound, 
                                        leftmost_cut, epsilon)
    rightmost_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                        rightmost_cut_bounds)
    return rightmost_cut_bounds


# def non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, left_bound, 
#                                 right_bound, epsilon, cut_bounds_update):
#     cut_bounds = Bounds(left_bound, right_bound)
#     while (cut_bounds.upper // epsilon) != (cut_bounds.lower // epsilon):
#         cut_bounds = \
#             cut_bounds_update(indifferent_agent, prefs, 
#                               cut_bounds, alpha, left_bound,
#                               right_bound, epsilon)
#     cut_epsilon_interval = find_epsilon_interval(cut_bounds, epsilon)
#     #TODO
#     while abs(cut_bounds.upper - cut_bounds.lower) > 1e-15:
#         cut_bounds = cut_bounds_update(indifferent_agent, prefs, 
#                                        cut_bounds, alpha, left_bound,
#                                        right_bound, epsilon)
#     return cut_bounds.midpoint()

def non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, left_bound, 
                                right_bound, epsilon, cut_bounds_update):
    cut_bounds = Bounds(left_bound, right_bound)
    while (cut_bounds.upper // epsilon) != (cut_bounds.lower // epsilon):
        cut_bounds = \
            cut_bounds_update(indifferent_agent, prefs, 
                              cut_bounds, alpha, left_bound,
                              right_bound, epsilon)
    cut_epsilon_interval = find_epsilon_interval(cut_bounds, epsilon)
    return cut_epsilon_interval


# def one_apart_slice_cuts(indifferent_agent, prefs, alpha, left_bound, 
#                          right_bound, epsilon):
#     start = timer()
#     leftmost_unknown_cut = \
#         non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
#                                        alpha, left_bound, right_bound, epsilon,
#                                        leftmost_cut_bounds_one_apart_update)
#     rightmost_unknown_cut = \
#         non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
#                                        alpha, left_bound, right_bound, epsilon,
#                                        rightmost_cut_bounds_one_apart_update)
#     end = timer()
#     print(end - start)
#     return leftmost_unknown_cut, rightmost_unknown_cut

def one_apart_queries(indifferent_agent, prefs, start_bound, leftmost_cut_bounds, 
                      rightmost_cut_bounds, end_bound, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(start_bound, end_bound, epsilon)
    first_slice_queries_one = intermediate_queries_variant_one(indifferent_agent, prefs, start_bounds, 
                                                               leftmost_cut_bounds, epsilon)
    first_slice_queries_two = intermediate_queries_variant_two(indifferent_agent, prefs, start_bounds, 
                                                               leftmost_cut_bounds, epsilon)
    second_slice_queries_one = intermediate_queries_variant_one(0, prefs, leftmost_cut_bounds, 
                                                                rightmost_cut_bounds, epsilon)
    second_slice_queries_two = intermediate_queries_variant_two(0, prefs, leftmost_cut_bounds, 
                                                                rightmost_cut_bounds, epsilon)
    third_slice_queries_one = intermediate_queries_variant_one(indifferent_agent, prefs, rightmost_cut_bounds, 
                                                                end_bounds, epsilon)
    third_slice_queries_two = intermediate_queries_variant_two(indifferent_agent, prefs, rightmost_cut_bounds, 
                                                               end_bounds, epsilon)
    queries = [
        [
            first_slice_queries_one, first_slice_queries_two
        ],
        [
            second_slice_queries_one, second_slice_queries_two
        ],
        [
            third_slice_queries_one, third_slice_queries_two
        ]
    ]
    return queries

def one_apart_slice_cuts_exact(indifferent_agent, prefs, alpha, left_bound, right_bound, 
                               leftmost_cut_bounds, rightmost_cut_bounds, epsilon):
    queries = one_apart_queries(indifferent_agent, prefs, left_bound, leftmost_cut_bounds, 
                                rightmost_cut_bounds, right_bound, epsilon)
    leftmost_cut = leftmost_cut_bounds.midpoint()
    while abs(leftmost_cut_bounds.upper - leftmost_cut_bounds.lower) > 1e-15:
        leftmost_cut = leftmost_cut_bounds.midpoint()
        left_segment_value = value_query(indifferent_agent, prefs, left_bound, leftmost_cut,
                                         epsilon, queries[0])
        rightmost_cut = cut_query(0, prefs, leftmost_cut, alpha, epsilon, 
                                  True, rightmost_cut_bounds, queries[1])
        if rightmost_cut is None:
            rightmost_cut = rightmost_cut_bounds.midpoint()
            alpha_check = value_query(0, prefs, leftmost_cut, rightmost_cut, 
                                      epsilon, queries[1])
            leftmost_cut_bounds = bounds_shift(alpha, alpha_check, 
                                               leftmost_cut_bounds)
        else:
            right_segment_value = value_query(indifferent_agent, prefs, rightmost_cut, right_bound,
                                              epsilon, queries[2])
            leftmost_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                            leftmost_cut_bounds)
    return leftmost_cut, rightmost_cut

def one_apart_slice_cuts(indifferent_agent, prefs, alpha, left_bound, 
                          right_bound, epsilon):
    #start = timer()
    leftmost_unknown_cut_bounds = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
                                       alpha, left_bound, right_bound, epsilon,
                                       leftmost_cut_bounds_one_apart_update)
    rightmost_unknown_cut_bounds = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, 
                                       alpha, left_bound, right_bound, epsilon,
                                       rightmost_cut_bounds_one_apart_update)
    leftmost_unknown_cut, rightmost_unknown_cut = \
        one_apart_slice_cuts_exact(indifferent_agent, prefs, 
                                   alpha, left_bound, right_bound, 
                                   leftmost_unknown_cut_bounds,
                                   rightmost_unknown_cut_bounds,  
                                   epsilon)
    #end = timer()
    #print(end - start)
    return leftmost_unknown_cut, rightmost_unknown_cut


def condition_b_slice_one_three_preferred(prefs, alpha, epsilon, return_division = False):
    right_cut = cut_query(0, prefs, 1, alpha, epsilon, end_cut = False)
    if right_cut is None:
        return False
    for i in range(1,4):
        left_cut, middle_cut = \
            one_apart_slice_cuts(i, prefs, alpha, 0, right_cut, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,3], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [1,3],
                                 'indifferent_agent': i})
            return division, info
        if (check_value == True) and (return_division == False):
            return check_value
        else:
            continue
    return False


def condition_b_slice_two_four_preferred(prefs, alpha, epsilon, return_division = False):
    left_cut = cut_query(0, prefs, 0, alpha, epsilon, end_cut = True)
    if left_cut is None:
        return False
    for i in range(1,4):
        middle_cut, right_cut = \
            one_apart_slice_cuts(i, prefs, alpha, left_cut, 1, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([2,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [2,4],
                                 'indifferent_agent': i})
            return division, info
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
    if middle_cut is None:
        right_segment_value = 0
    else:
        right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
        if right_cut is None:
            right_segment_value = 0
        else:
            right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                    left_cut_bounds)
    return left_cut_bounds 


def middle_cut_bounds_two_apart_update(agent, prefs, 
                                       middle_cut_bounds, alpha, left_bound,
                                       right_bound, epsilon):
    middle_cut = middle_cut_bounds.midpoint()
    left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
    if left_cut is None:
        left_segment_value = 0
    else:
        left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = True)
    if right_cut is None:
        right_segment_value = 0
    else:
        right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    middle_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                     middle_cut_bounds)
    return middle_cut_bounds


def right_cut_bounds_two_apart_update(agent, prefs, 
                                      right_cut_bounds, alpha, left_bound,
                                      right_bound, epsilon):
    right_cut = right_cut_bounds.midpoint()
    middle_cut = cut_query(0, prefs, right_cut, alpha, epsilon, end_cut = False)
    if middle_cut is None:
        left_segment_value = 0
    else:
        left_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, end_cut = False)
        if left_cut is None:
            left_segment_value = 0
        else:
            left_segment_value = value_query(agent, prefs, 0, left_cut, epsilon)
    right_segment_value = value_query(agent, prefs, right_cut, 1, epsilon)
    right_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                    right_cut_bounds)
    return right_cut_bounds


# def two_apart_slice_cuts(indifferent_agent, prefs, alpha, left_bound, 
#                          right_bound, epsilon):
#     left_cut = \
#         non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
#                                        epsilon, left_cut_bounds_two_apart_update)
#     middle_cut = \
#         non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
#                                        epsilon, middle_cut_bounds_two_apart_update)
    
#     right_cut = \
#         non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
#                                        epsilon, right_cut_bounds_two_apart_update)
#     return left_cut, middle_cut, right_cut
def two_apart_queries_four_agents(indifferent_agent, prefs, left_cut_bounds,
                                  middle_cut_bounds, right_cut_bounds, epsilon):
    start_bounds, end_bounds = piecewise_linear_bounds(0, 1, epsilon)
    first_slice_queries_one = intermediate_queries_variant_one(indifferent_agent, prefs, start_bounds, 
                                                               left_cut_bounds, epsilon)
    first_slice_queries_two = intermediate_queries_variant_two(indifferent_agent, prefs, start_bounds, 
                                                               left_cut_bounds, epsilon)
    second_slice_queries_one = intermediate_queries_variant_one(0, prefs, left_cut_bounds, 
                                                                middle_cut_bounds, epsilon)
    second_slice_queries_two = intermediate_queries_variant_two(0, prefs, left_cut_bounds, 
                                                                middle_cut_bounds, epsilon)
    third_slice_queries_one = intermediate_queries_variant_one(0, prefs, middle_cut_bounds, 
                                                               right_cut_bounds, epsilon)
    third_slice_queries_two = intermediate_queries_variant_two(0, prefs, middle_cut_bounds, 
                                                               right_cut_bounds, epsilon)
    fourth_slice_queries_one = intermediate_queries_variant_one(indifferent_agent, prefs, right_cut_bounds, 
                                                                end_bounds, epsilon)
    fourth_slice_queries_two = intermediate_queries_variant_two(indifferent_agent, prefs, right_cut_bounds, 
                                                                end_bounds, epsilon)
    
    queries = [
        [
            first_slice_queries_one, first_slice_queries_two
        ],
        [
            second_slice_queries_one, second_slice_queries_two
        ],
        [
            third_slice_queries_one, third_slice_queries_two
        ],
        [
            fourth_slice_queries_one, fourth_slice_queries_two
        ]
    ]
    return queries

def two_apart_slice_cuts_exact(indifferent_agent, prefs, alpha, left_cut_bounds,
                               middle_cut_bounds, right_cut_bounds, epsilon):
    queries = two_apart_queries_four_agents(indifferent_agent, prefs, left_cut_bounds,
                                            middle_cut_bounds, right_cut_bounds, epsilon)
    left_cut = left_cut_bounds.midpoint()
    while abs(left_cut_bounds.upper - left_cut_bounds.lower) > 1e-15:
        left_cut = left_cut_bounds.midpoint()
        left_segment_value = value_query(indifferent_agent, prefs, 0, left_cut,
                                         epsilon, queries[0])
        middle_cut = cut_query(0, prefs, left_cut, alpha, epsilon, True, 
                               middle_cut_bounds, queries[1])
        if middle_cut is None:
            middle_cut = middle_cut_bounds.midpoint()
            right_cut = right_cut_bounds.midpoint()
            alpha_check = value_query(0, prefs, left_cut, middle_cut, 
                                      epsilon, queries[1])
            left_cut_bounds = bounds_shift(alpha, alpha_check, 
                                           left_cut_bounds)
            continue
        right_cut = cut_query(0, prefs, middle_cut, alpha, epsilon, True, 
                               right_cut_bounds, queries[2])
        if right_cut is None:
            right_cut = right_cut_bounds.midpoint()
            alpha_check = value_query(0, prefs, middle_cut, right_cut, 
                                      epsilon, queries[2])
            left_cut_bounds = bounds_shift(alpha, alpha_check, 
                                           left_cut_bounds)
            continue
        right_segment_value = value_query(indifferent_agent, prefs, right_cut, 1, 
                                          epsilon, queries[3])
        left_cut_bounds = bounds_shift(left_segment_value, right_segment_value, 
                                        left_cut_bounds)
    return left_cut, middle_cut, right_cut
    

def two_apart_slice_cuts(indifferent_agent, prefs, alpha, epsilon):
    left_cut_bounds = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, left_cut_bounds_two_apart_update)
    middle_cut_bounds = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, middle_cut_bounds_two_apart_update)
    
    right_cut_bounds = \
        non_adjacent_slice_cuts_update(indifferent_agent, prefs, alpha, 0, 1, 
                                       epsilon, right_cut_bounds_two_apart_update)
    
    left_cut, middle_cut, right_cut =\
        two_apart_slice_cuts_exact(indifferent_agent, prefs, 
                                   alpha, left_cut_bounds,
                                   middle_cut_bounds, right_cut_bounds,
                                   epsilon)
    return left_cut, middle_cut, right_cut


def condition_b_slice_one_four_preferred(prefs, alpha, epsilon, return_division = False):
    for i in range(1,4):
        left_cut, middle_cut, right_cut = \
            two_apart_slice_cuts(i, prefs, alpha, epsilon)
        division = FourAgentPortion(left_cut, middle_cut, right_cut)
        if check_valid_division(division) == False:
            continue
        check_value = condition_b_check([1,4], prefs, alpha, division, epsilon)
        if (check_value == True) and (return_division == True):
            info = pd.DataFrame({'condition': 2,
                                 'slices': [1,4],
                                 'indifferent_agent': i})
            return division, info
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
    
def check_envy_free_four_agent(prefs, division, epsilon):
    agent_slice_values = np.zeros((4,4))
    for i in range(4):
        agent_slice_values[i] = slice_values(i, prefs, division, 4, epsilon)
    for h in range(4):
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    if (k == j) or (k == i) or (j == i) or (h == i) or (h == j) or (h == k):
                        continue
                    if  np.isclose(agent_slice_values[0][h], np.max(agent_slice_values[0]), rtol = 0, atol = epsilon) and \
                        np.isclose(agent_slice_values[1][i], np.max(agent_slice_values[1]), rtol = 0, atol = epsilon) and \
                        np.isclose(agent_slice_values[2][j], np.max(agent_slice_values[2]), rtol = 0, atol = epsilon) and \
                        np.isclose(agent_slice_values[3][k], np.max(agent_slice_values[3]), rtol = 0, atol = epsilon):
                            return True
    return False
    
# def assign_slices(division, prefs, agents_number, epsilon, additive = False):
#     if agents_number == 3:
#         agents = [0,1,2]
#         slices = [1,2,3]
#     if  agents_number == 4:
#         agents = [0,1,2,3]
#         slices = [1,2,3,4]
#     agent_slice_values = np.zeros((len(agents),len(slices)))
#     for i in range(agents_number):
#         if additive == False:
#             agent_slice_values[i] = slice_values(i, prefs, division, agents_number, epsilon)
#         else:
#             agent_slice_values[i] = slice_values_additive(i, prefs, division, epsilon)
#     assignments = {}  # To store the assignments of slices to agents

#     while len(agents) > 1:
#         max_difference = -1
#         chosen_agent = None
#         chosen_slice = None

#         # Find the agent with the maximum difference between their top two best slices
#         for agent in agents:
#             # Sort the agent's valuations and get the indices of the top two values
#             valuations = pd.DataFrame({"slices": slices,
#                                        "values": agent_slice_values[agent]})
#             sorted_valuations = valuations.sort_values(by ='values' , ascending=False).reset_index(drop=True)
#             top_value = sorted_valuations["values"][0]
#             second_value = sorted_valuations["values"][1]
#             difference = top_value - second_value
#             #value_for_print = sorted_valuations["slices"][0]

#             if difference > max_difference:
#                 max_difference = difference
#                 chosen_agent = agent
#                 chosen_slice = sorted_valuations["slices"][0]

#         # Assign the chosen slice to the chosen agent
#         assignments[int(chosen_slice)] = chosen_agent

#         # Remove the chosen agent and slice
#         agents.remove(chosen_agent)
#         slice_index = slices.index(chosen_slice)
#         slices.remove(chosen_slice)
#         agent_slice_values = [np.concatenate([val[:slice_index], val[slice_index+1:]]) for val in agent_slice_values]

#     # Assign the remaining slice to the remaining agent
#     assignments[int(slices[0])] = agents[0]

#     return assignments

def assign_slices(division, prefs, agents_number, epsilon, additive = False):
    '''
    Makes a cost matrix where the cost of an agent being assigned a slice is the difference
    between the slice value and the value of their favourite slice. If a slice's value is more
    than epsilon below the agents favourite slice, the cost is set to 10000 for that agent. 
    This cost matrix is then passed into a cost minimization function that assigns the slices.
    '''
    agent_slice_values = np.zeros((agents_number, agents_number))
    for i in range(agents_number):
        if additive == False:
            agent_slice_values[i] = slice_values(i, prefs, division, agents_number, epsilon)
        else:
            agent_slice_values[i] = slice_values_additive(i, prefs, division, epsilon)

    max_slice_values = np.max(agent_slice_values, axis = 1)
    max_slice_values_matrix = np.tile(max_slice_values, [agents_number,1]).T
    cost_matrix = max_slice_values_matrix - agent_slice_values
    cost_matrix[cost_matrix>epsilon] = 10000
    _, slice_assignments = linear_sum_assignment(cost_matrix)
    assignments = {}  # To store the assignments of slices to agents
    for j in range(1,agents_number+1):
        assignments[j] = int(np.where(slice_assignments==(j-1))[0][0])
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
    

def branzei_nisan(raw_prefs, cake_size):
    #Need to implement specifics in line with four agent algo
    prefs = one_lipschitz(raw_prefs, cake_size)
    equipartition, alpha_lower_bound = compute_equipartition(prefs, 3, epsilon)
    if check_equipartition_envy_free_three_agents(prefs, alpha_lower_bound, 3,
                                                  epsilon) == True:
        slice_assignments = assign_slices(equipartition, prefs, 3, epsilon)
        raw_envy_free_division = raw_division(equipartition, cake_size, 3)
        return jsonify({'division': raw_envy_free_division,
                        'assignment': slice_assignments,
                        'condition': 0})
    alpha_upper_bound = 1
    alpha_bounds = Bounds(alpha_lower_bound, alpha_upper_bound)
    while abs(alpha_bounds.upper - alpha_bounds.lower) > ((epsilon)**4)/12:
        alpha = alpha_bounds.midpoint()
        if check_invariant_three_agents(prefs, alpha, epsilon)[0] == True:
            alpha_bounds.lower = alpha
        else:
            alpha_bounds.upper = alpha
    envy_free_division, slices = division_three_agents(prefs, alpha_bounds.lower, epsilon)
    raw_equipartition = raw_division(equipartition, cake_size, 3)
    slice_assignments = assign_slices(envy_free_division, prefs, 3, epsilon)
    raw_envy_free_division = raw_division(envy_free_division, cake_size, 3)
    return jsonify({'equipartition': raw_equipartition,
                    'division': raw_envy_free_division,
                    'assignment': slice_assignments,
                    'condition': 1,
                    'slices': slices})


def hollender_rubinstein(raw_prefs, cake_size):
    prefs = one_lipschitz(raw_prefs, cake_size)
    equipartition, alpha_lower_bound = compute_equipartition(prefs, 4, epsilon)
    if check_equipartition_envy_free_four_agents(prefs, alpha_lower_bound, 4,
                                                 epsilon) == True:
        slice_assignments = assign_slices(equipartition, prefs, 4, epsilon)
        raw_envy_free_division = raw_division(equipartition, cake_size, 4)
        return jsonify({'equipartition': raw_envy_free_division,
                        'division': 0,
                        'assignment': slice_assignments,
                        'condition': [0],
                        'slices': 0,
                        'indifferent_agent': 0})
    alpha_upper_bound = 1
    alpha_bounds = Bounds(alpha_lower_bound, alpha_upper_bound)
    while abs(alpha_bounds.upper - alpha_bounds.lower) > ((epsilon)**4)/12:
        alpha = alpha_bounds.midpoint()
        if check_invariant_four_agents(prefs, alpha, epsilon) == True:
            alpha_bounds.lower = alpha
        else:
            alpha_bounds.upper = alpha
    x = 1
    envy_free_division, info = check_invariant_four_agents(prefs, alpha_bounds.lower, 
                                                           epsilon, return_division = True)
    app.logger.debug(check_envy_free_four_agent(prefs, envy_free_division, epsilon))
    raw_equipartition = raw_division(equipartition, cake_size, 4)
    slice_assignments = assign_slices(envy_free_division, prefs, 4, epsilon)
    raw_envy_free_division = raw_division(envy_free_division, cake_size, 4)
    return jsonify({'equipartition': raw_equipartition,
                    'division': raw_envy_free_division,
                    'assignment': slice_assignments,
                    'condition': info['condition'].to_list(),
                    'slices': info['slices'].to_list(),
                    'indifferent_agent': info['indifferent_agent'].to_list()})
    #return raw_envy_free_division, slice_assignments

def value_query_hungry_additive(agent, prefs, end, epsilon):
    initial_value = value_query_initial(agent, prefs, 0, end)
    value = (1 - epsilon / 2) * initial_value  + epsilon / 2
    return value

# def value_query_additive(agent, prefs, start, end, epsilon):
#     initial_value = value_query_initial(agent, prefs, start, end)
#     value = (1 - epsilon / 2) * initial_value  + epsilon / 2
#     return value


def value_query_piecewise_additive(agent, prefs, end, epsilon):
    check = end % epsilon
    assert np.isclose(check, 0, rtol = 0, atol= 1e-15) or \
           np.isclose(check, epsilon, rtol = 0, atol= 1e-15),\
           'end cut must be divisible by epsilon'
    initial_value = value_query_hungry_additive(agent, prefs, end, epsilon) 
    if initial_value % epsilon == 0:
        return initial_value
    else:
        final_value = (initial_value // epsilon) * epsilon + epsilon
        return final_value
    
def value_query_interpolated_additive(agent, prefs, end, epsilon):
    check = end % epsilon
    if np.isclose(check, 0, rtol = 0, atol= 1e-15) or \
        np.isclose(check, epsilon, rtol = 0, atol= 1e-15):
        value =  value_query_piecewise_additive(agent, prefs, end, epsilon)
        return value 
    else:
        interpolation_constant = (end % epsilon) / epsilon
        end_left =  (end // epsilon) * epsilon
        end_right = end_left + epsilon
        value_left = value_query_piecewise_additive(agent, prefs, end_left, epsilon)
        value_right = value_query_piecewise_additive(agent, prefs, end_right, epsilon)
        value = value_left + (value_right - value_left) * interpolation_constant
        return value

def value_query_additive(agent, prefs, start, end, epsilon):
    component_one = value_query_interpolated_additive(agent, prefs, start, epsilon)
    component_two = value_query_interpolated_additive(agent, prefs, end, epsilon)
    value = component_two - component_one
    return value


def end_cut_query_additive(agent, prefs, start, value, epsilon):
    end_cut_bounds = Bounds(start, 1)
    while (end_cut_bounds.upper - end_cut_bounds.lower) > epsilon / 200:
        end_cut_bounds = end_cut_bounds_update_additive(agent, prefs, start, end_cut_bounds, 
                                                        value, epsilon)
    end_cut = end_cut_bounds.midpoint()
    return end_cut

def end_cut_bounds_update_additive(agent, prefs, start, end_cut_bounds, 
                                   value, epsilon):
    end_cut = end_cut_bounds.midpoint()
    queried_value = value_query_additive(agent, prefs, start, end_cut, epsilon)
    if queried_value <= value:
        end_cut_bounds.lower  = end_cut
    if queried_value > value:
        end_cut_bounds.upper = end_cut
    return end_cut_bounds

def start_cut_query_additive(agent, prefs, end, value, epsilon):
    start_cut_bounds = Bounds(0, end)
    while (start_cut_bounds.upper - start_cut_bounds.lower) > epsilon / 200:
        start_cut_bounds = start_cut_bounds_update_additive(agent, prefs, end, start_cut_bounds, 
                                                            value, epsilon)
    start_cut = start_cut_bounds.midpoint()
    return start_cut


def start_cut_bounds_update_additive(agent, prefs, end, start_cut_bounds, 
                            value, epsilon):
    start_cut = start_cut_bounds.midpoint()
    queried_value = value_query_additive(agent, prefs, start_cut, end, epsilon)
    if queried_value <= value:
        start_cut_bounds.upper  = start_cut
    if queried_value > value:
        start_cut_bounds.lower = start_cut
    return start_cut_bounds


def cut_query_additive(agent, prefs, initial_cut, value, epsilon, end_cut = True):
    #Must add functionality that returns if there is no cut.
    if end_cut == True:
        queried_cut = end_cut_query_additive(agent, prefs, initial_cut, value, epsilon)
    else:
        queried_cut = start_cut_query_additive(agent, prefs, initial_cut, value, epsilon)
    return queried_cut


def bisection_cut_query_additive(agent, prefs, start, end, epsilon):
    half_value = value_query_additive(agent, prefs, start,
                                      end, epsilon) / 2
    mid_cut = cut_query_additive(agent, prefs, start, half_value, epsilon, end_cut = True)
    return mid_cut



def compute_equipartition_additive(prefs, epsilon):
    agents = [0,1,2]
    rightmost_mark = 0
    for i in agents:
        third_of_total = value_query_additive(i, prefs, 0, 1, epsilon) / 3
        right_cut = cut_query_additive(i, prefs, 1, third_of_total, epsilon, end_cut = False)
        if right_cut > rightmost_mark:
            rightmost_mark = right_cut
            chosen_agent = i
    third_of_total = value_query_additive(chosen_agent, prefs, 0, 1, epsilon) / 3
    left_cut = cut_query_additive(chosen_agent, prefs, 0, third_of_total, epsilon, end_cut = True)
    right_cut = rightmost_mark
    division = ThreeAgentPortion(left_cut, right_cut)
    return division, chosen_agent

def slice_values_additive(agent, prefs, division, epsilon):
    left_slice_value = np.array([value_query_additive(agent, prefs, 0, division.left, 
                                                      epsilon)])
    middle_slice_value = np.array([value_query_additive(agent, prefs, division.left, division.right, 
                                                         epsilon)])
    right_slice_value = np.array([value_query_additive(agent, prefs, division.right, 1, 
                                                       epsilon)])
    return np.concatenate([left_slice_value, middle_slice_value, 
                           right_slice_value])

def check_unique_preferences_additive(prefs, division, epsilon):
    agents = [0,1,2]
    agents_number = 3
    slices_number = 3
    agent_slice_values = np.zeros((agents_number,slices_number))
    for agent in agents:
        agent_slice_values[agent] = slice_values_additive(agent, prefs, division, epsilon)                                                                        
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if (j == i) or (j == k) or (i == k):
                    continue
                if  (np.isclose(agent_slice_values[0][i], 
                                np.max(agent_slice_values[0]), rtol = 0, atol = epsilon) and \
                    np.isclose(agent_slice_values[1][j], 
                                np.max(agent_slice_values[1]), rtol = 0, atol = epsilon) and \
                    np.isclose(agent_slice_values[2][k],
                                np.max(agent_slice_values[2]), rtol = 0, atol = epsilon)):
                    return True
    return False

def middle_preferred_check(prefs, division, chosen_agent, epsilon):
    agents = [0,1,2]
    agents = np.delete(agents, chosen_agent)
    agents_number = 3
    slices_number = 3
    agent_slice_values = np.zeros((agents_number,slices_number))
    for agent in agents:
        agent_slice_values[agent] = slice_values_additive(agent, prefs, division, epsilon)
    if  (np.isclose(agent_slice_values[agents[0]][1], 
                    np.max(agent_slice_values[agents[0]]), rtol = 0, atol = epsilon / 2) and \
         np.isclose(agent_slice_values[agents[1]][1],
                    np.max(agent_slice_values[agents[1]]), rtol = 0, atol = epsilon / 2)):   
        return True
    else:
        return False

def middle_preferred_bounds_update(prefs, cut_bounds, chosen_agent, epsilon):
    right_cut = bisection_cut_query_additive(chosen_agent, prefs, cut_bounds.lower,
                                             cut_bounds.upper, epsilon)
    right_slice_value = value_query_additive(chosen_agent, prefs, right_cut, 1, epsilon) 
    left_cut = cut_query_additive(chosen_agent, prefs, 0, right_slice_value, epsilon, end_cut = True) 
    division = ThreeAgentPortion(left_cut, right_cut)
    if middle_preferred_check(prefs, division, chosen_agent, epsilon) == True:
        cut_bounds.upper = right_cut
    else:
        cut_bounds.lower = right_cut 
    return cut_bounds, division                                                                                                                                          
    

def middle_preferred_case(prefs, division, chosen_agent, epsilon):
    upper_bound = division.right
    half_of_total = value_query_additive(chosen_agent, prefs, 0, 1, epsilon) / 2
    lower_bound = cut_query_additive(chosen_agent, prefs, 1, 
                                     half_of_total, epsilon, end_cut = False)
    cut_bounds = Bounds(lower_bound, upper_bound)
    while check_unique_preferences_additive(prefs, division, epsilon) == False:
        cut_bounds, division = middle_preferred_bounds_update(prefs, cut_bounds, chosen_agent, epsilon)
    return division

def left_preferred_check(prefs, division, chosen_agent, epsilon):
    agents = [0,1,2]
    agents = np.delete(agents, chosen_agent)
    agents_number = 3
    slices_number = 3
    agent_slice_values = np.zeros((agents_number,slices_number))
    for agent in agents:
        agent_slice_values[agent] = slice_values_additive(agent, prefs, division, epsilon)
    if  (np.isclose(agent_slice_values[agents[0]][0], 
                    np.max(agent_slice_values[agents[0]]), rtol = 0, atol = epsilon / 2) and \
         np.isclose(agent_slice_values[agents[1]][0],
                    np.max(agent_slice_values[agents[1]]), rtol = 0, atol = epsilon / 2)):   
        return True
    else:
        return False

def left_preferred_bounds_update(prefs, cut_bounds, chosen_agent, epsilon):
    left_cut = bisection_cut_query_additive(chosen_agent, prefs, cut_bounds.lower,
                                            cut_bounds.upper, epsilon)
    right_cut = bisection_cut_query_additive(chosen_agent, prefs, left_cut, 1, epsilon) 
    division = ThreeAgentPortion(left_cut, right_cut)
    if left_preferred_check(prefs, division, chosen_agent, epsilon) == True:
        cut_bounds.upper = left_cut
    else:
        cut_bounds.lower = left_cut
    return cut_bounds, division                                                                                                                                          
    

def left_preferred_case(prefs, division, chosen_agent, epsilon):
    lower_bound = 0
    upper_bound = division.left
    cut_bounds = Bounds(lower_bound, upper_bound)
    while check_unique_preferences_additive(prefs, division, epsilon) == False:
        cut_bounds, division = left_preferred_bounds_update(prefs, cut_bounds, chosen_agent, epsilon)
    return division


def branzei_nisan_additive(raw_prefs, cakeSize):
    prefs = one_lipschitz(raw_prefs, cakeSize)
    equipartition, chosen_agent = compute_equipartition_additive(prefs, epsilon)
    if check_unique_preferences_additive(prefs, equipartition, epsilon) == True:
        slice_assignments = assign_slices(equipartition, prefs, 3, epsilon, additive = True)
        raw_envy_free_division = raw_division(equipartition, cakeSize, 3)
        return jsonify({'equipartition': raw_envy_free_division,
                        'assignment': slice_assignments,
                        'chosen_agent': chosen_agent,
                        'condition': 0})
    if middle_preferred_check(prefs, equipartition, chosen_agent, epsilon) == True:
        envy_free_division = middle_preferred_case(prefs, equipartition, chosen_agent, epsilon)
        specifics = 0
    else:
        envy_free_division = left_preferred_case(prefs, equipartition, chosen_agent, epsilon)
        specifics = 1
    raw_equipartition = raw_division(equipartition, cakeSize, 3)
    slice_assignments = assign_slices(envy_free_division, prefs, 3, epsilon, additive = True)
    raw_envy_free_division = raw_division(envy_free_division, cakeSize, 3)
    return jsonify({'equipartition': raw_equipartition,
                    'division': raw_envy_free_division,
                    'assignment': slice_assignments,
                    'chosen_agent': chosen_agent,
                    'condition': 1,
                    'specifics': specifics})


#piecewise-constant algorithm

def find_segments_intervals(prefs):
    breakpoints = set()
    for agents in prefs:
        for segments in agents:
            assert (segments['startValue'] == segments['endValue']), \
                'Valuations must be piecewise-constant for this algorithm.'
            if segments['startValue'] > 0:
                breakpoints.add(segments['start'])
                breakpoints.add(segments['end'])

    # Convert breakpoints to a sorted list
    sorted_breakpoints = sorted(breakpoints)
    segment_intervals=[]
    for i in range(1, len(sorted_breakpoints)):
        left = sorted_breakpoints[i-1]
        right = sorted_breakpoints[i]
        segment_intervals.append({
                'start': left,
                'end': right
            })
    return segment_intervals


def remove_zeros_from_segments(segmented_prefs, agents_number):
    amount_of_segments = len(segmented_prefs[0])
    segments_to_remove = []
    for i in range(amount_of_segments):
        zero_values = 0
        for j in range(agents_number):
            if segmented_prefs[j][i]['value'] == 0:
                zero_values += 1
                if zero_values == agents_number:
                    segments_to_remove.append(i)
    sorted_segments_to_remove = sorted(segments_to_remove, reverse=True)
    for i in sorted_segments_to_remove:
        for j in range(agents_number):
            del segmented_prefs[j][i]
    return segmented_prefs



def find_segments(prefs, agents_number):
    segments_intervals = find_segments_intervals(prefs)
    segmented_prefs = [[] for _ in range(agents_number)]
    for i in range(agents_number):
        for intervals in segments_intervals:
            for segments in prefs[i]:
                if (((segments['start'] >= intervals['start']) and (segments['start'] < intervals['end'])) or \
                    ((segments['end'] > intervals['start']) and (segments['end'] <= intervals['end'])) or \
                    ((segments['start'] <= intervals['start']) and (segments['end'] >= intervals['end']))):
                    segmented_prefs[i].append({'start': intervals['start'],
                                               'end': intervals['end'],
                                               'value': segments['startValue'],
                                               'area': (intervals['end'] - intervals['start']) * segments['startValue']})
                    break
    segmented_prefs_without_zeros = remove_zeros_from_segments(segmented_prefs, agents_number)
    return segmented_prefs_without_zeros


def first_slice_value(x, segments, agent, cut):
    first_agent_constant_value = 0
    cut_range = segments[agent][cut]['end'] - segments[agent][cut]['start']
    for i in range(cut):
        first_agent_constant_value += segments[agent][i]['area']
    first_agent_variable_value = segments[agent][cut]['value']
    if ((0 <= x) and (x <= cut_range)):
        value = first_agent_constant_value + x * first_agent_variable_value 
        return value 
    else:
        return "Input out of bounds"
    

def middle_slice_value(x, y, segments, agent, cut_one, cut_two):
    cut_one_range = segments[agent][cut_one]['end'] - segments[agent][cut_one]['start']
    cut_two_range = segments[agent][cut_two]['end'] - segments[agent][cut_two]['start']
    middle_agent_constant_value = 0
    for i in range(cut_one+1, cut_two):
        middle_agent_constant_value += segments[agent][i]['area']
    middle_agent_variable_value_component_one = segments[agent][cut_one]['value']
    middle_agent_variable_value_component_two = segments[agent][cut_two]['value']
    assert (((0 <= x) and (x <= cut_one_range)) and ((0 <= y) and (y <= cut_two_range))), \
        "cut out of range"
    if cut_one != cut_two:
        value = middle_agent_constant_value + (cut_one_range - x) * middle_agent_variable_value_component_one + \
                y * middle_agent_variable_value_component_two
    else:
        value = middle_agent_constant_value + (y - x) * middle_agent_variable_value_component_one
    return value


def last_slice_value(y, segments, agent, cut):
    last_agent_constant_value = 0
    cut_range = segments[agent][cut]['end'] - segments[agent][cut]['start']
    amount_of_segments = len(segments[agent])
    for i in range(cut+1, amount_of_segments):
        last_agent_constant_value += segments[agent][i]['area']
    last_agent_variable_value = segments[agent][cut]['value']
    if ((0 <= y) and (y <= cut_range)):
        value =  last_agent_constant_value + (cut_range - y) * last_agent_variable_value
        return value
    else:
        return "Input out of bounds"
    

def constraints_three_agents(segments, agents, cuts, params):
    def constraint1(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]
        cuts = params[4]
        slice_one_first_agent_value = first_slice_value(x, segments, agents[0], cuts[0])
        slice_two_first_agent_value = middle_slice_value(x, y, segments, agents[0], cuts[0], cuts[1])
        return slice_one_first_agent_value - slice_two_first_agent_value

    def constraint2(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]
        cuts = params[4]
        slice_one_first_agent_value = first_slice_value(x, segments, agents[0], cuts[0])
        slice_three_first_agent_value = last_slice_value(y, segments, agents[0], cuts[1])
        return slice_one_first_agent_value - slice_three_first_agent_value

    def constraint3(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]
        cuts = params[4]
        slice_two_second_agent_value = middle_slice_value(x, y, segments, agents[1], cuts[0], cuts[1])
        slice_one_second_agent_value = first_slice_value(x, segments, agents[1], cuts[0])
        return slice_two_second_agent_value - slice_one_second_agent_value

    def constraint4(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]
        cuts = params[4]
        slice_two_second_agent_value = middle_slice_value(x, y, segments, agents[1], cuts[0], cuts[1])
        slice_three_second_agent_value = last_slice_value(y, segments, agents[1], cuts[1])
        return slice_two_second_agent_value - slice_three_second_agent_value

    def constraint5(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]

        cuts = params[4]
        slice_three_third_agent_value = last_slice_value(y, segments, agents[2], cuts[1])
        slice_one_third_agent_value = first_slice_value(x, segments, agents[2], cuts[0])
        return slice_three_third_agent_value - slice_one_third_agent_value

    def constraint6(vars, params):
        cut_one, cut_two = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[2]
        agents = params[3]
        cuts = params[4]
        slice_three_third_agent_value = last_slice_value(y, segments, agents[2], cuts[1])
        slice_two_third_agent_value = middle_slice_value(x, y, segments, agents[2], cuts[0], cuts[1])
        return slice_three_third_agent_value - slice_two_third_agent_value

    def constraint7(vars, params):
        cut_one, cut_two = vars
        return cut_two - cut_one

    cons = [{'type': 'ineq', 'fun': constraint1, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint2, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint3, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint4, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint5, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint6, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint7, 'args': (params,)}]

    return cons


def constraints_four_agents(segments, agents, cuts, params):
    def constraint1(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_one_first_agent_value = first_slice_value(x, segments, agents[0], cuts[0])
        slice_two_first_agent_value = middle_slice_value(x, y, segments, agents[0], cuts[0], cuts[1])
        return slice_one_first_agent_value - slice_two_first_agent_value
            

    def constraint2(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_one_first_agent_value = first_slice_value(x, segments, agents[0], cuts[0])
        slice_three_first_agent_value = middle_slice_value(y, z, segments, agents[0], cuts[1], cuts[2])
        return slice_one_first_agent_value - slice_three_first_agent_value

    def constraint3(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_one_first_agent_value = first_slice_value(x, segments, agents[0], cuts[0])
        slice_four_first_agent_value = last_slice_value(z, segments, agents[0], cuts[2])
        return slice_one_first_agent_value - slice_four_first_agent_value

    def constraint4(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_two_second_agent_value =  middle_slice_value(x, y, segments, agents[1], cuts[0], cuts[1])
        slice_one_second_agent_value = first_slice_value(x, segments, agents[1], cuts[0])
        return slice_two_second_agent_value - slice_one_second_agent_value

    def constraint5(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_two_second_agent_value =  middle_slice_value(x, y, segments, agents[1], cuts[0], cuts[1])
        slice_three_second_agent_value = middle_slice_value(y, z, segments, agents[1], cuts[1], cuts[2])
        return slice_two_second_agent_value - slice_three_second_agent_value

    def constraint6(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_two_second_agent_value =  middle_slice_value(x, y, segments, agents[1], cuts[0], cuts[1])
        slice_four_second_agent_value = last_slice_value(z, segments, agents[1], cuts[2])
        return slice_two_second_agent_value - slice_four_second_agent_value

    def constraint7(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_three_third_agent_value = middle_slice_value(y, z, segments, agents[2], cuts[1], cuts[2])
        slice_one_third_agent_value = first_slice_value(x, segments, agents[2], cuts[0])
        return slice_three_third_agent_value - slice_one_third_agent_value

    def constraint8(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_three_third_agent_value = middle_slice_value(y, z, segments, agents[2], cuts[1], cuts[2])
        slice_two_third_agent_value = middle_slice_value(x, y, segments, agents[2], cuts[0], cuts[1])
        return slice_three_third_agent_value - slice_two_third_agent_value

    def constraint9(vars, params):
        cut_one, cut_two, cut_three = vars
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_three_third_agent_value = middle_slice_value(y, z, segments, agents[2], cuts[1], cuts[2])
        slice_four_third_agent_value = last_slice_value(z, segments, agents[2], cuts[2])
        return slice_three_third_agent_value - slice_four_third_agent_value

    def constraint10(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_four_fourth_agent_value = last_slice_value(z, segments, agents[3], cuts[2])
        slice_one_fourth_agent_value = first_slice_value(x, segments, agents[3], cuts[0])
        return slice_four_fourth_agent_value - slice_one_fourth_agent_value

    def constraint11(vars, params):
        cut_one, cut_two, cut_three = vars
        x = cut_one - params[0]
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_four_fourth_agent_value = last_slice_value(z, segments, agents[3], cuts[2])
        slice_two_fourth_agent_value = middle_slice_value(x, y, segments, agents[3], cuts[0], cuts[1])
        return slice_four_fourth_agent_value - slice_two_fourth_agent_value

    def constraint12(vars, params):
        cut_one, cut_two, cut_three = vars
        y = cut_two - params[1]
        z = cut_three - params[2]
        segments = params[3]
        agents = params[4]
        cuts = params[5]
        slice_four_fourth_agent_value = last_slice_value(z, segments, agents[3], cuts[2])
        slice_three_fourth_agent_value = middle_slice_value(y, z, segments, agents[3], cuts[1], cuts[2])
        return slice_four_fourth_agent_value - slice_three_fourth_agent_value

    def constraint13(vars, params):
        cut_one, cut_two, cut_three = vars
        return cut_two - cut_one

    def constraint14(vars, params):
        cut_one, cut_two, cut_three = vars
        return cut_three - cut_one

    def constraint15(vars, params):
        cut_one, cut_two, cut_three = vars
        return cut_three - cut_two

    cons = [{'type': 'ineq', 'fun': constraint1, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint2, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint3, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint4, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint5, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint6, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint7, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint8, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint9, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint10, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint11, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint12, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint13, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint14, 'args': (params,)},
            {'type': 'ineq', 'fun': constraint15, 'args': (params,)}]

    return cons


def find_division_three_agents(segments, agents, cuts):
    cut_one_lower_bound = segments[0][cuts[0]]['start']
    cut_one_upper_bound = segments[0][cuts[0]]['end']
    cut_two_lower_bound = segments[0][cuts[1]]['start']
    cut_two_upper_bound = segments[0][cuts[1]]['end']

    params = [cut_one_lower_bound, cut_two_lower_bound, segments, agents, cuts]
    cons = constraints_three_agents(segments, agents, cuts, params)
    initial_guess = [cut_one_lower_bound, cut_two_lower_bound]
    cut_bounds = [(cut_one_lower_bound, cut_one_upper_bound), (cut_two_lower_bound, cut_two_upper_bound)]

    def objective(vars, *args):
        return 0

    result = minimize(objective, initial_guess, args=(params,), constraints=cons, bounds= cut_bounds)

    if result.success:
        return {'envy_free_check':True, 'exact_cuts': result.x}
    else:
        return {'envy_free_check':False, 'exact_cuts': None}
    

def find_division_four_agents(segments, agents, cuts):
    cut_one_lower_bound = segments[0][cuts[0]]['start']
    cut_one_upper_bound = segments[0][cuts[0]]['end']
    cut_two_lower_bound = segments[0][cuts[1]]['start']
    cut_two_upper_bound = segments[0][cuts[1]]['end']
    cut_three_lower_bound = segments[0][cuts[2]]['start']
    cut_three_upper_bound = segments[0][cuts[2]]['end']
    
    params = [cut_one_lower_bound, cut_two_lower_bound, cut_three_lower_bound, segments, agents, cuts]
    cons = constraints_four_agents(segments, agents, cuts, params)
    initial_guess = [cut_one_lower_bound, cut_two_lower_bound, cut_three_lower_bound]
    cut_bounds = [(cut_one_lower_bound, cut_one_upper_bound), (cut_two_lower_bound, cut_two_upper_bound),
                  (cut_three_lower_bound, cut_three_upper_bound)]

    def objective(vars, *args):
        return 0

    result = minimize(objective, initial_guess, args=(params,), constraints=cons, bounds= cut_bounds)

    if result.success:
        return {'envy_free_check':True, 'exact_cuts': result.x}
    else:
        return {'envy_free_check':False, 'exact_cuts': None}
    

def find_division(segments, agents, cuts, agents_number):
    if agents_number == 3:
        return find_division_three_agents(segments, agents, cuts)
    if agents_number == 4:
        return find_division_four_agents(segments, agents, cuts)
    

def solver(segments, agents_number):
    amount_of_segments = len(segments[0])
    cut_positions = []
    assert (agents_number == 3) or (agents_number == 4),\
        "Invalid agents number for algorithm"
    if agents_number == 3:
        for cut_one in range(amount_of_segments):
            for cut_two in range(cut_one, amount_of_segments):
                cut_positions.append([cut_one, cut_two])
    if agents_number == 4:
        for cut_one in range(amount_of_segments):
            for cut_two in range(cut_one, amount_of_segments):
                for cut_three in range(cut_two, amount_of_segments):
                    cut_positions.append([cut_one, cut_two, cut_three])
    agents_list = [i for i in range(agents_number)]
    agents_permutations = list(itertools.permutations(agents_list))
    for agents in agents_permutations:
        for cuts in cut_positions:
            info = find_division(segments, agents, cuts, agents_number)
            if info['envy_free_check'] == True:
                return cuts, info['exact_cuts'], agents
            else:
                continue
    return False

def piecewise_constant_algorithm(preferences, cake_size):
    agents_number = len(preferences)
    raw_segments = find_segments(preferences, agents_number)
    preferences = change_bounds(preferences, cake_size)
    segments = find_segments(preferences, agents_number)
    cut_positions, exact_cuts, agents = solver(segments, agents_number)
    if agents_number == 3:
        envy_free_division = ThreeAgentPortion(exact_cuts[0], exact_cuts[1])
        slice_assignments = {1: agents[0], 2: agents[1], 3: agents[2]}
        raw_envy_free_division = raw_division(envy_free_division, cake_size, 3)
    if agents_number == 4:
        envy_free_division = FourAgentPortion(exact_cuts[0], exact_cuts[1], exact_cuts[2])
        slice_assignments = {1: agents[0], 2: agents[1], 
                            3: agents[2], 4: agents[3]}
        raw_envy_free_division = raw_division(envy_free_division, cake_size, 4)
    
    return jsonify({'segments': raw_segments,
                    'cut_positions': cut_positions,
                    'division': raw_envy_free_division,
                    'assignment': slice_assignments,
                    'agents_number': agents_number})
    

@app.route('/api/three_agent_additive', methods=['POST'])
def three_agent_additive():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    # result = branzei_nisan(preferences, cake_size)
    # result_as_dict = [result.left, result.right]
    # return jsonify({'result': result_as_dict})
    return branzei_nisan(preferences, cake_size)


@app.route('/api/three_agent', methods=['POST'])
def three_agent():
    data = request.json
    preferences = data.get('preferences')
    cake_size = data.get('cakeSize')
    
    # Call your algorithm function with preferences and cake_size
    # result = branzei_nisan(preferences, cake_size)
    # result_as_dict = [result.left, result.right]
    # return jsonify({'result': result_as_dict})
    return branzei_nisan_additive(preferences, cake_size)

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


@app.route('/api/piecewise_constant', methods=['POST'])
def piecewise_constant():
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
    return piecewise_constant_algorithm(preferences, cake_size)


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
