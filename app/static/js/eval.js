optionsSelected = $('.eval-batch-select option:selected');
allRadios = $(':radio');
// var activate_modal_button;
$(document).ready(function () {
    $('.modal-btn-eval').each(function (index, item) {
        $object = $("#news_for_" + $(item).attr("id"));
        $object.toggle();
        if ($object.is(":visible")){
            $(item).text("Esconder texto")
        }else {
            $(item).text("Exibir texto")
        }
    });

    function flaskTextToHTML (index, item) {
        $(item).html($(item).text());
    }
    $('.flask-text h4').each(function (index, item) {
        flaskTextToHTML(index, item)
    });
    $('.flask-text h5').each(function (index, item) {
        flaskTextToHTML(index, item)
    });
    $('.flask-text p').each(function (index, item) {
        flaskTextToHTML(index, item)
    });
});
$('.modal-btn-eval').each(function (index, item) {
    $(item).click(function(){
        $object = $("#news_for_" + $(item).attr("id"));
        $object.toggle();
        if ($object.is(":visible")){
            $(item).text("Esconder texto")
        }else {
            $(item).text("Exibir texto")
        }
    });
});

$(document).ready(function () {
    allRadios.each(function (index, item) {
        $(item).prop('checked', false);
    })
});

$("[data-toggle=popover]").popover({html:true});
$('.submit-eval').each(function (index, item) {
    $(item).click(function(e){
        e.preventDefault();
        submitFunction($(item).parents("form"), item);
    });
});

function radiosAreChecked(form) {
    const selector_checked = '#' + $(form).attr("id") + " :radio:checked";
    const selector_all = '#' + $(form).attr("id") + " :radio";
    return ($(selector_checked).length === $(selector_all).length / 2);
}

function selectsHaveValue(form) {
    returnVal = true;
    const selector = '#' + $(form).attr("id") + ' .eval-batch-select option:selected';
    $(selector).each( function (index, item) {
        if ($(item).val() === ""){
            returnVal = false;
        }
    });
    return returnVal;
}

function submitFunction (form, item) {
    if(radiosAreChecked(form) && selectsHaveValue(form)){
        var data = new FormData(form[0]);
        optionsSelected.each(function (index, item) {
            data.append($(item).parents("select").attr("id"), $(item).val());
        });
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            processData: false,
            contentType: false,
            success: function(response){
                $(item).prop("disabled", true);
                alert($(form).attr("id") + " success!");
                card = $(form).parents(".card");
                $(card).remove();
                console.log($(form).attr("id") + " success!");
                console.log(response)
            },
            error: function(response){
                alert(form.attr("id") + " failed D:");
                console.log(form.attr("id") + " failed D:");
                console.log(response)
            }
        });
    }
}