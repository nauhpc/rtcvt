/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import ReactDOM from 'react-dom';
import {Router, Route, hashHistory, IndexRoute } from 'react-router';

import MainContainer from './MainContainer.jsx';
import QuickTest from './QuickTest.jsx';
import Cluster from './Cluster.jsx';

class Index extends React.Component {
  constructor(props){
    super(props);
  }

  render() {
    return (
      <div style={styles.containingDiv}>
      <Router history={hashHistory}>
        <Route component={MainContainer}>
          <Route path='/' component={Cluster}/>
          <Route path='cluster/:id' component={Cluster}/>
        </Route>
      </Router>
      </div>
    );
  }
}

const styles = {
  containingDiv: {height: '100%'},
};

ReactDOM.render((<Index />), document.getElementById('container'))
