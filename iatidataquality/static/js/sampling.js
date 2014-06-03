
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
	var template = $('#template').html();
	Mustache.parse(template);   // optional, speeds up future uses
	var rendered = Mustache.render(template, work_item);
	$('#insert-here').html(rendered);

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
    $.post("/api/sampling/process/", $('form').serialize(), 
		   function(returndata){
			   getNewData();
		   });
});

