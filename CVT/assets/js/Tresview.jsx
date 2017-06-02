/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
import React from 'react';
import Gauge from './Gauge.jsx';
require('../styles/cpb-style.css');

export default class Tresview extends React.Component {
    constructor(props){
        super(props);
        this.state = {
            data:[]
        }
    }

    apiCall(props){
      let url = '/api/getugl/'.concat(props.cluster).concat('/').concat(props.group).concat('/'); 
      $.ajax({
        url: url,
        datatype: 'json',
        success: function(data){
          this.setState({data: data[0]});
        }.bind(this)
      });
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

  render(){
    if (!('group' in this.state.data)){
      return(
        <div></div>
      );
    }
    return(
      <div style={styles.container}>
        <div style={styles.gaugesContainer}>
          <text>Group: </text>
          <div style={styles.gaugeBox}>
            <Gauge name='Memory' percentage={Math.round((this.state.data.group.memory/this.state.data.group.total_memory)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='CPU Minutes' percentage={Math.round((this.state.data.group.cpu/this.state.data.group.total_cpu)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Node' percentage={Math.round((this.state.data.group.node/this.state.data.group.total_node)*100)}/>
          </div>
        </div>
        <div style={styles.gaugesContainer}>
          <text>Personal: </text>
          <div style={styles.gaugeBox}>
            <Gauge name='Memory' percentage={Math.round((this.state.data.memory/this.state.data.group.total_memory)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='CPU Minutes' percentage={Math.round((this.state.data.cpu/this.state.data.group.total_cpu)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Node' percentage={Math.round((this.state.data.node/this.state.data.group.total_node)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Energy' percentage={Math.round((this.state.data.energy/this.state.data.group.energy)*100)}/>
          </div>
          <div style={styles.gaugeBox}>
            <Gauge name='Fairshare' percentage={Math.round((this.state.data.fairshare/this.state.data.group.fairshare)*100)}/>
          </div>
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
    justifyContent:'space-around'
  },
  gaugesContainer:{
    display:'flex',
    flexDirection:'row',
    flex:1,
    alignItems:'center',
    justifyContent: 'space-around',
    padding:'1em',
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