var success = false;
jQuery().ready(function() { 

	// organisation_code is defined in the HTML template

    var url = ""; 
    jQuery.getJSON(url+"/plan/api/organisations/" + organisation_code + "?callback=?", null, function(org) { 
        success = true;
        if (org['scores']['group'] == 'Under consideration'){
            var approach_text = '<i class="icon icon-info-sign"></i> It looks like IATI publication is under consideration.';
            var elements_text = '<i class="icon icon-question-sign"></i> Please let us know if there is an updated schedule';
            var schedulequalifier = '';
        } else if (org['scores']['group'] == 'No publication') {
            var approach_text = '<i class="icon icon-info-sign"></i> It looks like you\'re not planning to publish to IATI.';
            var elements_text = '<i class="icon icon-question-sign"></i> Please let us know if there is an updated schedule';
            var schedulequalifier = '';
        } else {
            if (org['publisher']['publisher_code_actual'] != organisation_code) {
                var schedulequalifier = ' (for ' + org['publisher']['publisher_actual'] + ')';
            } else {
                var schedulequalifier = '';
            }
            var approach = org['scores']['approach'];
            if (approach==100){
                var approach_text = '<i class="icon icon-ok"></i> Good publication approach: planning to publish under an open licence and at least quarterly';
            } else if (approach==50) {
                var approach_text = '<i class="icon icon-minus"></i> Moderate publication approach: planning to publish either under an open licence or quarterly';
            } else if (approach==0) {
                var approach_text = '<i class="icon icon-remove"></i> Poor publication approach: neither planning to publish under an open licence nor quarterly';
            }
            var elements = org['scores']['elements'];
            if (elements>=60){
                var elements_text = '<i class="icon icon-ok"></i> Planning to publish '+elements+'% of fields';
            } else if (elements>=40) {
                var elements_text = '<i class="icon icon-minus"></i> Planning to publish '+elements+'% of fields';
            } else if (elements>=0) {
                var elements_text = '<i class="icon icon-remove"></i> Planning to publish '+elements+'% of fields';
            }
        }
        jQuery(".commitment .foundschedule").html('<i class="icon icon-ok"></i> Implementation schedule found' + schedulequalifier).removeClass('muted');
        jQuery(".commitment .approach").html(approach_text);
        jQuery(".commitment .elements").html(elements_text);
        jQuery(".commitment .review").html('<a class="btn btn-success" href="'+url+'/plan/organisations/' + organisation_code + '>Review Commitment »</a>');
    });
});

setTimeout(function() {
    if (!success)
    {
        // Handle error
        jQuery(".commitment .foundschedule").html('<i class="icon icon-remove"></i> No implementation schedule found');
        jQuery(".commitment .approach").html('');
        jQuery(".commitment .elements").html('');
        jQuery(".commitment .review").html('<a class="btn btn-warning" href="http://www.oecd.org/dac/aid-architecture/acommonstandard.htm" target="_blank">More on implementation schedules »</a>');
    }
}, 5000);
