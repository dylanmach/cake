# A Visual Solver for Fair Division

This is a single page application for educating about the problem of fair dividing a resource among several people, commonly called "Cake Cutting." It is built with [React](https://react.dev/) and uses [React-Router](https://reactrouter.com/) for internal routing. 

It was bootstrapped with [Create React App](https://github.com/facebook/create-react-app) which simplifies app set up.

It is hosted from github using Netlify. View it live at https://fairslice.netlify.app/.app/

## Libraries

### Material UI

This project uses [Material UI](https://mui.com/material-ui/) components. These are a robust set of components and styling built by Google and used by hundreds of apps and websites. In the code, anything imported from `@mui/material` or `@mui/icons-material` is Material UI.

### D3

Graph display uses the data visualization library [D3](https://d3js.org/) in a very basic way. The mapping between pixels and graph values uses D3, but that's about it.

## Available Scripts

In the project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

## Learn More

You can learn more in the [Create React App documentation](https://facebook.github.io/create-react-app/docs/getting-started).

To learn React, check out the [React documentation](https://reactjs.org/).

## Working with SVGs

Working with SVGs in React is the same as working with HTML elements, however, the SVG elements include more display logic than HTML. In particular, `z-index` _does not work_ with SVG so elements will be stacked in the _same order_ as in the file. 