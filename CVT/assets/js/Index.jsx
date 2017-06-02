/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import ReactDOM from 'react-dom';
import {Router, Route, hashHistory, IndexRoute} from 'react-router';

import MainContainer from './MainContainer.jsx';
import QuickTest from './QuickTest.jsx';
import Cluster from './Cluster.jsx';

class Index extends React.Component {
  constructor(props){
    super(props);
    this.state={
      routes:(<div/>),
    }
  }

  componentDidMount(){
    this.apiCall(this.props);
  }
  

  apiCall(){
    $.ajax({
      url: '/api/clusters',
      datatype: 'json',
      success: function(data){
        this.setState({routes: (
            <div style={styles.containingDiv}>
            <Router history={hashHistory}>
              <Route component={MainContainer}>
                <Route path='/' component={Cluster} params={{id:data[0].name}}/>
                <Route path='cluster/:id' component={Cluster}/>
              </Route>
            </Router>
            </div>  
          )});
      }.bind(this)
    });
  }

  render() {
    return(this.state.routes);
  }
}

const styles = {
  containingDiv: {height: '100%'},
};

ReactDOM.render((<Index />), document.getElementById('container'))
