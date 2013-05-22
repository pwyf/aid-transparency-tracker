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
        alert("Commitment indicators must have numerical scores. Please correct errors above.");
    }
});

function checkNumeric(n){
    return !isNaN(parseFloat(n)) && isFinite(n);
}
