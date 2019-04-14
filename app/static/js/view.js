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

function validateSelect(){
    console.log(select_input.val() !== "");
    return (select_input.val() !== "");
}