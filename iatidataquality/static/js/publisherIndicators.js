$(".showTests").click(function(e){
    if ($(this).hasClass("visible")) {
        e.preventDefault();

        re=new RegExp("showindicator-([0-9]*)");
        r=re.exec(this.id);
        indicator_id = r[1]

        $(this).closest("tr").removeClass("success");
        $(this).removeClass("visible").html('<i class="icon-chevron-down"></i>');
        $(".group-"+indicator_id).hide();
        $(".th_test").addClass('hidden');

    } else {
        e.preventDefault();

        re=new RegExp("showindicator-([0-9]*)");
        r=re.exec(this.id);
        indicator_id = r[1]
        $(this).closest("tr").addClass("success");
        $(this).addClass("visible").html('<i class="icon-chevron-up"></i>');
        $(".group-"+indicator_id).show().removeClass('hidden');
        $(".th_test").removeClass('hidden');
}
});
