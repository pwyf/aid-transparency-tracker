var locationx = 17.65667;
var map;
var markers;
$(".btn-yes").click(function(e){
    $(this).toggleClass("btn-default btn-success");
});

$(".btn-no").click(function(e){
    $(this).toggleClass("btn-default btn-danger");
});

$(".btn-unsure").click(function(e){
    $(this).toggleClass("btn-default btn-warning");
});

var setupLocation = function(survey_data) {
    if (typeof(map)!='undefined') {
        map.remove();
    }
	locationx += 2;
	var geojsonMarkerOptions = {
	    radius: 8,
	    fillColor: "#ff7800",
	    color: "#000",
	    weight: 1,
	    opacity: 1,
	    fillOpacity: 0.8
	};
	
    
	var locations = survey_data['sample']['locations'];

	markers = new L.MarkerClusterGroup();
	for (var i in locations) {
		var feature = locations[i];
		var marker = new L.Marker(
			new L.LatLng(
				feature['latitude'],
				feature['longitude']
			    )
		);
		var popupContent = '<dl>Location: '+feature['name']+'</dl>';
		marker.bindPopup(popupContent);
		markers.addLayer(marker);
	}
	
	// OSM: http://{s}.tile.osm.org/{z}/{x}/{y}.png
	// MB: http://{s}.tiles.mapbox.com/v3/markbrough.map-qmxr8jb5/{z}/{x}/{y}.png
	// ARC: https://d.tiles.mapbox.com/v3/americanredcross.map-ms6tihx6/{z}/{x}/{y}.png
	
	layer_MapBox = new L.tileLayer(
	    'https://d.tiles.mapbox.com/v3/americanredcross.map-ms6tihx6/{z}/{x}/{y}.png',{
			maxZoom: 18, attribution: 'Map data <a href="http://mapbox.com">MapBox Streets</a>'
	    }
	)
    
    map = new L.Map('projectMap', {
        zoom: 5,
        maxZoom: 15
    });
	layer_MapBox.addTo(map);
    map.addLayer(markers);
    map.fitBounds(markers.getBounds());
	
    $("#location-xml").text(vkbeautify.xml($("#location-xml").text()));
};

var setupNewSurveyForm = function(survey_data) {

	if(survey_data["error"]) {
		if(survey_data["error"] == "Finished") {
			alert("Finished");
		} else {
			alert("Unknown error");
		}
		return;
	}

	var kind = survey_data['sample']['test_kind'];
	var template = $('#' + kind + '-template').html();
	Mustache.parse(template);   // optional, speeds up future uses
	
	var xmltmpl = $('#xml-template').html(),
	partials = {"xml-template": xmltmpl};
	
	var rendered = Mustache.render(template, survey_data['sample'], partials);
	$('#insert-here').html(rendered);

	header_data = survey_data['headers'];

	var header_template = $("#header-template").html();
	var rendered_header = Mustache.render(header_template, header_data);
	$('#header-insert').html(rendered_header);

	buttons_data = {'buttons': survey_data['buttons']};
	var buttons_template = $("#buttons-template").html();
	var rendered_buttons = Mustache.render(buttons_template, buttons_data);
	$('#buttons-insert').html(rendered_buttons);

	if (kind=='location') {
		setupLocation(survey_data);
	}
};

var getNewData = function() {
	$.getJSON(api_sampling_url, function(data) { 
        setupNewSurveyForm(data);
	});
};

$(document).ready(function(){
	getNewData();
});

$(document).on("click", ".advance", function(e) {
    e.preventDefault();

    var url = api_sampling_process_url + $(this).attr('value');
    $.post(url, $("form").serialize(), 
        function(returndata){
            if (update == true) {
                if (returndata == "NO SUCH UUID"){
                alert("That UUID could not be found");
                } else {
                window.location.assign(returndata);
                }
            } else {
                if (returndata == 'EXISTS'){
                    alert("That sample has already been submitted.");
                }
                getNewData();
            }
        }
    );
});

