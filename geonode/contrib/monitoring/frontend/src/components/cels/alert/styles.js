export default {
  content: {
    width: '100%',
    padding: 10,
    marginTop: 10,
  },

  date: {
    fontWeight: 'bold',
    marginBottom: 5,
  },

  short: {
    color: '#ffa031',
    marginBottom: 5,
  },

  hiddenDetail: {
    maxHeight: 0,
    overflow: 'hidden',
    transition: 'max-height 0.5s ease-out',
  },

  shownDetail: {
    maxHeight: 50,
    overflow: 'hidden',
    transition: 'max-height 0.5s ease-in',
  },
};
