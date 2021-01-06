function ADDON_createPercHeatmap(jsonstr, year){
    //jsonstr: string, year: number

    var dt = JSON.parse(jsonstr);
    if(year in dt){
        dt = dt[year];
    }else{
        dt = {}
    }
    var daysInYear = 365;
    if(moment([year]).isLeapYear()){
        daysInYear = 366;
    }
    var chartData = new Array(daysInYear);
    for(var month = 0; month < 12; month++){
        end = moment([year, month]).daysInMonth()
        for(var date = 1; date <= end; date++){
            dateObj = moment();
            dateObj.year(Number(year));
            dateObj.month(Number(month));
            dateObj.date(Number(date));
            var idx = dateObj.dayOfYear() - 1; //1 based to 0 based
            var value = -1;
            if(month in dt){
                if(date in dt[month]){
                    value = dt[month][date]; //number
                }
            }
            chartData[idx] = {"date": dateObj, "count": Math.round(value * 100)};
        }
    }


    var colors = window.ADDON_perccolors
    console.log(colors)
    var colorFunc = function(cnt){
        if(cnt > 99){
            return colors[5];
        }else if(cnt >= 75){
            return colors[4];
        }else if(cnt >= 50){
            return colors[3];
        }else if(cnt >= 25){
            return colors[2]
        }else if(cnt >= 0){
            return colors[1];
        }else{
            return colors[0];
        }
    };


    var chart1 = calendarHeatmap()
              .data(chartData)
              .selector("#percHeatmap")
              .max(100)
              .color(colorFunc)
              .startDate(moment([year, 0, 1]).toDate())
              .legendEnabled(true)
              .tooltipUnit(
                [
                  {min: -100, max: -1, unit:'No Data'},
                  {min: 0, max: 100, unit: '%n %'}
                ]
              );
    chart1();   
    
}

ADDON_createPercHeatmap(window.ADDON_percjsonstr, window.ADDON_percyear)
