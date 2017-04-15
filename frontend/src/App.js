import React from 'react';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';

import BugList from './BugList';
import BugDetails from './BugDetails';

const App = () => (
  <Router>
    <div className="Buggy">
      <header id="site_title">
        <h1><Link to="/">Buggy</Link></h1>
        <p>+</p>
        <p>Hello User Name</p>
      </header>

      <Route exact path="/" component={BugList} />
      <Route exact path="/bug/:bugId" component={BugDetails} />
    </div>
  </Router>
);

export default App;
