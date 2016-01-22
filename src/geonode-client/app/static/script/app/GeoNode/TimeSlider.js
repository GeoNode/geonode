Ext.namespace('GeoExplorer');

GeoExplorer.TimeSlider = Ext.extend(Ext.slider.MultiSlider, {

    startDate: new Date(2010, 01, 01),
    endDate: new Date(),
    
    increment: 1,

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
            return self.getThumbDate(thumb);
        }
      });

      GeoExplorer.TimeSlider.superclass.initComponent.call(this);
    },

    getDateValues: function(){
      var values = this.getValues();
      return values;
    }
});
