import React from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import {
  ApolloClient,
  ApolloProvider,
  createNetworkInterface,
} from 'react-apollo';

import BugList from './BugList';
import BugDetails from './BugDetails';

const networkInterface = createNetworkInterface({
  uri: 'http://localhost:3000/graphql/',
});

const client = new ApolloClient({
  networkInterface,
});

const App = () => (
  <ApolloProvider client={client}>
    <Router>
      <div className="Buggy">
        <header id="site_title">
          <h1><Link to="/">Buggy</Link></h1>
          <p>+</p>
          <p>Hello User Name</p>
        </header>

        <Route exact path="/" component={BugList} />
        <Route exact path="/bug/:bugNumber" component={BugDetails} />
      </div>
    </Router>
  </ApolloProvider>
);

export default App;
