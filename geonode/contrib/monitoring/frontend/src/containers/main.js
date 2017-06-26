import React from 'react';
import { Router, hashHistory } from 'react-router';
import { connect } from 'react-redux';
import MuiThemeProvider from 'material-ui/styles/MuiThemeProvider';
import { StyleRoot } from 'radium';
import routes from './app';


const mapStateToProps = (state) => ({
  theme: state.theme.theme,
});


function Main(props) {
  return (
    <StyleRoot>
      <MuiThemeProvider muiTheme={props.theme}>
        <Router history={hashHistory} routes={routes} />
      </MuiThemeProvider>
    </StyleRoot>
  );
}


Main.propTypes = {
  theme: React.PropTypes.object,
};


export default connect(mapStateToProps)(Main);
