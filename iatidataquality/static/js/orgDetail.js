
var url_root = "/"; // or "/publish"

function paginate_result(result_id, hierarchy_id, page) {
	var new_html = '<tr id="tr-pagination-' +  result_id  + '-hierarchy-' + hierarchy_id + '" ><td class="pagination_td" colspan="5"><div class="pagination"><ul><li><a class="' +
		(page-1) + '" href="#">Prev</a></li><li><a class="' + page + '" href="#">' + page + '</a></li><li><a class="' +
		(page + 1) + '" href="#">' +
		(page + 1) + '</a></li><li><a class="' +
		(page + 2) + '" href="#">' +
		(page + 2) + '</a></li><li><a class="' +
		(page + 3) + '" href="#">' +
		(page + 3) + '</a></li><li><a class="' +
		(page + 4) + '" href="#">' +
		(page + 4) + '</a></li><li><a class="' +
		(page + 1) + '" href="#">Next</a></li></ul></div><p>Note that this contains test results for historical as well as current data; and therefore may not necessarily agree with the total percentages shown above.</p></td></tr><tr id="tr-result-'  +  result_id  +  '"><td class="results" colspan="5"><span class="muted loading_data">Loading data... (this may take considerable time)</span></td></tr>';
	return new_html;
}

$(document).on('click', ".pagination a", function(e){
    e.preventDefault();
    re=new RegExp("tr\-pagination\-([0-9]*|[A-z]*)\-hierarchy\-([0-9]|[A-z]*)");
    r=re.exec($(this).closest('tr').attr('id'));

    result_id = r[1];
    hierarchy_id = r[2];
    $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    $("#tr"+result_id+"h"+hierarchy_id).next().slideUp('slow').delay(5000).remove();
    var page = parseInt($(this).attr('class'));
    var offset = ((page-1)*50)

	var html_addition = paginate_result(result_id, hierarchy_id, page);
    $("#tr" + result_id + "h" + hierarchy_id).after(html_addition);
	
    $('.loading_data').show();
    $.getJSON(url_root + "api/organisations/" +  organisation_code + "/hierarchy/" + hierarchy_id + "/tests/" + result_id + "/activities?offset="+offset, function(data){
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
		
        var offset = ((page-1)*50)
		
		var html_addition = paginate_result(result_id, hierarchy_id, page);

        $("#tr"+result_id+"h"+hierarchy_id).after(html_addition);

        $('.loading_data').show();
        $.getJSON(url_root + "api/organisations/" + organisation_code + "/hierarchy/" + hierarchy_id + "/tests/" + result_id + "/activities?offset="+offset, function(data){
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


var previous_aggregation_type;
var chosen_aggregation_type;
$('#aggregation_type').focus(function(){
    previous_aggregation_type = $(this).val();
}).change(function(){
    var agg_type = $('#aggregation_type_form select').val();
    if (agg_type == 1) {
        // changing to all data
        var warning_text = "Do you want to switch to show all data? This may include data from several years ago. Please note that the 2014 Index will only consider current data.";
    } else {
        // changing to current data
        var warning_text = "Do you want to switch to show only current data? The 2014 Index will only consider current data - defined as projects that are currently operational, or ended less than 13 months ago.";
    }
    if (!$('#dataConfirmModal').length) {
		$('body').append(
			'<div id="dataConfirmModal" class="modal" role="dialog" ' +
            '      aria-labelledby="dataConfirmLabel" aria-hidden="true">' +
            '   <div class="modal-header">' +
            '     <button type="button" class="close" data-dismiss="modal" ' +
            '             aria-hidden="true">×</button>' +
            '     <h3 id="dataConfirmLabel">Switch data source</h3>' +
            '   </div>' +
            '   <div class="modal-body"></div>' +
            '   <div class="modal-footer">' +
            '     <button class="btn" data-dismiss="modal" ' +
            '             aria-hidden="true">Cancel</button>' +
            '     <a class="btn btn-primary" id="dataConfirmOK">OK</a>' +
            '   </div>' +
            ' </div>');
    }
    $('#dataConfirmModal').find('.modal-body').text(warning_text);
    $('#dataConfirmOK').addClass('confirmswitch');
    $('#dataConfirmModal').modal({show:true});
    chosen_aggregation_type = $(this).val();
    $(this).val(previous_aggregation_type);
    return false;
});

$(document).on("click", ".confirmswitch", function(e){
    $("#dataConfirmModal").modal('hide');
    e.preventDefault();
    $('#aggregation_type').val(chosen_aggregation_type);
    $('#aggregation_type_form').submit();
});

