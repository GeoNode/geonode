/**
 * 
 */

function ConvertLonToAlbersEqArea(dLon) 
{

    //compute LON
    //Earth radius = 5,269,308.57789304
    //pi = 3.1415
    //cos(38)/180 = 0.00530596468915164
    //Earth Radius * pi = 16553532.89745098516 * cos(38)/180 = 87832.461034585
    return roundNumber(87832.461034585 * (dLon + 100), 2);
};

function ConvertLatToAlbersEqArea(dLat)
{
    //compute LAT
    var e = 0.0818191955335;    //eccentricity
    var es = .00669438075774911;  //e^2
    var one_es = 0.993305619242251; //1-es
    var k0 = .0000001237057815;       //general scaling factor 
    var pi = 3.14159265358979;      //our old friend
    
    var dRadsLat = (pi * dLat) / 180;  //angle in radians
    var dSinLat = Math.sin(dRadsLat);     //sin(lat in radians)
    var dCon = e * dSinLat; 
    return roundNumber(0.5 * (one_es * (dSinLat / (1 - dCon * dCon) - (0.5 / e) * Math.log((1 - dCon) / (1 + dCon)))) / k0, 2);
};


//  roundNumber function from:  http://www.mediacollege.com/internet/javascript/number/round.html
function roundNumber(rnum, rlength) 
{
  if (rnum > 8191 && rnum < 10485) 
  {
    rnum = rnum-5000;
    var newnumber = Math.round(rnum*Math.pow(10,
rlength))/Math.pow(10,rlength);
    return newnumber+5000;
  } 
  else 
    return Math.round(rnum*Math.pow(10,rlength))/Math.pow(10,rlength);
};