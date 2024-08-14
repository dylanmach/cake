from base import hollender_rubinstein 
from base import piecewise_constant_algorithm
from base import branzei_nisan_additive
import numpy as np
from timeit import default_timer as timer
import csv

def runtime_three_agents():
    for _ in range(20):
        print('Hello')
        agents_number = 3
        cake_size = 5
        prefs = [[] for _ in range(agents_number)]
        values = np.random.uniform(low=0, high=10, size=(agents_number, cake_size))
        for i in range(agents_number):
            for j in range(cake_size):
                prefs[i].append({'agent': i,
                                'start': j,
                                'end': j + 1,
                                'startValue': values[i][j],
                                'endValue': values[i][j]
                })
        with open('test_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['agent', 'start', 'end', 'startValue', 'endValue']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(agents_number):
                writer.writerows(prefs[i])
        start_time_branzei_nisan = timer()
        branzei_nisan_additive(prefs, cake_size)
        end_time_branzei_nisan = timer()
        time_elapsed_branzei_nisan = end_time_branzei_nisan - \
                                     start_time_branzei_nisan
        print(f"Branzei Nisan with cake size {cake_size} takes {time_elapsed_branzei_nisan} seconds to run")

        start_time_piecewise_constant = timer()
        piecewise_constant_algorithm(prefs, cake_size)
        end_time_piecewise_constant = timer()
        time_elapsed_piecewise_constant = end_time_piecewise_constant - \
                                          start_time_piecewise_constant
        print(f"piecewise constant with cake size {cake_size} takes \
            {time_elapsed_piecewise_constant} seconds to run")
        
        
        data = [
            {'algo': 'Hollender_Rubinstein', 'cake_size': cake_size, \
                    'runtime': time_elapsed_branzei_nisan},
            {'algo': 'Piecewise_constant', 'cake_size': cake_size, \
                   'runtime': time_elapsed_piecewise_constant}
        ]

        #Uncomment the below to create the csv file

        # with open('four_agent_runtime_tests.csv', 'w', newline='') as csvfile:
        #     fieldnames = ['algo', 'cake_size', 'runtime']
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()
        #     writer.writerows(data)

        with open('three_agent_runtime_tests.csv', 'a', newline='') as csvfile:
            fieldnames = ['algo', 'cake_size', 'runtime']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)

def runtime_four_agents():
    for _ in range(20):
        print('Hello')
        agents_number = 4
        cake_size = 5
        prefs = [[] for _ in range(agents_number)]
        values = np.random.uniform(low=0, high=10, size=(agents_number, cake_size))
        for i in range(agents_number):
            for j in range(cake_size):
                prefs[i].append({'agent': i,
                                'start': j,
                                'end': j + 1,
                                'startValue': values[i][j],
                                'endValue': values[i][j]
                })
        with open('test_data.csv', 'w', newline='') as csvfile:
            fieldnames = ['agent', 'start', 'end', 'startValue', 'endValue']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for i in range(agents_number):
                writer.writerows(prefs[i])
        start_time_hollender_rubinstein = timer()
        hollender_rubinstein(prefs, cake_size)
        end_time_hollender_rubinstein = timer()
        time_elapsed_hollender_rubinstein = end_time_hollender_rubinstein - \
                                            start_time_hollender_rubinstein
        print(f"Hollender-Rubinstein with cake size {cake_size} takes {time_elapsed_hollender_rubinstein} seconds to run")

        start_time_piecewise_constant = timer()
        piecewise_constant_algorithm(prefs, cake_size)
        end_time_piecewise_constant = timer()
        time_elapsed_piecewise_constant = end_time_piecewise_constant - \
                                            start_time_piecewise_constant
        print(f"piecewise constant with cake size {cake_size} takes \
            {time_elapsed_piecewise_constant} seconds to run")
        
        
        data = [
            {'algo': 'eval', 'cake_size': cake_size, \
                    'runtime': time_elapsed_hollender_rubinstein},
            {'algo': 'Piecewise_constant', 'cake_size': cake_size, \
                    'runtime': time_elapsed_piecewise_constant}
            ]
        
        #Uncomment the below to create the csv file

        # with open('four_agent_runtime_tests.csv', 'w', newline='') as csvfile:
        #     fieldnames = ['algo', 'cake_size', 'runtime']
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()
        #     writer.writerows(data)

        with open('four_agent_runtime_tests.csv', 'a', newline='') as csvfile:
            fieldnames = ['algo', 'cake_size', 'runtime']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerows(data)
    

if __name__ == "__main__":
    #Uncomment whichever tests you wish to run.

    #runtime_three_agents()
    runtime_four_agents()
