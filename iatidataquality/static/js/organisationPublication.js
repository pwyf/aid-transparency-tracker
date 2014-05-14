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
$(".showTests").click(function(e){
    if ($(this).hasClass("visible")) {
        e.preventDefault();

        re=new RegExp("showindicator-([0-9]*)");
        r=re.exec(this.id);
        indicator_id = r[1]

        $(this).closest("tr").removeClass("success");
        $(this).removeClass("visible").html('<i class="icon-chevron-down align-right"></i>');
        $(".group-"+indicator_id).hide();
        $(".th_test").addClass('hidden');

    } else {
        e.preventDefault();

        re=new RegExp("showindicator-([0-9]*)");
        r=re.exec(this.id);
        indicator_id = r[1]
        $(this).closest("tr").addClass("success");
        $(this).addClass("visible").html('<i class="icon-chevron-up align-right"></i>');
        $(".group-"+indicator_id).show().removeClass('hidden');
        $(".th_test").removeClass('hidden');
}
});

$(".scrollto").click(function(e){
    e.preventDefault();
    scrollto = $(this).attr('href');
    $("html, body").animate(
            {scrollTop: $(scrollto).offset().top},'slow'
    );
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
       var warning_text = "Do you want to switch to show only current data? The 2014 Index will only consider current data - defined as projects that are currently operational, or ended less than 13 months ago.";
    }
    if (!$('#dataConfirmModal').length) {
$('body').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button><h3 id="dataConfirmLabel">Switch data source</h3></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button><a class="btn btn-primary" id="dataConfirmOK">OK</a></div></div>');
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
