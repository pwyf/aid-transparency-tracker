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
        $('#dataConfirmModal').modal('hide');
        if (!$('#commitmentWarning').length) {
            $('body').append('<div id="commitmentWarning" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button><h3 id="dataConfirmLabel">Errors in your survey input</h3></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-dismiss="modal" aria-hidden="true">OK</button></div></div>');
        }
        warning_text = "Commitment indicators must have numerical scores. Please correct errors above.";
        $('#commitmentWarning').find('.modal-body').text(warning_text);
        $('#commitmentWarning').modal({show:true});
    }
});

function checkNumeric(n){
    return !isNaN(parseFloat(n)) && isFinite(n);
}
$("#submit").click(function(e){
    e.preventDefault();
    if (!$('#dataConfirmModal').length) {
        $('form').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button><h3 id="dataConfirmLabel">Confirm submit survey</h3></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button><input type="submit" name="submit" class="btn btn-success" id="dataConfirmOK" value="Submit data" /></div></div>');
    }
    warning_text = "Are you sure you want to submit this survey? You cannot make any changes once you have submitted.";
    $('#dataConfirmModal').find('.modal-body').text(warning_text);
    $('#dataConfirmModal').modal({show:true});
});
