/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
require('../styles/table-style.css');
var moment = require('moment');

export default class JobTable extends React.Component {
  constructor(props){
    super(props);
    this.state = {
      data:this.props.data,
      headers:this.props.headers
    };
  }

  componentWillReceiveProps(nextProps) {
    this.setState({data:nextProps.data, headers:nextProps.headers});
  }

  isExpandableRow(row){
    return true;
  }

  expandComponent(row){
    var extras = [];
    if (row.sched_jobid){
      for(var key in row){
        if (row.hasOwnProperty(key)){
          if (key=='elapsed_time' || key=='time_limit'){
            let m = moment.duration(row[key], 'seconds');
            let formattedCell = Math.floor(m.asDays()).toString().concat('D ').concat(m.hours()).concat(':').concat(m.minutes()).concat(':').concat(m.seconds());
            extras.push(
              <li>
                <b>{key}: </b>{formattedCell}
              </li>
            );
          }
          else{
            extras.push(
              <li>
                <b>{key}: </b>{row[key]}
              </li>
            );
          }
        }
      }

      return(
        <ul>
          {extras}
        </ul>
      );
    }
    else {
      return(
        <JobTable data={row.data} headers={this.state.headers}/>
      );
    }
  }

  elapsedTimeFormatter(cell, row){
    let elapsedTime = parseInt(row.elapsed_time);
    let timelimit = parseInt(row.time_limit);

    let m = moment.duration(cell, 'seconds');
    let formattedCell = Math.floor(m.asDays()).toString().concat('D ').concat(m.hours()).concat(':').concat(m.minutes()).concat(':').concat(m.seconds());
    let color = 'black';

    for(var c of this.props.colorCoding){
      if (timelimit > 0 && elapsedTime >= (timelimit*c[0])){
        color = c[1];
      }
      else {break;}
    }

    return (
      <div style={{color:color}}>
        <p>{formattedCell}</p>
      </div>
    );
  }

  timeLimitFormatter(cell, row){
    let m = moment.duration(cell, 'seconds');
    let formattedCell = Math.floor(m.asDays()).toString().concat('D ').concat(m.hours()).concat(':').concat(m.minutes()).concat(':').concat(m.seconds());
    return formattedCell;
  }

  render(){
    console.log("JobTable: ");
    console.log(this.state.data);
    const options = {
      page: 1,  // which page you want to show as default
      sizePerPageList: [ {
        text: '10', value: 10
      }, {
        text: '50', value: 50
      }, {
        text: '100', value: 100
      }, {
        text: 'All', value: (this.state.data === undefined ? 0 : this.state.data.length)
      } ], // you can change the dropdown list for size per page
      sizePerPage: 10,  // which size per page you want to locate as default
      pageStartIndex: 1, // where to start counting the pages
      paginationSize: 2,  // the pagination bar size.
      prePage: 'Prev', // Previous page button text
      nextPage: 'Next', // Next page button text
      firstPage: 'First', // First page button text
      lastPage: 'Last', // Last page button text
      paginationShowsTotal: true,  // Accept bool or function
    };

    let tableheaders = this.state.headers.map((header, k)=>{
      if(header[0]==='elapsed_time'){
        return(
          <TableHeaderColumn
            key={k}
            dataSort={true}
            dataFormat={this.elapsedTimeFormatter.bind(this)}
            dataField={header[0]}>
              {header[1]}
          </TableHeaderColumn>);
        }
        else if(header[0]==='time_limit'){
          return(
            <TableHeaderColumn
              key={k}
              dataSort={true}
              dataFormat={this.timeLimitFormatter.bind(this)}
              dataField={header[0]}>
                {header[1]}
            </TableHeaderColumn>); 
        }
        else{
          return(
            <TableHeaderColumn
              key={k}
              dataSort={true}
              dataField={header[0]}>
                {header[1]}
            </TableHeaderColumn>);
        }
    });
    return(
      <BootstrapTable data={this.state.data}
        expandableRow={this.isExpandableRow}
        expandComponent={this.expandComponent.bind(this)}
        keyField='sched_jobid'
        pagination
        options={options}
        search
        hover>
        {tableheaders}
      </BootstrapTable>
    );
  }
}

