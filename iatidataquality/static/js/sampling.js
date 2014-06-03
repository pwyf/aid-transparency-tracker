
$(".btn-yes").click(function(e){
    $(this).toggleClass("btn-default btn-success");
});

$(".btn-no").click(function(e){
    $(this).toggleClass("btn-default btn-danger");
});

$(".btn-unsure").click(function(e){
    $(this).toggleClass("btn-default btn-warning");
});

var setupNewSurveyForm = function(work_item) {
	var sample_iati_identifier = work_item["iati-identifier"];
	var elt = $("#data-iati-identifier");
    elt.html(sample_iati_identifier);
    $("#sampling-container")[0].data = work_item;
};

var getNewData = function() {
	$.getJSON("/api/sampling", function(data) { 
        setupNewSurveyForm(data);
	});
};

$(document).ready(function(){
	getNewData();
});

$(".advance").click(function(e) {
    var data = $("#sampling-container")[0].data;
    $.post("/api/sampling/process/", data, function(returndata){
		getNewData();
    });
});

