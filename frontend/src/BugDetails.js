import React from 'react';

const BugDetails = ({ match }) => (
  <div>
    {match.params.bugId}
  </div>
);

export default BugDetails;
