import React from 'react';
import {Navbar, Nav, NavItem} from 'react-bootstrap';
import {Link} from 'react-router';
import UserComp from './UserComp.jsx';

export default class Topbar extends React.Component {
    constructor(props){
    super(props);
    this.state = {data:[]};
  }

  apiCall(){
    $.ajax({
      url: '/api/clusters',
      datatype: 'json',
      success: function(data){
        this.setState({data: data});
      }.bind(this)
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
        if (this.state.data) {
          var clusterItems = this.state.data.map(
            (cluster, k) => {
                return(
                    <NavItem key={k} eventKey={cluster.name} href={'/#/cluster/'.concat(cluster.name)}>
                        {cluster.name}
                    </NavItem>
                );
            }
          );
        }
        return(
            <Navbar fixedTop>
                <Navbar.Header>
                    <Navbar.Brand>
                        <text>CVT</text>
                    </Navbar.Brand>
                    <Navbar.Toggle/>
                </Navbar.Header>
                <Navbar.Collapse>
                    <Nav>
                      {clusterItems}
                      <NavItem eventKey='All' href={'/#/'}>
                        All
                      </NavItem>
                    </Nav>
                    <UserComp/>
                </Navbar.Collapse>
            </Navbar>
        );
    }
}

const styles = {
  bannerImage:{
    maxHeight: '50px',
    marginTop: '-15px'
  }
}
