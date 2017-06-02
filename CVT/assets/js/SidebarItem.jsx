/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import { Link } from 'react-router';


export default class SidebarItem extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      minimized:true
    }

    this.onMouseEnter = this.onMouseEnter.bind(this);
    this.onMouseLeave = this.onMouseLeave.bind(this);
  }

  onMouseEnter(event){
    this.setState(prevState => ({
      minimized: false
    }));
  }

  onMouseLeave(event){
    this.setState(prevState => ({
      minimized: true
    })); 
  }

  // Instead of changing the Style on the same element
  // I think this would work better if the maxItem was another element
  // that rendered ontop of the minItem, that way position absolute would work nicely
  render() {
    if (this.state.minimized){
      return (
        <div style={Object.assign({}, styles.item, styles.minItem)} onMouseEnter={this.onMouseEnter} onMouseLeave={this.onMouseLeave}>
          <div style={{textAlign:'center'}}>
            <Link to={this.props.linkTo}>{this.props.shortName}</Link>
          </div>
        </div>
      )
    }
    else{
      return (
        <div style={Object.assign({}, styles.item, styles.maxItem)} onMouseEnter={this.onMouseEnter} onMouseLeave={this.onMouseLeave}>
          <div style={{textAlign:'center'}}>
            <Link style={{whiteSpace:'nowrap'}} to={this.props.linkTo}>{this.props.name}</Link>
          </div>
        </div>
      ) 
    }
  }
}

const styles = {
  item:{
    display:'flex',
    flex:1,
    minWidth:'32px',
    minHeight:'32px',
    maxHeight:'32px',
    alignItems:'center',
    justifyContent:'center',
  },
  minItem:{
    
  },
  maxItem:{
    position:'relative',
    left:'45%',
    backgroundColor:'lightblue'
  }
}
