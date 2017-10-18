import { createAction } from 'redux-actions';
import { THEME } from './constants';


const changeTheme = createAction(THEME, theme => theme);


const actions = { changeTheme };


export default actions;
