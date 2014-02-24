$(document).on('click', ".pagination a", function(e){
    e.preventDefault();
    re=new RegExp("tr\-pagination\-([0-9]*|[A-z]*)\-hierarchy\-([0-9]|[A-z]*)");
    r=re.exec($(this).closest('tr').attr('id'));

    result_id = r[1];
    hierarchy_id = r[2];
    $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    page = parseInt($(this).attr('class'));
    offset = ((page-1)*50)

    $("#tr"+result_id+"h"+hierarchy_id).after('<tr id="tr-pagination-'+ result_id +'-hierarchy-'+hierarchy_id+'" ><td class="pagination_td" colspan="5"><div class="pagination"><ul><li><a class="'+(page-1)+'" href="#">Prev</a></li><li><a class="'+page+'" href="#">'+page+'</a></li><li><a class="'+(page+1)+'" href="#">'+(page+1)+'</a></li><li><a class="'+(page+2)+'" href="#">'+(page+2)+'</a></li><li><a class="'+(page+3)+'" href="#">'+(page+3)+'</a></li><li><a class="'+(page+4)+'" href="#">'+(page+4)+'</a></li><li><a class="'+(page+1)+'" href="#">Next</a></li></ul></div></td></tr><tr id="tr-result-' + result_id + '"><td class="results" colspan="5"><span class="muted loading_data">Loading data...</span></td></tr>');

    $('.loading_data').show();
    $.getJSON("/publish/api/publishers/{{p_group.name}}/hierarchy/" + hierarchy_id + "/tests/" + result_id + "/activities?offset="+offset, function(data){
        var items = [];
        $.each(data["results"], function(key, val){
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
          }).appendTo("#tr-result-"+result_id+" td.results");
        $("#tr-result-"+result_id).slideDown("slow");
        $('.loading_data').hide();
    });

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
var page = 1;
$(".showResult").click(function(e){
    if ($(this).hasClass("visible")) {
        e.preventDefault();

        re=new RegExp("result([0-9]*)hierarchy([0-9]|[A-z]*)");
        r=re.exec(this.id);

        result_id = r[1]
        hierarchy_id=r[2]

        $(this).removeClass("visible").html('<i class="icon-chevron-down"></i>');
        $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
        $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    } else {
        e.preventDefault();

        re=new RegExp("result([0-9]*)hierarchy([0-9]|[A-z]*)");
        r=re.exec(this.id);
        result_id = r[1]
        hierarchy_id=r[2]

        offset = ((page-1)*50)

        $("#tr"+result_id+"h"+hierarchy_id).after('<tr id="tr-pagination-'+ result_id +'-hierarchy-'+hierarchy_id+'" ><td class="pagination_td" colspan="5"><div class="pagination"><ul><li><a class="'+(page-1)+'" href="#">Prev</a></li><li><a class="'+page+'" href="#">'+page+'</a></li><li><a class="'+(page+1)+'" href="#">'+(page+1)+'</a></li><li><a class="'+(page+2)+'" href="#">'+(page+2)+'</a></li><li><a class="'+(page+3)+'" href="#">'+(page+3)+'</a></li><li><a class="'+(page+4)+'" href="#">'+(page+4)+'</a></li><li><a class="'+(page+1)+'" href="#">Next</a></li></ul></div></td></tr><tr id="tr-result-' + result_id + '"><td class="results" colspan="5"><span class="muted loading_data">Loading data...</span></td></tr>');
        $('.loading_data').show();
        $.getJSON("/publish/api/publishers/{{p_group.name}}/hierarchy/" + hierarchy_id + "/tests/" + result_id + "/activities?offset="+offset, function(data){
            var items = [];
            $.each(data["results"], function(key, val){
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
              }).appendTo("#tr-result-"+result_id+" td.results");
            $("#tr-result-"+result_id).slideDown("slow");
            $('.loading_data').hide();
        });
        $(this).addClass("visible").html('<i class="icon-chevron-up"></i>');
}
});
