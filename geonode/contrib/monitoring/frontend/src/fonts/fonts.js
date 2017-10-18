import RobotoWoff2 from './Roboto.woff2';
import RobotoWoff from './Roboto.woff';
import RobotoTtf from './Roboto.ttf';

export default {

  '@font-face': {
    fontFamily: 'Roboto',
    src: `url(${RobotoWoff2}) format("woff2"),
          url(${RobotoWoff}) format("woff"),
          url(${RobotoTtf}) format("truetype")`,
    fontWeight: 'normal',
    fontStyle: 'normal',
  },

};
