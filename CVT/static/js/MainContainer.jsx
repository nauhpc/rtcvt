/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import Row from 'react-bootstrap';

import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';

export default class MainContainer extends React.Component {
  constructor(props){
    super(props);
  }

  render() {
    return (
      <div style={styles.mainContainer}>
        <Topbar />
        <div style={styles.childContainer}>
          {this.props.children}
        </div>
      </div>
    )
  }
}

const styles = {
  mainContainer:{
    display:'flex',
    flexDirection:'column',
    flex:1,
  },
  childContainer:{
    paddingTop:'70px',
  }
}
