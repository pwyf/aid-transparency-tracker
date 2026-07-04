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
        indicator_id = r[1];

        $(this).closest("tr").removeClass("table-success");
        $(this).removeClass("visible").html('<i class="bi bi-chevron-down align-right"></i>');
        $(".group-"+indicator_id).hide();
        $(".th_test").addClass('d-none');

    } else {
        e.preventDefault();

        re=new RegExp("showindicator-([0-9]*)");
        r=re.exec(this.id);
        indicator_id = r[1];
        $(this).closest("tr").addClass("table-success");
        $(this).addClass("visible").html('<i class="bi bi-chevron-up align-right"></i>');
        $(".group-"+indicator_id).show().removeClass('d-none');
        $(".th_test").removeClass('d-none');
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
       var warning_text = "Do you want to switch to show all data? This may include data from several years ago. Please note that the Index will only consider current data.";
    } else {
       // changing to current data
       var warning_text = "Do you want to switch to show only current data? The Index will only consider current data - defined as projects that are currently in implementation, or ended less than 12 months ago, or with a transaction in the last 12 months.";
    }
    if (!$('#dataConfirmModal').length) {
$('body').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-dialog" role="document"><div class="modal-content"><div class="modal-header"><h3 id="dataConfirmLabel">Switch data source</h3><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-bs-dismiss="modal" aria-hidden="true">Cancel</button><a class="btn btn-primary" id="dataConfirmOK">OK</a></div></div></div></div>');
    }
    $('#dataConfirmModal').find('.modal-body').text(warning_text);
    $('#dataConfirmOK').addClass('confirmswitch');
    new bootstrap.Modal(document.getElementById('dataConfirmModal')).show();
    chosen_aggregation_type = $(this).val();
    $(this).val(previous_aggregation_type);
    return false;
});
$(document).on("click", ".confirmswitch", function(e){
    var _m = bootstrap.Modal.getInstance(document.getElementById('dataConfirmModal')); if (_m) { _m.hide(); }
    e.preventDefault();
    $('#aggregation_type').val(chosen_aggregation_type);
    $('#aggregation_type_form').submit();
});
