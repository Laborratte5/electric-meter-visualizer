function init() {
    var lineData = {
        "type":"line",
        "data":{
            "labels": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
            "datasets": [{
                "label":"electric meter #1",
                "data":[13,12,6,3,15,3,8,9,4,67,2,12],
                "backgroundColor":"rgba(255,200,200,0.3)",
                "borderColor":"#F00",
                "lineTension": 0.1
            },
            {
                "label":"electric meter #1 last year",
                "data":[7,12,7,54,32,8,21,1,4,9,23,1],
                "backgroundColor":"rgba(200,255,200, 0.3)",
                "borderColor":"#0F0",
                "lineTension": 0.1
            }]
        },
        "options":{
            "onClick": function(c,i) {
                e = i[0];
                if (e != null) {
                    console.log(e._index)
                    var x_value = this.data.labels[e._index];
                    var y_value = this.data.datasets[0].data[e._index];
                    console.log(x_value);
                    console.log(y_value);
                }
            }
        }
    }

    var ctx = document.getElementById("line").getContext("2d");
    var myChart = new Chart(ctx, lineData);

}