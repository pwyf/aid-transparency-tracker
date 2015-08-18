
var url_root = "/"; // or "/publish"

var showAllTests;
$("#showAllTests").click(function(e){
    e.preventDefault();
    $(".condition-hidden").toggle();
    if (showAllTests == true) {
        showAllTests = false;
        $(this).text("Show all tests");
    } else {
        showAllTests = true;
        $(this).text("Show only relevant tests");
    }
});

var previous_aggregation_type;
var chosen_aggregation_type;
$('#aggregation_type').focus(function(){
    previous_aggregation_type = $(this).val();
}).change(function(){
    var agg_type = $('#aggregation_type_form select').val();
    if (agg_type == 1) {
        // changing to all data
        var warning_text = "Do you want to switch to show all data? This may include data from several years ago. Please note that the 2014 Index will only consider current data.";
    } else {
        // changing to current data
        var warning_text = "Do you want to switch to show only current data? The review will only consider current data - defined as projects that are currently operational, or ended less than 13 months ago.";
    }
    if (!$('#dataConfirmModal').length) {
		$('body').append(
			'<div id="dataConfirmModal" class="modal" role="dialog" ' +
            '      aria-labelledby="dataConfirmLabel" aria-hidden="true">' +
            '   <div class="modal-header">' +
            '     <button type="button" class="close" data-dismiss="modal" ' +
            '             aria-hidden="true">×</button>' +
            '     <h3 id="dataConfirmLabel">Switch data source</h3>' +
            '   </div>' +
            '   <div class="modal-body"></div>' +
            '   <div class="modal-footer">' +
            '     <button class="btn" data-dismiss="modal" ' +
            '             aria-hidden="true">Cancel</button>' +
            '     <a class="btn btn-primary" id="dataConfirmOK">OK</a>' +
            '   </div>' +
            ' </div>');
    }
    $('#dataConfirmModal').find('.modal-body').text(warning_text);
    $('#dataConfirmOK').addClass('confirmswitch');
    $('#dataConfirmModal').modal({show:true});
    chosen_aggregation_type = $(this).val();
    $(this).val(previous_aggregation_type);
    return false;
});

$(document).on("click", ".confirmswitch", function(e){
    $("#dataConfirmModal").modal('hide');
    e.preventDefault();
    $('#aggregation_type').val(chosen_aggregation_type);
    $('#aggregation_type_form').submit();
});

