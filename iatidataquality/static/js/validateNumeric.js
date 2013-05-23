$("form").submit(function(e){
    var errors=false;
    $('.commitment-indicator').each(function(indicator){
        var commitmentval = $('#'+$(this).attr('id') + ' .commitment-indicator-value').val();
        if (!checkNumeric(commitmentval)){
            errors = true;
            $('#'+$(this).attr('id') + " .control-group").addClass('error');
        } else {
            $('#'+$(this).attr('id') + " .control-group").removeClass('error');
        }
    });
    if (errors) {
        e.preventDefault();
        if (!$('#dataConfirmModal').length) {
            $('body').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button><h3 id="dataConfirmLabel">Errors in your survey input</h3></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-dismiss="modal" aria-hidden="true">OK</button></div></div>');
        }
        warning_text = "Commitment indicators must have numerical scores. Please correct errors above.";
        $('#dataConfirmModal').find('.modal-body').text(warning_text);
        $('#dataConfirmModal').modal({show:true});
    }
});

function checkNumeric(n){
    return !isNaN(parseFloat(n)) && isFinite(n);
}
