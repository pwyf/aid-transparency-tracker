$(document).ready(function() {
    $('a[data-confirm]').click(function(ev) {
	    var href = $(this).attr('href');
	    if (!$('#dataConfirmModal').length) {
		    $('body').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-dialog" role="document"><div class="modal-content"><div class="modal-header"><h3 id="dataConfirmLabel">Please Confirm</h3><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-bs-dismiss="modal" aria-hidden="true">Cancel</button><a class="btn btn-primary" id="dataConfirmOK">OK</a></div></div></div></div>');
	    }
	    $('#dataConfirmModal').find('.modal-body').text($(this).attr('data-confirm'));
	    $('#dataConfirmOK').attr('href', href);
	    new bootstrap.Modal(document.querySelector('#dataConfirmModal')).show();
	    return false;
    });
});
