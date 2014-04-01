$(document).on("click", "a[data-confirm]", function(ev) {
    var href = $(this).attr('href');
    if (!$('#dataConfirmModal').length) {
        $('body').append('<div id="dataConfirmModal" class="modal" role="dialog" aria-labelledby="dataConfirmLabel" aria-hidden="true"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">×</button><h3 id="dataConfirmLabel">Please Confirm</h3></div><div class="modal-body"></div><div class="modal-footer"><button class="btn" data-dismiss="modal" aria-hidden="true">Cancel</button><a class="btn btn-primary" id="dataConfirmOK">OK</a></div></div>');
    } 
    $('#dataConfirmModal').find('.modal-body').text($(this).attr('data-confirm'));
    $('#dataConfirmOK').attr('data-permission-id', $(this).attr('data-permission-id')).addClass('deletepermission');
    $('#dataConfirmModal').modal({show:true});
    return false;
});
$(document).on("click", ".deletepermission", function(e){
    $("#dataConfirmModal").modal('hide');
    e.preventDefault();
    var permissionid = $(this).attr('data-permission-id');

    delete_permissiondata = {
        'permisison_id': permissionid
    }
    $.post('deletepermission/', delete_permissiondata, function(resultdata) {
        if (resultdata['success']) {
            $("#permission"+permissionid).addClass('error').fadeOut();
        } else {
            alert("Couldn't delete that permission.");
        }
    });
});
$("#addpermissionbtn").click(function(e){
    e.preventDefault();
    var name = $("#name option:selected").val();
    var method = $("#method option:selected").val();
    var value = $("#value").val();
    permissiondata = {
        'permission_name': name,
        'permission_method': method,
        'permission_value': value
    }
    $.post('addpermission/', permissiondata, function(resultdata) {
        permission_id=resultdata.id;
        if (!(resultdata['error'])) {
            $("#permissions tbody").append('<tr id="permission' + permission_id + '"><td><input type="hidden" name="permission" value="' + permission_id + '" /><input type="hidden" name="name' + permission_id + '" value="' + name + '" />' + name + '</td><td><input type="hidden" name="method' + permission_id + '" value="' + method + '" />' + method + '</td><td>' + value + '</td><input type="hidden" name="value' + permission_id + '" value="' + value + '" /></td><td><a href="" data-confirm="Are you sure you want to delete this permission?" data-permission-id="' + permission_id + '"><i class="icon-trash"></i></td></tr>');
            $("#addPermission").modal('hide');
        } else {
            alert("Couldn't add that permission. Maybe you're not authorised, or maybe that permission already exists?");
        }
    });
});
