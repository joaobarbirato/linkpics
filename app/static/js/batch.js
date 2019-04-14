$(document).ready(function (e) {
    output = $('#batch_links');
});

$('#upload-batch').submit(function(e){
    e.preventDefault();
    output.html("");
    let form_data = new FormData($(this).get(0));
    $.ajax({
        url: $(this).attr("action"),
        data: form_data,
        processData: false,
        contentType: false,
        type: "post",
        success: function (response) {
            const urls = response["urls"];
            console.log(urls.length);
            let batch_links = $("#batch_links");
            // batch_links.attr("rows", urls.length);
            for(const url in urls){
                batch_links.text(batch_links.text() + urls[url] + "\n");
                // output.append(
                //     "<li><input type='text' name='url_" + url + "' value=\"" + urls[url] + "\"/></li>"
            }
        },
        error: function (response) {},
    });
});

$("#align-batch").submit(function (e){
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
