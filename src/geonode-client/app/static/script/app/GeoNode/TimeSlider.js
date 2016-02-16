Ext.namespace('GeoNode');

var time_periods = [
['5000M BCE', '*'],
['500M BCE', -500000000],
['50M BCE',- 50000000],
['5M BCE', -5000000],
['1M BCE', -1000000],
['100K BCE', -100000],
['10K BCE', -10000],
['1K BCE', -1000],
['500 BCE', -500],
['100 BCE', -100],
['1', 1],
['100', 100],
['500', 500],
['1000', 1000],
['1500', 1500],
['1600', 1600],
['1700', 1700],
['1800', 1800],
['1900', 1900],
['1910', 1910],
['1920', 1920],
['1930', 1930],
['1940', 1940],
['1950', 1950],
['1960', 1960],
['1970', 1970],
['1980', 1980],
['1990', 1990],
['1991', 1991],
['1992', 1992],
['1993', 1993],
['1994', 1994],
['1995', 1995],
['1996', 1996],
['1997', 1997],
['1998', 1998],
['1999', 1999],
['2000', 2000],
['2001', 2001],
['2002', 2002],
['2003', 2003],
['2004', 2004],
['2005', 2005],
['2006', 2006],
['2007', 2007],
['2008', 2008],
['2009', 2009],
['2010', 2010],
['2011', 2011],
['2012', 2012],
['2013', 2013],
['2014', 2014],
['2015', 2015],
['2016', 2016],
['2017', 2017],
['2018', 2018],
['2019', 2019],
['2020', 2020],
['2050', 2050],
['2100', 2100],
['Future' , '*']
];

GeoNode.TimeSlider = Ext.extend(Ext.slider.MultiSlider, {
    
    increment: 1,
    minValue: 0,
    maxValue: 60,
    values: [0, 60],

    getDateValues: function(){
      var dates = this.valuesToDates();
      var start = dates[0];
      var end = dates[1];
      if(start !== '*'){
        start = start + '-01-01T00:00:00.0Z';
      };
      if(end !== '*'){
        end = end + '-01-01T00:00:00.0Z';
      };
      return '[' + start + ' TO ' + end + ']';
    },

    valuesToTime: function(){
      var values = this.getValues();
      return [time_periods[values[0]][0], time_periods[values[1]][0]];
    },

    valuesToDates: function(){
      var values = this.getValues();
      return [time_periods[values[0]][1], time_periods[values[1]][1]];
    },

    cleanupInput: function(input){
      if(input.indexOf('BCE') > -1){
        var zeros = '';
        if(input.indexOf('M') > -1){
          zeros = '000000';
        }
        if(input.indexOf('K') > -1){
          zeros = '000';
        }
        input = '-' + input.replace(/\D+/, '') + zeros;
      }
      return input;
    },

    valuesFromInput: function(index, input){
      var value = parseInt(this.cleanupInput(input));
      for(var i=0;i<time_periods.length;i++){
        if(value>=time_periods[i][1] && value<=time_periods[i+1][1]){
          this.setValue(index, i+1);
          break
        }
      }
    }
});
