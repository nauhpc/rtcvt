/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import {
  Button,
  ButtonGroup,
  Col,
  DropdownButton,
  MenuItem,
  PageHeader,
  Panel,
  Well
} from 'react-bootstrap';

import Dataview from './Dataview.jsx';
import Usageview from './Usageview.jsx';
import Gresview from './Gresview.jsx';
import Tresview from './Tresview.jsx';


export default class Cluster extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      groups: ['please wait...'],
      viewGroup: 'User',
      username: 'null',
      cluster: 'null'
    };
  }

  apiCall(props){
    $.ajax({
      url: 'api/clusters',
      datatype: 'json',
      success: function(data){
        this.setState({cluster: data[0].name});
      }.bind(this)
    });
    $.ajax({
      url: '/api/getusergroups/',
      datatype: 'json',
      success: function(data){
        this.setState({groups: data})
      }.bind(this)
    });
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
    this.apiCall(this.props);
    this.interval = setInterval(()=>{this.apiCall(this.props)}, 60000);
  }

  componentWillReceiveProps(nextProps){
    clearInterval(this.interval);
    this.apiCall(nextProps);
    this.interval = setInterval(()=>{this.apiCall(nextProps)}, 5000); 
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render(){
    let groupButtonTitle = 'Groups';
    if (this.state.viewGroup !== 'User') {groupButtonTitle = this.state.viewGroup;}
    let cluster = 'null';
    if (this.props.params.id === undefined)
      cluster = this.state.cluster;
    else
      cluster = this.props.params.id;
    const viewOptions = this.state.groups.map(
      (group, k) => {
        return(
          <MenuItem key={k} eventKey={group.name}>{group.name}</MenuItem>
        );
      }
    );

    let GRES = null;
    if (cluster!=='All' && this.state.viewGroup!=='All' && this.state.viewGroup!=='User'){
      GRES = (
          <div>
            <Panel collapsible header={<b>{this.state.viewGroup} GRES Summary</b>}>
              <Gresview cluster={cluster} group={this.state.viewGroup}/>
            </Panel>
            <Panel collapsible header={<b>{this.state.viewGroup} TRES Summary</b>}>
              <Tresview cluster={cluster} group={this.state.viewGroup}/>
            </Panel>
          </div>
      );
    }

    let job = null;
    if (this.state.username!=='null'){
      job = (
      <Panel collapsible defaultExpanded={true} header={<b>Jobs</b>}>
        <ButtonGroup style={{float:'right'}}>
          <Button bsStyle={this.state.viewGroup === 'User' ? 'primary' : 'default'}
            onClick={() => {this.setState({viewGroup: 'User'});}}>
              User
          </Button>
          <DropdownButton bsStyle={this.state.viewGroup !== 'User' ? 'primary' : 'default'}
            title={groupButtonTitle}
            id='Group Selector'
            onSelect={
              (eventKey, event) => {this.setState({viewGroup: eventKey});}
            }>
            <MenuItem eventKey='All'>All My Groups</MenuItem>
            <MenuItem divider />
            {viewOptions}
          </DropdownButton>
        </ButtonGroup>
        <hr/>
        <Dataview group={this.state.viewGroup} cluster={cluster}/>
      </Panel>);
    }

    return(
      <Col md={8} mdOffset={2}>
        <Panel collapsible defaultExpanded={true} header={<b>Cluster Summary</b>}>
          <Usageview cluster={cluster}/>
        </Panel>
        {GRES}
        {job}
      </Col>
    );
  }
}
