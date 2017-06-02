/*jshint node:true, browser: true, devel: true, jquery: true, indent: 2, -W097, strict:true, esnext:true*/
'use strict';

import React from 'react';
import { BootstrapTable, TableHeaderColumn } from 'react-bootstrap-table';
require('../styles/table-style.css');

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
    if (row.id){
      for(var key in row){
        if (row.hasOwnProperty(key)){
          extras.push(
            <li>
              <b>{key}: </b>{row[key]}
            </li>
          );
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
    let pendingTime = parseInt(row.pending_time);
    let totalTime = elapsedTime+pendingTime;
    if (totalTime >= row.time_limit*0.75){
      return(
        <div style={{color:'red'}}>
          <p>{cell}</p>
        </div>
      ); 
    }
    else if (totalTime >= (row.time_limit*0.5)){
      return(
        <div style={{color:'#FFDF00'}}>
          <p>{cell}</p>
        </div>
      ); 
    }
    else{
      return(
        <div>
          <p>{cell}</p>
        </div>
      );
    }
  }

  render(){
    const options = {
      page: 1,  // which page you want to show as default
      sizePerPageList: [ {
        text: '10', value: 10
      }, {
        text: '50', value: 50
      }, {
        text: '100', value: 100
      }, {
        text: 'All', value: this.state.data.length
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
            dataFormat={this.elapsedTimeFormatter}
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

