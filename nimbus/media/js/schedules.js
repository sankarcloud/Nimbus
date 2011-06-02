$(document).ready(function(){
    $(".submit").click(function(){
    	alert('vai');
        var dataString = "";
        var month_days = "";
        var week_days = "";
        $.each($('#schedule_new').serializeArray(), function(i, field) {
            if (field.name == 'schedule.monthly.day')
            {
                month_days += field.value+",";
            }
            else if (field.name == 'schedule.weekly.day')
            {
                week_days += field.value+",";
            }
            else
            {
                dataString += field.name+"="+field.value+"&";
            }
        });
        dataString += "schedule.monthly.day="+month_days+"&schedule.weekly.day="+week_days;
        $.ajax({
            type: "POST",
            url: "/schedules/add/",
            data: dataString,
            success: function() {
                alert("Cadastro efetuado com MUITO MUITO sucesso!");
                //$(document).trigger('close.facebox');
            },
            error: function(){
                alert('Houve um problema com a requisição');
                //$(document).trigger('close.facebox');
            }
        });
    };
    $(".use_it").click(function(){
        commit_settings("False");
    });
    $(".use_and_save_it").click(function(){
        commit_settings("True");
        jQuery.facebox( ajax : "/schedules/add/" )
    });
});
