
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
	console.log(work_item);
	var kind = work_item['test_kind'];
	var template = $('#' + kind + '-template').html();
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
    e.preventDefault();

    var url = "/api/sampling/process/" + $(this).attr('value');

    $.post(url, $("form").serialize(), 
		   function(returndata){
			   getNewData();
		   });
    
});

