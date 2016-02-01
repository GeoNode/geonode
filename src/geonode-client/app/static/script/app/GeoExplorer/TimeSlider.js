Ext.namespace('GeoNode');

GeoNode.TimeSlider = Ext.extend(Ext.slider.MultiSlider, {
    
    increment: 1,
    minValue: 1980,
    maxValue: 2100,
    values: [1980, 2100],

    getReadableValues: function(){
      var values = this.getValues();

      return '[' + values[0] + ' TO ' + values[1] + ']';
    },

    getDateValues: function(){
      var start_date = new Date(this.thumbs[0].value, 0, 1);
      var end_date = new Date(this.thumbs[1].value, 11, 31);
      var start = start_date.toISOString();
      var end = end_date.toISOString();

      return '[' + start + ' TO ' + end + ']';
    },

});
