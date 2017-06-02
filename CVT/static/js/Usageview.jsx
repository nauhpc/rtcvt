/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
import {
  ProgressBar
} from 'react-bootstrap';

import React from 'react'
import Gauge from './Gauge.jsx'
require('../styles/cpb-style.css');

export default class Usageview extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      base:[],
      gres:[]
    }
  }

  apiCall(props){
    var url = '/api/getusage/';

    if (props.cluster!=='All'){
      url = url.concat('?cluster=').concat(props.cluster);

      $.ajax({
        url: '/api/getgres/'.concat(props.cluster).concat('/'),
        datatype: 'json',
        success: function(data){
          this.state.gres = data;
          this.forceUpdate();
        }.bind(this),
      });
    }
    $.ajax({
      url: url,
      datatype: 'json',
      success: function(data){
        this.state.base = data;
        this.forceUpdate();
      }.bind(this)
    });
  }

  componentDidMount(){
    this.apiCall(this.props);
    this.interval = setInterval(()=>{this.apiCall(this.props)}, 5000);
  }

  componentWillReceiveProps(nextProps){
    if (this.props.cluster!==nextProps.cluster){
      this.state.base = [];
      this.state.gres = [];
    }
    clearInterval(this.interval);
    this.apiCall(nextProps);
    this.interval = setInterval(()=>{this.apiCall(nextProps)}, 5000); 
  }

  componentWillUnmount() {
    clearInterval(this.interval);
  }

  render(){
    var usage = {
      mem_usage:0,
      core_usage:0,
      node_usage:0,
      jobs_total:0,
      jobs_running:0,
      jobs_pending:0,
    };

    for (var i=0;i<this.state.base.length;i++){
      usage.mem_usage += this.state.base[i].mem_usage*100;
      usage.core_usage += this.state.base[i].core_usage*100;
      usage.node_usage += this.state.base[i].node_usage*100;
      usage.jobs_total += this.state.base[i].jobs_total;
      usage.jobs_running += this.state.base[i].jobs_running;
      usage.jobs_pending += this.state.base[i].jobs_pending;
    }

    usage.mem_usage = Math.round(usage.mem_usage / this.state.base.length);
    usage.core_usage = Math.round(usage.core_usage / this.state.base.length);
    usage.node_usage = Math.round(usage.node_usage / this.state.base.length);

    var clusterGRES = this.state.gres.map((GRES)=>{
      return(
        <div style={styles.gaugeBox}>
          <Gauge name={GRES.gres.type} percentage={Math.round(GRES.usage*100)}/>
        </div>
      );
    });

    return(
      <div style={styles.container}>
        <div style={styles.jobSummary}>
          <div style={styles.testContainer}>
            <text style={{color:'#5cb85c'}}>Running Jobs</text>
            <ProgressBar style={{width:'100%'}} label={usage.jobs_running.toString()} active bsStyle="success" now={usage.jobs_running} max={usage.jobs_running}/>
          </div>
          <div style={styles.testContainer}>
            <text style={{color:'#f0ad4e'}}>Pending Jobs</text>
            <ProgressBar style={{width:'100%'}} label={usage.jobs_pending.toString()} bsStyle="warning" now={usage.jobs_pending} max={usage.jobs_pending}/>
          </div>
        </div>
        <div style={styles.clusterSummary}>
          <div style={styles.gaugeBox}>
            <Gauge name='Memory' percentage={usage.mem_usage}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Cores' percentage={usage.core_usage}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Nodes' percentage={usage.node_usage}/>
          </div>
          {clusterGRES}
        </div>
      </div>
    );
  }
}

const styles = {
  container:{
    display:'flex',
    flexDirection:'column',
    flex:1,
    alignItems:'center',
  },
  testContainer:{
    display:'flex',
    flexDirection:'row',
    flex:1,
    justifyContent:'space-around',
    width:'100%'
  },
  clusterSummary:{
    display:'flex',
    flexDirection:'row',
    flex:1,
    alignItems:'center',
    padding:'1em'
  },
  jobSummary:{
    display:'flex',
    flexDirection:'column',
    flex:1,
    alignItems:'center',
    justifyContent: 'space-around',
    minWidth:'33%'
  },
  jobBox:{
    flex:1,
    textAlign:'center',
    padding:'.5em'
  },
  gaugeBox:{
    display:'flex',
    flex:1,
    flexDirection:'column',
    textAlign:'center',
    alignItems:'center',
    padding:'.5em',
  }
}
