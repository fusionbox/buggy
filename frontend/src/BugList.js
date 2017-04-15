import React from 'react';
import { graphql, gql } from 'react-apollo';
import { Link } from 'react-router-dom';

const BugList = ({ data: { loading, allBugs } }) => {
  if (loading) {
    return <span>Loading...</span>;
  }
  return (
    <ol>
      {allBugs.edges.map(({ node }) => (
        <li key={node.id}>
          <Link to={`/bug/${node.number}`}>{node.title}</Link>
        </li>
      ))}
    </ol>
  );
};

const bugListQuery = gql`
query bugListQuery {
  allBugs(first: 100) {
     edges {
      node {
        id
        number
        title
      }
    }
  }
}
`;

export default graphql(bugListQuery)(BugList);
