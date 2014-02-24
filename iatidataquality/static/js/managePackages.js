$("input").change(function(thischeckbox) {
    if ($(this).attr('checked')) {
        $(this).next().text("Active");
    }
    else {
        $(this).next().text("");
    }
});
$("#markall").click(function(e){
    e.preventDefault();
    $("input:checkbox").each(function(){
        $(this).prop('checked', true);
    });
});
$("#unmarkall").click(function(e){
    e.preventDefault();
    $("input:checkbox").each(function(){
        $(this).prop('checked', false);
    });
});
