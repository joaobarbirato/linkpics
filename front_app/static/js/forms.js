dic_avaliacao = null;

$(document).ready(function (e){
    $('#resultado-alinhamento').hide();
});

function click_function(link){
    $("#btnAlignFile").prop("disabled", true);
    $("#btnAlignLink").prop("disabled", true);
    $("#btnAlignManual").prop("disabled", true);
    $("#btnAlignFile").css("cursor", "progress");
    $("#btnAlignLink").css("cursor", "progress");
    $("#btnAlignManual").css("cursor", "progress");
    let pessoas = 1;
    let objetos = 0;
    // Project alignment
    if (window.location.pathname.indexOf("baseline") < 0){
        objetos = 0;
        pessoas = 1;
    }
    // Baseline alignment
    else {
        objetos = 4;
        pessoas = 0;
    }
    const data = {
        "link": link,
        "pessoas": pessoas,
        "objetos": objetos,
        "csrf_token": $('#align_form_csrf').val(),
    };
    $.ajax({
        url: $('#align-form').attr('action'),
        data: data,
        type: $('#align-form').attr('method'),
        success: function (response) {
            successFunction(response);
        },
        error: function (error) {
            errorFunction(error)
        }
    });
}

$('#btnAlignFile').click(function (e) {
    e.preventDefault();
    $(".img_alinhamento").attr("src", "static/black_image.png");
    link = $("#url_folha").val();
    if (link == null) {
        alert('Você deve selecionar um Link!');
    }
    else {
        click_function(link);
    }
});

$('#linkform').submit(function (e) {
    e.preventDefault();
    $(".img_alinhamento").attr("src", "static/black_image.png");
    link = $("#input_link").val();
    if (link == null) {
        alert('Você deve selecionar um Link!');
    }
    else {
        click_function(link)
    }
});

function successFunction(response){
    console.log(response);
    const result_pessoas = response["result_pessoas"];
    const result_img = response["img_alinhamento"];
    let result_colums = '';
    if(result_pessoas != null){
        for (const [key, value] of Object.entries(result_pessoas)) {
            result_colums += "<tr><td>" + key + "</td><td>" + value + "</td></tr>";
        }
    }
    const result_objetos = response["result_objetos"];
    if(result_objetos != null){
        for (const [key, value] of Object.entries(result_objetos)) {
            result_colums += "<tr><td>" + key + "</td><td>" + value + "</td></tr>";
        }
    }
    const body_table = document.getElementById("line_resultados");
    body_table.innerHTML = result_colums;
    $(".img_alinhamento").attr("src", result_img);
    console.log(result_img);
    if (result_img == null) {
        console.log(result_img.length);
        img_resultado.setAttribute("src", "static/sem_imagem.png")
    }
    // Alinhamento
    //setando o texto
    const texto = document.getElementById("texto");
    texto.innerHTML = response["texto"];
    //setando a legenda
    const legenda = document.getElementById("legenda");
    legenda.innerHTML = response["legenda"];
    //setando o titulo
    const titulo = document.getElementById("titulo");
    titulo.innerHTML = response["titulo"];

    dic_avaliacao = response["dic_avaliacao"];
    $("#btnAlignFile").prop("disabled", false);
    $("#btnAlignFile").css("cursor", "default");
    $("#btnAlignLink").prop("disabled", false);
    $("#btnAlignLink").css("cursor", "default");
    $("#btnAlignManual").prop("disabled", false);
    $("#btnAlignManual").css("cursor", "default");
    $('#resultado-alinhamento').show(1000);
}

function errorFunction(response){
    console.log(response);
    alert(response['responseJSON']['message']);
    $("#btnAlignManual").prop("disabled", false);
    $("#btnAlignManual").css("cursor", "default");
}

$('#btnFimAvaliacao').click(function (e) {
    e.preventDefault();
    $("#btnFimAvaliacao").prop("disabled", true);
    $("#btnFimAvaliacao").css("cursor", "progress");
    link = $("#url_folha").val();
    if (link == null) {
        alert('Você deve selecionar um Link!');
    }
    else {
        let radios;
        const avaliacao = {};
        for (const [key, _] of Object.entries(dic_avaliacao)) {
            palavra_alinhada = key.replace(" ", "_");
            radios = document.getElementsByName("radio_" + palavra_alinhada);
            for (var i = 0; i < radios.length; i++) {
                if (radios[i].checked) {
                    avaliacao[palavra_alinhada] = radios[i].value;
                }
            }
        }
        radios = document.getElementsByName("radio_similaridade");
        let medida_similaridade;
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked) {
                medida_similaridade = radios[i].value;
                break;
            }
        }

        const data = {
            "link": $("#url_folha").val(),
            "avaliacao": JSON.stringify(avaliacao),
            "medida_similaridade": medida_similaridade
            // "alinhamento_invalido": alinhamento_invalido
        };
        $.ajax({
            url: $("#btnFimAvaliacao").attr('action'),
            data: data,
            type: $("#btnFimAvaliacao").attr('method'),
            success: function (response) {
                console.log(response);
                alert("Avaliação enviada!");
                $("#btnFimAvaliacao").prop("disabled", false);
                $("#btnFimAvaliacao").css("cursor", "default");
            },
            error: function (error) {
                errorFunction(error);
                $("#btnFimAvaliacao").prop("disabled", false);
                $("#btnFimAvaliacao").css("cursor", "default");
            }
        });
    }
});
