checkboxes = $('#evaluated_actions .checkbox');
checkbox_class = $('.checkbox');
form = $('#evaluated_actions');

select_input = $('#select-actions');

$('#check-all').click(function() {
    const checked = $(this).prop('checked');
    $('.checkbox').prop('checked', checked);
    if(checked){
        $('#label-check-all').html("Desmarcar todos")
    }else{
        $('#label-check-all').html("Marcar todos")
    }
});

$('.check-batch').each(function(index, item){
    $(item).click(function () {
        const checked = $(this).prop('checked');
        const this_id = $(this).prop('id');
        const this_label_sel = '#label-' + this_id;
        msg = $(this_label_sel).html();
        $("#div-of-" + this_id + ' .checkbox').prop('checked', checked);
        if(checked){
            $(this_label_sel).html(msg.replace("Marcar", "Desmarcar"));
        }else{
            $(this_label_sel).html(msg.replace("Desmarcar", "Marcar"));
        }
    });
});

function validateSelect(){
    console.log(select_input.val() !== "");
    return (select_input.val() !== "");
}