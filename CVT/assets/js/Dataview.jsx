/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import {Button} from 'react-bootstrap';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
import JobTable from './JobTable.jsx';
require('../styles/table-style.css');
var moment = require('moment');


export default class Dataview extends React.Component {
  constructor(props){
    super(props);

    this.state = {
      colorCoding:[],
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
        this.setState({data: this.modifyJobData(data)});
      }.bind(this)
    })
    $.ajax({
      url: '/api/jobcolorcoding/',
      datatype: 'json',
      success: function(data){
        this.setState({colorCoding:data})
      }.bind(this)
    })
  }

  // Used to clean up anything that needs to be changed about the raw job data from the API
  modifyJobData(jobs) {
    let modified = jobs;
    modified = this.convertJobTimes(modified);
    modified = this.aggregateBatchJobs(modified);
    return modified;
  }

  convertJobTimes(jobs) {
    // list of keys with UNIX times attached
    const dateKeys = ['exec_end_time', 'exec_start_time', 'exp_start_time', 'submitted_time'];
    const durationKeys = ['pending_time', 'time_left'];
    const converted = jobs.map((job, index) => {
      for(var key in job) {
        if (dateKeys.indexOf(key) > -1) {
          // This key has a UNIX time associated with it, so we want to replace that with a
          // formatted time. Sometimes this field comes back as the beginning of UNIX time, which is
          // just zero, so we want to take care of that case too.
          const keyTime = job[key];
          if (keyTime === null || keyTime === 0) {
            job[key] = 'Not yet';
          } else {
            job[key] = moment.unix(keyTime).format('LTS l');
          }
        }
        if (durationKeys.indexOf(key) > -1) {
          // Convert this into a 'humanized' duration e.g. "A day," "11 hours" etc.
          let m = moment.duration(job[key], 'seconds');
          job[key] = Math.floor(m.asDays()).toString().concat('D ').concat(m.hours()).concat(':').concat(m.minutes()).concat(':').concat(m.seconds());
        }
      }
      return job
    });
    return converted;
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
      headers = [
          ['sched_jobid', 'Job ID'],
          ['name', 'Name'],
          ['user', 'User'],
          ['state', 'State'],
          ['elapsed_time', 'Elapsed Time'],
          ['time_left', 'Time Left']
      ];
    }
    else {
      headers = [
          ['sched_jobid', 'Job ID'],
          ['name', 'Name'],
          ['group', 'Group'],
          ['state', 'State'],
          ['elapsed_time', 'Elapsed Time'],
          ['time_left', 'Time Left']
      ];
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
          <text><h4>Jobs in Queue</h4></text>
          <JobTable data={unfinishedJobs} headers={headers} colorCoding={this.state.colorCoding}/>
        </div>
        <hr/>
        <div style={finJobCssDisplay}>
          <text><h4>Completed Jobs</h4></text>
          <JobTable data={finishedJobs} headers={headers} colorCoding={this.state.colorCoding}/>
        </div>
        <Button bsStyle={'link'} style={{float: 'right'}}
          onClick={this.toggleFinJobsDisplay.bind(this)}
        >{finJobButtonText}</Button>
      </div>
    );
  }  
}
