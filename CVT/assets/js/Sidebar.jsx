/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import {Button, ButtonGroup, ButtonToolbar, Panel} from 'react-bootstrap';
import {Link} from 'react-router';

import SidebarItem from './SidebarItem.jsx';
import UserComp from './UserComp.jsx';


export default class Sidebar extends React.Component {
  constructor(props){
    super(props);
    this.state = {data:[]};
  }

  apiCall(){
    $.ajax({
      url: '/api/clusters',
      datatype: 'json',
      success: function(data){
        this.setState({data: data});
      }.bind(this)
    });
  }

  componentDidMount(){
    this.apiCall(this.props);
    this.interval = setInterval(()=>{this.apiCall(this.props)}, 60000);
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render() {
    if (this.state.data) {
      var clusterItems = this.state.data.map(
        (cluster, k) => {
          const myPath = '/#/cluster/'.concat(cluster.name.toString());
          return(
            <Button href={myPath} key={k}>
              {cluster.name}
            </Button>
          );
        }
      );
    }
    return (
      <Panel style={{textAlign: 'center'}}>
        <UserComp/>
        <hr/>
        <ButtonGroup block vertical>
          <Button href='/#/'>
            Home
          </Button>
          {clusterItems}
        </ButtonGroup>
      </Panel>
    );
  }
}

const styles = {
  sidebar:{
    display:'flex',
    flexDirection:'column',
    flex:1,
    marginRight:'5px',
    alignItems:'center',
    backgroundColor:'lightgrey',
    //maxWidth:'32px',
    borderRadius:'1em',
  }
}
