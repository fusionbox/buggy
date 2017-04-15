import React from 'react';
import { graphql, gql } from 'react-apollo';

const BugDetails = ({ data: { loading, bug } }) => {
  if (loading) {
    return <span>Loading...</span>;
  }
  return (
    <div>
      <h1>{bug.title}</h1>
      <pre>
        {JSON.stringify(bug, null, '  ')}
      </pre>
    </div>
  );
};

const bugDetailsQuery = gql`
query bugDetailsQuery($number: String!) {
  bug(number: $number) {
    id
    number
    title
    state
    priority
  }
}
`;

export default graphql(bugDetailsQuery, {
  options: ({ match }) => ({
    variables: {
      number: match.params.bugNumber,
    },
  }),
})(BugDetails);
