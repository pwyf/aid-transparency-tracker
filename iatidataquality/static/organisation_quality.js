jQuery(function($){
    // hack
    if($("#organisation_quality").length == 0){
        return;
    }
    var show_organisation_quality = function(report){
        var data = {children : report}; // is "children" needed?
        var h = 700, w = 1000
        format = d3.format(",d"),
        fill = d3.scale.category20c();

        var bubble = d3.layout.pack()
            .sort(null)
            .size([w, h])
            .value(function(c){return c.total;})
            .padding(20);


        var vis = d3.select("#chart").append("svg")
            .attr("width", w)
            .attr("height", h)
            .attr("class", "bubble");

        var title = vis.append("text")
            .attr("class", "title")
            .attr("dy", ".71em")
            .attr("transform", "translate(10, 10)")
            .text("Organisational data quality");

         var node = vis.selectAll("g.node")
            .data(bubble.nodes(data))
            .enter().append("g")
            .filter(function(d) { return !d.children;})
            .attr("class", "node")
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });

            node.append("circle")
                 .attr("r", 0)
                 .transition().duration(1250)
                 .attr("r", function(d) { return d.r; })
                 .style("fill", function(d) { return fill(d.package_name); });

        node.append("circle")
            .attr("class", "inner")
            .attr("r", 0)
            .transition().duration(2500)
            .attr("r", function(d) {  return d.r * (d.passed/d.total); })
            .style("fill", function(d) { return fill(d.package_name); });

        node.append("text")
            .style("opacity", 0.0)
            .transition().duration(1000).style("opacity", 0.9)
            .attr("text-anchor", "right")
            .attr("dy", ".3em")
            .text(function(d) { return d.package_name.substring(0, d.r / 3); });
    };
    jQuery.getJSON(window.endpoint_url +"?&callback=?", function(data){

        show_organisation_quality(data.results_by_org);
    });
});
