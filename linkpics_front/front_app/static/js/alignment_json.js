$("#align-to-json").submit(function (e){
    e.preventDefault();
    let form_data = new FormData($(this).get(0));
    $.ajax({
        data: form_data,
        url: $(this).attr("action"),
        type: $(this).attr("method"),
        cache: false,
        processData: false,
        contentType: false,
        success: function (response) {
            alert(":D");
            console.log(response);
        },
        error: function (response) {
            alert("D:");
            console.log(response);
        }
    });
});
