# A Visual Solver for Fair Division

This is a github repository for an in-development beta for a new version of the Fair Slice platform. For the original github repository for Fair slice, developed by Andy Ernst, please visit [Fair Slice](https://github.com/AndyCErnst/cake/).

My contributions are mainly located in the backend directory. This is where I created a [Flask](https://flask.palletsprojects.com/en/3.0.x/) app, the details of which are located within base.py. This script contains all backend code for the Branzei-Nisan, Hollender-Rubinstein, and Piecewise-Constant algorithms. These communicate to the frontend through the associated .ts files in /src/Graph/algorithm, branzeiNisan.ts, hollenderRubinstein.ts, and piecewiseConstant.ts. They communicate via axios.

To launch the website in development mode, run "npm install", "npm i -S react-scripts" and then "npm start" in the root directory to launch the frontend, which is written in [React](https://react.dev/) and subsequently run "flask run" in the backend directory after installing the requirements.txt file in a virtual python environment to launch the backend, which is written in [Flask](https://flask.palletsprojects.com/en/3.0.x/). You can also view a beta version of the frontend of the site at [Fair Slice Beta](https://fairslicebeta.netlify.app) to view the interactive course and UI, though this frontend cannot run backend algorithms.

The runtime tests for the backend algorithms are located in the backend directory under runtime.py and the runtime test for Selfridge-Conway is located in the /src/Graph/algorithm under selfridgeConway.test.ts as the last function. The runtime test results are located in the test data directory. There is a typo in three_agent_runtime_tests.csv where it says "Hollender-Rubinstein" instead of "Branzei-Nisan", but note that these runtime tests are for Branzei-Nisan. The runtime tests were run in blocks of 20 and 50 depending on what was required but, in some cases, tests were interrupted and I opted to run a new batch. This would explain any minor discrepancy in results if you choose to average more than the last 20 or 50 values in a given test run. 

 
