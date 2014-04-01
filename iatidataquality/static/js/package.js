$(".showResult").click(function(e){
    if ($(this).hasClass("visible")) {
        e.preventDefault();


        re=new RegExp("result([0-9]*)hierarchy([0-9]|[A-z]*)");
        r=re.exec(this.id);

        result_id = r[1]
        hierarchy_id=r[2]

        $(this).removeClass("visible").html('<i class="icon-chevron-down"></i>');
        $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    } else {
        e.preventDefault();

        re=new RegExp("result([0-9]*)hierarchy([0-9]|[A-z]*)");
        r=re.exec(this.id);

        result_id = r[1]
        hierarchy_id=r[2]
        $("#tr"+result_id+"h"+hierarchy_id).after('<tr class="hidden-results-tr" id="tr-result-' + result_id + '"><td colspan="5"></td></tr>');
        $.getJSON("/publish/api/packages/"+package_name+"/hierarchy/" + hierarchy_id + "/tests/" + result_id + "/activities", function(data){
            var items = [];
            $.each(data, function(key, val){
                if (val == '1') {
                    var status="PASS";
                    var statusclass="success";
                } else {
                    var status="FAIL";
                    var statusclass="error";
                }
                items.push('<tr id="' + val + '" class="' + statusclass + '"><td><a href="http://beta.openaidsearch.org/explore-detail/?id=' + key + '">'+key+'</a></td><td>' + status + '</td></tr>');
            });
            $('<table/>', {
                html: items.join('')
              }).appendTo("#tr-result-"+result_id+" td");
            $("#tr-result-"+result_id).slideDown("slow");
        });
        $(this).addClass("visible").html('<i class="icon-chevron-up"></i>');
}
});
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

$('#aggregation_type').change(function(){
    $('#aggregation_type_form').submit();
});
