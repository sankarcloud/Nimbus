function set_toggles() {
    $('.toggle').click(
        function () {
            visible = false;
            if ($('#' + $(this).attr('rel') + ':visible').size()) {
                visible = true;
            }
            
            $('#' + $(this).attr('rel')).toggle('fast');
            if (visible) {
                $.cookie('#' + $(this).attr('rel'), null);
            } else {
                $.cookie('#' + $(this).attr('rel'), true);
            }
        }
    )
    
    $('.cookie_toggle').each(
        function() {
            if ($.cookie('#' + $(this).attr('id')) == 'true') {
                $(this).show();
            }
        }
    );
}

function set_backup_type() {
    if (!$('form select[name=type]')) {
        return false;
    }
    $('form select[name=type]').change(
        function() {
            backup_type = $(this).children().filter(':selected').val();
            change_backup_type(backup_type);
        }
    );
    $('form select[name=type]').change();
}

function change_backup_type(backup_type) {
    $('#id_schedule_type').val(backup_type);
    switch (backup_type.toLowerCase()) {
        case 'weekly':
            // Do something...
            //console.log('weekly');
            $('.mtriggform').hide('fast');
            $('.mtriggform').find('input, select').attr('disabled', true);
            $('.wtriggform').show('fast');
            $('.wtriggform').find('input, select').attr('disabled', false);
            $('.triggform_message').hide('fast');
            break;
        case 'monthly':
            // Do something more...
            //console.log('monthly');
            $('.mtriggform').show('fast');
            $('.mtriggform').find('input, select').attr('disabled', false);
            $('.wtriggform').hide('fast');
            $('.wtriggform').find('input, select').attr('disabled', true);
            $('.triggform_message').hide('fast');
            break;
        default:
            // Go away.
            //console.log('default');
            $('.mtriggform').hide('fast');
            $('.mtriggform').find('input, select').attr('disabled', true);
            $('.wtriggform').hide('fast');
            $('.wtriggform').find('input, select').attr('disabled', true);
            $('.triggform_message').show('fast');
    }
}



function set_schedule_procedure() {
    $('#execute_procedure #id_run_now').change(
        function() {
            change_schedule_procedure();
        }
    );
    $('#execute_procedure #id_run_now').click();
    $('#execute_procedure #id_run_now').change();
}

function change_schedule_procedure() {
    run_now = $('#execute_procedure #id_run_now').attr('checked');
    if (!run_now) {
        $('.runscheduledform').show('fast');
        $('#execute_procedure input[type=submit]').val('Agendar');
    } else {
        $('.runscheduledform').hide('fast');
        $('#execute_procedure input[type=submit]').val('Executar');
    }
}


$(document).ready(function() {
    // Execute function to start the application.
    set_toggles();
    set_backup_type();
    set_schedule_procedure();
});