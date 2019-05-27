/* http://meyerweb.com/eric/tools/css/reset/
   v2.0 | 20110126
   License: none (public domain)
*/

export default {
	// eslint-disable-next-line
  'html, body, div, span, applet, object, iframe, h1, h2, h3, h4, h5, h6, p, blockquote, pre, a, abbr, acronym, address, big, cite, code, del, dfn, em, img, ins, kbd, q, s, samp, small, strike, strong, sub, sup, tt, var, b, u, i, center, dl, dt, dd, ol, ul, li, fieldset, form, label, legend, table, caption, tbody, tfoot, thead, tr, th, td, article, aside, canvas, details, embed, figure, figcaption, footer, header, hgroup, main, menu, nav, output, ruby, section, summary, time, mark, audio, video': {
    margin: 0,
    padding: 0,
    border: 0,
    /* verticalAlign: 'baseline',*/
  },

  'article, aside, details, figcaption, figure, footer, header, hgroup, main, menu, nav, section': {
    display: 'block',
  },

  body: {
    lineHeight: 1,
    fontFamily: 'Roboto, sans-serif',
    backgroundColor: '#333',
  },

  'ol, ul': {
    listStyle: 'none',
  },

  'blockquote, q': {
    quotes: 'none',
  },

  'blockquote:before, blockquote:after, q:before, q:after': {
    content: 'none',
  },

  'a:hover, a:active': {
    outline: 'none',
  },

  table: {
    borderCollapse: 'collapse',
    borderSpacing: 0,
  },

  'input:invalid': {
    boxShadow: 'none',
  },

  footer: {
    padding: 20,
    lineHeight: 1.5,
  },

  '.datamaps-legend': {
    position: 'relative',
  },
};
