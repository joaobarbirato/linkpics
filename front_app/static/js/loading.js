$.ajaxSetup({
    beforeSend: function() {
        showLoading();
    },
    complete: function() {
        hideLoading();
    }
});

$(document).ready(function (e) {
    hideLoading();
});

function hideLoading(){
    $("#loading").hide();
}

function showLoading() {
    $("#loading").show();
}
