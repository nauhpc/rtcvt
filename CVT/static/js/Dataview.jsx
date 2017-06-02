/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import {Button} from 'react-bootstrap';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
import JobTable from './JobTable.jsx';
require('../styles/table-style.css');


export default class Dataview extends React.Component {
  constructor(props){
    super(props);

    this.state = {
      data:[],
      displayFinJobs: false
    }
  }

  apiCall(props){
    var url;
    if (props.group!=='User'){
      url = '/api/getgroupjobs/'.concat(props.group).concat('/');
      if (props.cluster!=='All'){
        url = url.concat('?cluster=').concat(props.cluster);
      }
    }
    else {
      url = '/api/getjobs/';
      if (props.cluster!=='All'){
        url = url.concat('?cluster=').concat(props.cluster);
      }
    }

    $.ajax({
      url: url,
      datatype: 'json',
      success: function(data){
        this.setState({data: this.aggregateBatchJobs(data)});
      }.bind(this)
    })
  }

  aggregateBatchJobs(jobs){
    jobs = jobs.slice();
    let batchJobs = {};
    let delJobs = [];

    jobs.map((job,index) => {
      let strIndex = job.sched_jobid.search(/_[0-9]+/);
      if(strIndex!==-1){
        let rootName = job.sched_jobid.slice(0,strIndex);
        if (!(batchJobs[rootName])) {
          batchJobs[rootName] = {
            sched_jobid:rootName,
            name:'Array: '.concat(job.name),
            group:job.group,
            state:'CD',
            data:[]
          }
        }
        batchJobs[rootName].data.push(job);
        if (job.state == 'R' || 'PD'){
          batchJobs[rootName].state = job.state;
        }
        delJobs.push(job);
      }
    });
    delJobs.map((job)=>{
      let jIndex = jobs.indexOf(job);
      if (jIndex!==-1){
        jobs.splice(jIndex, 1);
      }
    });

    for (var prop in batchJobs){
      jobs.push(batchJobs[prop]);
    }
    return jobs
  }

  componentDidMount(){
    this.apiCall(this.props);
    this.interval = setInterval(()=>{this.apiCall(this.props)}, 5000);
  }

  componentWillReceiveProps(nextProps){
    clearInterval(this.interval);
    this.apiCall(nextProps);
    this.interval = setInterval(()=>{this.apiCall(nextProps)}, 5000); 
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  toggleFinJobsDisplay() {
    this.setState({displayFinJobs: !this.state.displayFinJobs});
  }

  render(){
    let headers;
    if (this.props.group!=='User'){
      headers = [['sched_jobid', 'Job ID'], ['name', 'Name'], ['user', 'User'], ['state', 'State'], ['elapsed_time', 'Elapsed Time']];
    }
    else {
      headers = [['sched_jobid', 'Job ID'], ['name', 'Name'], ['group', 'Group'], ['state', 'State'], ['elapsed_time', 'Elapsed Time']];
    }

    let unfinishedJobs = this.state.data.filter(
      (x) => {return x.state == 'R' || x.state == 'PD'}
    );
    let finishedJobs = this.state.data.filter(
      (x) => {return x.state !== 'R' && x.state !== 'PD'}
    );

    let finJobCssDisplay = {display: 'none'};
    if(this.state.displayFinJobs) {
      finJobCssDisplay = {};
    }
    let finJobButtonText = 'Show Finished Jobs';
    if(this.state.displayFinJobs) {
      finJobButtonText = 'Hide Finished Jobs'
    }
    return(
      <div>
        <div>
          <text><h4>Incomplete Jobs</h4></text>
          <JobTable data={unfinishedJobs} headers={headers}/>
        </div>
        <hr/>
        <div style={finJobCssDisplay}>
          <text><h4>Finished Jobs</h4></text>
          <JobTable data={finishedJobs} headers={headers}/>
        </div>
        <Button bsStyle={'link'} style={{float: 'right'}}
          onClick={this.toggleFinJobsDisplay.bind(this)}
        >{finJobButtonText}</Button>
      </div>
    );
  }  
}
