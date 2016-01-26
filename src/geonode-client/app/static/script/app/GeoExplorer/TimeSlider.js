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

      this.plugins = new Ext.slider.Tip({
        getText: function(thumb){
            return self.getThumbRedableDate(thumb);
        }
      });

      GeoNode.TimeSlider.superclass.initComponent.call(this);
    },

    getDateValues: function(){
      if(this.thumbs[0].value != this.minValue || this.thumbs[1].value != this.maxValue){
        var start = this.getThumbDate(this.thumbs[0]).toISOString();
        var end = this.getThumbDate(this.thumbs[1]).toISOString();

        return '[' + start + ' TO ' + end + ']';
      }
      else{
        return null;
      }
    },

    getReadableDates: function(){
      return 'from ' + this.getThumbRedableDate(this.thumbs[0]) + ' to ' + this.getThumbRedableDate(this.thumbs[1])
    }
});
