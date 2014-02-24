$(document).on("click", ".deletefeedback", function(e){
    e.preventDefault();
    var feedbackid = $(this).attr('data-feedback-id');
    $("#feedback"+feedbackid).remove();
});
var countfeedback = 0;
$("#addfeedbackbtn").click(function(){
    countfeedback ++;
    var uses = $("#uses option:selected").val();
    var element = $("#element option:selected").val();
    var where = $("#where option:selected").val();
    $("#conditions tbody").append('<tr id="feedback' + countfeedback + '"><td>'+organisation_code+' ' + $("#uses option:selected").val() + ' ' + $("#element option:selected").val() + ' at ' + $("#where option:selected").val() + '<input type="hidden" name="feedback" value="' + countfeedback + '" /><input type="hidden" name="uses' + countfeedback + '" value="' + uses + '" /><input type="hidden" name="element' + countfeedback + '" value="' + element + '" /><input type="hidden" name="where' + countfeedback + '" value="' + where + '" /></td><td><a href="" class="deletefeedback" data-feedback-id="' + countfeedback + '"><i class="icon-trash"></i></td></tr>');
    $("#addFeedback").modal('hide');
});
