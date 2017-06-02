import React from 'react';
import CircularProgressbar from 'react-circular-progressbar';
require('../styles/cpb-style.css');

export default class Gauge extends React.Component {
  constructor(props){
    super(props);
  }

  render(){
    return(
      <div style={styles.guage}>
        <p>{(this.props.name) ? this.props.name : ''}</p>
        <CircularProgressbar percentage={this.props.percentage}/>
      </div>
    );
  }
}
const styles = {
  guage:{
    maxWidth:'100px'
  }
}