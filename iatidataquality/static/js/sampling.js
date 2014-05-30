$(".btn-yes").click(function(e){
    $(this).toggleClass("btn-default btn-success");
});
$(".btn-no").click(function(e){
    $(this).toggleClass("btn-default btn-danger");
});
$(".btn-unsure").click(function(e){
    $(this).toggleClass("btn-default btn-warning");
});
$(document).ready(function(){
	var samplingdata;

	$.getJSON("/api/sampling", function(data) { 
		console.log("got json response");
		samplingdata = data;

		console.log(data);

		first_sample = samplingdata[0];
		sample_iati_identifier = first_sample["iati-identifier"];
		$("#data-iati-identifier").html(sample_iati_identifier);
	});

});
