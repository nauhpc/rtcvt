/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
import React from 'react'
import Gauge from './Gauge.jsx'
require('../styles/cpb-style.css');

export default class Gresview extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      data:[]
    }
  }

  apiCall(props){
    let url = '/api/getgres/'.concat(props.cluster).concat('/?group=').concat(props.group)
    $.ajax({
      url: url,
      datatype: 'json',
      success: function(data){
        this.setState({data: data});
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
    var spGRES = this.state.data.map((GRES)=>{
      return(
        <div style={styles.gaugeBox}>
          <Gauge name={GRES.gres.type} percentage={Math.round(GRES.usage*100)}/>
        </div>
      );
    });
    if(this.state.data.length > 0) {
      return(
        <div style={styles.gaugesContainer}>
          {spGRES}
        </div>
      );
    } else {
      return(
        <div>
          <p>Nothing to display</p>
        </div>
      );
    }
  }
}

const styles = {
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
