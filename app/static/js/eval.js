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

    allRadios.each(function (index, item) {
        $(item).prop('checked', false);
    })
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
    console.log($(selector_checked).length);
    console.log($(selector_all).length);
    return ($(selector_checked).length / 2 === $(selector_all).length / $(selector_all).length);
}

function submitFunction (form, item) {
    if(radiosAreChecked(form)){
        var data = new FormData(form[0]);
        $.ajax({
            url: form.attr("action"),
            data: data,
            type: form.attr("method"),
            processData: false,
            contentType: false,
            success: function(response){
                $(item).prop("disabled", true);
                alert($(form).attr("id") + " avaliado com sucesso!");
                card = $(form).parents(".card");
                $(card).remove();
                console.log($(form).attr("id") + " avaliado com sucesso!");
                console.log(response);
            },
            error: function(response){
                alert(form.attr("id") + " falhou D:");
                console.log(form.attr("id") + " falhou D:");
                console.log(response);
            }
        });
    } else {
        alert("É preciso assinalar todos os campos!");
    }
}