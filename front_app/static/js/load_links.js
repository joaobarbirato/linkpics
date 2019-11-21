$('#btnCarregarLinks').click(function (e) {
    e.preventDefault();
    const form_data = new FormData($("#uploadfileform")[0]);
    form_data["csrf_token"] = $('#link_form_csrf').val();
    $.ajax({
        url: '/upload',
        data: form_data,
        processData: false,
        contentType: false,
        type: 'POST',
        success: function (response) {
            console.log(response);

            const urls = response["urls"];
            let result_colums = '';
            let select = document.getElementById('url_folha');
            removeOptions(select);

            for (i = 0; i < urls.length; i++) {
                const opt = document.createElement('option');
                opt.value = urls[i];
                opt.innerHTML = urls[i];
                select.appendChild(opt);
            }
        },
        error: function (error) {
            console.log(error);
            alert(error);
        }
    });
});

function removeOptions(selectbox) {
    let i;
    for (i = selectbox.options.length - 1; i >= 0; i--) {
        selectbox.remove(i);
    }
}