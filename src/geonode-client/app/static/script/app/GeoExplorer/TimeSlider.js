Ext.namespace('GeoNode');

GeoNode.TimeSlider = Ext.extend(Ext.slider.MultiSlider, {

    startDate: new Date(2010, 01, 01),
    endDate: new Date(),
    
    increment: 1,

    getThumbRedableDate: function(thumb){
      return this.getThumbDate(thumb).toDateString();
    },

    getThumbDate: function(thumb){
      var val = thumb.value;
      var date = new Date()
      date.setTime( this.startDate.getTime() + val * 86400000 );
      return date;
    },

    initComponent: function(){
      var self = this;

      this.minValue = 0;

      this.maxValue = Math.round((this.endDate-this.startDate)/3600/24/1000); //from milliseconds,

      this.values = [0, this.maxValue];

      GeoNode.TimeSlider.superclass.initComponent.call(this);
    },

    getDateValues: function(){
      var start = this.getThumbDate(this.thumbs[0]).toISOString();
      var end = this.getThumbDate(this.thumbs[1]).toISOString();

      return '[' + start + ' TO ' + end + ']';
    },

    getReadableDates: function(){
      return  [this.getThumbRedableDate(this.thumbs[0]), this.getThumbRedableDate(this.thumbs[1])];
    },

    getValueFromDate: function(date){
      var date = new Date(date);
      return Math.round((date - this.startDate) / 3600 /24 / 1000);
    }
});
