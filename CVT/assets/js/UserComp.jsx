/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import {Button, Nav} from 'react-bootstrap';

export default class UserComp extends React.Component{
    constructor(props){
        super(props);
        this.state = {
            username:'null'
        }
    }

    apiCall(){
      $.ajax({
        url: '/api/activeuser/',
        datatype: 'json',
        success: function(data){
          this.setState({username: data.username});
        }.bind(this),
        error: function(Request, textStatus, errorThrown){
          this.setState({username: 'null'});
        }.bind(this),
      });
    }

  componentDidMount(){
    this.apiCall();
  }

  componentWillReceiveProps(nextProps){
    this.apiCall();  
  }

  render(){
    if (this.state.username!=='null'){
        return(
          <Nav pullRight>
            <text style={{float:'left', marginTop:'10%', paddingRight:'0.15em'}}>Hello, {this.state.username}!</text>
            <Button
              style={{margin: '0.2em'}}
              bsStyle={'default'}
              bsSize={'large'}
              onClick={() => {window.location = '/accounts/logout'}}
            >
              Logout
            </Button>
          </Nav>
        );
    }
    else{
        return(
          <Nav pullRight>
            <Button
              style={{margin: '0.2em'}}
              bsStyle={'default'}
              bsSize={'large'}
              onClick={() => {window.location = '/accounts/login'}}
            >
              Login
            </Button>
          </Nav>
        );
    }
  }
}
