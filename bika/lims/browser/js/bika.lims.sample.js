/**
 * Controller class for Sample View
 */
function SampleView() {

    var that = this;

    that.load = function() {
        // Trap the save button
        # TODO Sample View js. Why we need to trap the save button?
        $("input[name='save']").click(save_header);
    }

    function save_header(event){
        event.preventDefault();
        requestdata = new Object();
        $.each($("form[name='header_form']").find("input,select"), function(i,v){
            name = $(v).attr('name');
            value =  $(v).attr('type') == 'checkbox' ? $(v).prop('checked') : $(v).val();
            requestdata[name] = value;
        });
        requeststring = $.param(requestdata);
        href = window.location.href.split("?")[0] + "?" + requeststring;
        window.location.href = href;
    }
}
