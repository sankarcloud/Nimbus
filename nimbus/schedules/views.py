# Create your views here.
# -*- coding: UTF-8 -*-

import traceback
import simplejson
import socket

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.contrib import messages
from nimbus.computers.models import Computer
from nimbus.schedules import forms
from nimbus.shared.enums import levels, days_range, weekdays_range, end_days_range
from nimbus.schedules.models import Schedule as Schedule_obj


# def add(request):
#     if request.method == "POST":
#         print "#############################################################"
#         pass
#     lforms = [forms.ScheduleForm(prefix="schedule")]
#     schedule_forms = forms.make_schedule_form_container()
#     schedule_forms.get()
#     content = {'title':u'Criar Agendamento',
#                'levels':levels,
#                'forms':lforms,
#                'formset':schedule_forms,
#                'days':days_range,
#                'end_days':end_days_range,
#                'weekdays':weekdays_range,
#                'messages': {
#                    'Mensagem teste':u'Mensagem teste'
#                }}
#     return render_to_response('add_schedules.html', content)

def edit(request, object_id):
    print object_id
    schedule = Schedule_obj.objects.get(id=object_id)
    template = 'base_schedules.html'
    lforms = [forms.ScheduleForm(prefix="schedule", instance=schedule)]
    schedule_forms = forms.make_schedule_form_container(schedule)
    schedule_forms.get()
    extra_content = {'title':u'Editar Agendamento',
                     'levels':levels,
                     'forms':lforms,
                     'formset':schedule_forms,
                     'days':days_range,
                     'end_days':end_days_range,
                     'weekdays':weekdays_range}
    return render_to_response(template, extra_content)

def render(request, object_id=0):
    lforms = [ forms.ScheduleForm(prefix="schedules", initial={'computer':object_id}) ]
    content = {'title':u'Criar Backup',
               'forms':lforms,
               'computer_id':object_id}
    return render_to_response("backup_add.html", content)

def profile_new(request):
    lforms = [forms.ProfileForm(prefix="profile")]
    content = {'title':u'Criar Perfil de Backup',
               'forms':lforms}
    return render_to_response("profile_new.html", content)

def insert_schedule(POST_data):
    if POST_data.has_key('schedule-name') and (POST_data['schedule-name'] != ''):
        schedule_data = {'schedule-name': POST_data['schedule-name']}
    else:
        sugested = []
        if POST_data.has_key('schedule.hourly.active'):
            sugested.append('hora em hora')
        if POST_data.has_key('schedule.dayly.active'):
            sugested.append('diário')
        if POST_data.has_key('week.active'):
            sugested.append('semanal')
        if POST_data.has_key('schedule.monthly.active'):
            sugested.append('mensal')
        if len(sugested) > 1:
            sugested_name = "%s e %s" % (', '.join(sugested[0:-1]), sugested[-1])
        elif len(sugested) == 1:
            sugested_name = sugested[0]
        else:
            return False
        schedule_data = {'schedule-name': sugested_name.capitalize()}
    schedule_data["schedule-is_model"] = POST_data["schedule-is_model"]
    schedule_form = forms.ScheduleForm(schedule_data, prefix="schedule")
    if schedule_form.is_valid():
        new_schedule = schedule_form.save()
        print "deu certo"
        return new_schedule
    else:
        # tratar na interface
        # messages.warning(request, procedure_form.errors)
        # return render_to_response(request, "schedules_new.html", locals())
        print "nao deu certo"
        return schedule_form.errors

def insert_monthly(data, schedule):
    if data.has_key('schedule.monthly.active'):
        days = data['schedule.monthly.day']
        if (len(days) > 1) and (days[-1] == ","):
            days = days[0:-1]
        month_form = forms.MonthlyForm({'schedule': schedule.id,
                                        'days': days,
                                        'hour': data['month-hour'],
                                        'level': data['month-level']})
        if month_form.is_valid():
            month_form.save()
            return u"Agendamento mensal adicionado com sucesso"
        else:
            # tratar na interface
            return month_form.errors
    else:
        return None

def insert_weekly(data, schedule):
    if data.has_key('week.active'):
        days = data['schedule.weekly.day']
        if days[-1] == ",":
            days = days[0:-1]
        week_form = forms.WeeklyForm({'schedule': schedule.id,
                                      'days': days,
                                      'hour': data['week-hour'],
                                      'level': data['week-level']})
        if week_form.is_valid():
            week_form.save()
            return u"Agendamento semanal adicionado com sucesso"
        else:
            # tratar na interface
            return week_form.errors
    else:
        return None

def insert_daily(data, schedule):
    if data.has_key('schedule.dayly.active'):
        day_form = forms.DailyForm({'schedule': schedule.id,
                                    'hour': data['day-hour'],
                                    'level': data['day-level']})
        if day_form.is_valid():
            day_form.save()
            return u"Agendamento diário adicionado com sucesso"
        else:
            # tratar na interface
            return day_form.errors
    else:
        return None
        
def insert_hourly(data, schedule):
    if data.has_key('schedule.hourly.active'):
        hour_form = forms.HourlyForm({'schedule': schedule.id,
                                    'minute': data['hour-minute'],
                                    'level': data['hour-level']})
        if hour_form.is_valid():
            hour_form.save()
            return u"Agendamento de hora em hora adicionado com sucesso"
        else:
            # tratar na interface
            return hour_form.errors
    else:
        return None

def add_schedule(request):
    print "##################################################################"
    lforms = [forms.ScheduleForm(prefix="schedule")]
    schedule_forms = forms.make_schedule_form_container()
    schedule_forms.get()
    days_range = range(1, 32)
    weekdays_range = {0:'Domingo',
                      1:'Segunda',
                      2:'Terca',
                      3:'Quarta',
                      4:'Quinta',
                      5:'Sexta',
                      6:'Sabado'}
    end_days_range = [5, 10, 15, 20, 25, 30]
    content = {'title':u'Criar Agendamento',
               'forms':lforms,
               'formset':schedule_forms,
               'days':days_range,
               'end_days':end_days_range,
               'weekdays':weekdays_range,
               'messages':[u'Mensagem teste',
                           u'Mensagem teste 2']
              }
    if request.method == "POST":
        print request.POST
        data = request.POST
        new_schedule = insert_schedule(data)
        messages = []
        messages.append("bla")
        messages.append("ble")
        messages.append("bli")
        content["messages"] = messages
        if new_schedule:
            messages = []
            messages.append(insert_monthly(data, new_schedule))
            messages.append(insert_weekly(data, new_schedule))
            messages.append(insert_daily(data, new_schedule))
            messages.append(insert_hourly(data, new_schedule))
            content["messages"] = messages
    return render_to_response("add_schedule.html", content)


# def fileset_new(request, object_id):
#     # apenas teste, remover em modo de produção
#     if request.method == "POST":
#         print request.POST
#     lforms = [forms.FileSetForm(prefix="fileset")]
#     lformsets = [forms.FilePathForm(prefix="filepath")]
#     formset = forms.FilesFormSet()
#     content = {'title':u'Criar Sistema de Arquivos',
#                'forms':lforms,
#                'formsets':lformsets,
#                'computer_id':object_id,
#                'formset' : formset}
#     return render_to_response("fileset_new.html", content)


# def get_tree(request):
#     if request.method == "POST":
#         try:
#             path = request.POST['path']
#             computer_id = request.POST['computer_id']
#             try:
#                 computer = Computer.objects.get(id=computer_id)
#                 files = computer.get_file_tree(path)
#                 response = simplejson.dumps(files)
#             except socket.error, error:
#                 response = simplejson.dumps({"type" : "error",
#                                              "message" : "Impossível conectar ao cliente"})
#             except Computer.DoesNotExist, error:
#                 response = simplejson.dumps({"type" : "error",
#                                              "message" : "Computador não existe"})
#             return HttpResponse(response, mimetype="text/plain")
#         except Exception:
#             traceback.print_exc()





# # -*- coding: utf-8 -*-
# 
# from time import strftime, strptime
# 
# 
# from django.shortcuts import redirect
# from django.core.exceptions import ValidationError
# from django.contrib.auth.decorators import login_required
# 
# from nimbus.schedules.models import Schedule, Hourly
# from nimbus.schedules.forms import (ScheduleForm, DailyForm, MonthlyForm,
#                                     HourlyForm, WeeklyForm)
# from nimbus.schedules.shared import trigger_class, trigger_map
# from nimbus.shared.views import render_to_response
# from nimbus.shared import utils
# from nimbus.libs.db import Session
# 
# from django.contrib import messages
# from nimbus.shared.enums import days, weekdays, levels, operating_systems
# 
# 
# @login_required
# def add(request):
#     title = u"Criar agendamento"
# 
#     schedule_form = ScheduleForm()
#     daily_form = DailyForm()
#     monthly_form = MonthlyForm()
#     hourly_form = HourlyForm()
#     weekly_form = WeeklyForm()
# 
#     extra_content = {
#         'days': days,
#         'weekdays': weekdays,
#         'levels': levels,
#         'operating_systems': operating_systems,
#         'schedule_form': schedule_form
#     }
#     extra_content.update(**locals())
# 
#     if request.method == 'POST':
#         # TODO: Save.
#         pass
# 
#     return render_to_response(request, 'add_schedules.html', extra_content)
# 
# 
# @login_required
# def edit(request, object_id):
# 
#     schedule = Schedule.objects.get(id=object_id)
#     title = u"Editar agendamento"
#     template = 'base_schedules.html'
# 
# 
#     extra_content = {
#         'days': days,
#         'weekdays': weekdays,
#         'levels': levels,
#         'operating_systems': operating_systems,
#     }
#     extra_content.update(**locals())
# 
#     if request.method == "GET":
#         return render_to_response(request, template, extra_content)
# 
# 
#     if request.method == "POST":
# 
# 
#         errors = {}
#         extra_content["errors"] =  errors
# 
#         schedule = Schedule.objects.get(id=object_id)
# 
#         template = 'edit_schedules.html'
#         schedule_name = request.POST.get('schedule.name')
# 
#         try:
#             old_schedule = Schedule.objects.get(name=schedule_name)
#         except Schedule.DoesNotExist, notexist:
#             old_schedule = None
# 
#         if (not old_schedule is None) and old_schedule != schedule:
#             errors["schedule_name"] = "Nome não disponível. Já existe um agendamento com este nome"
# 
# 
#         with Session() as session:
# 
#             if schedule_name:
# 
#                 schedule.name = schedule_name
# 
# 
#                 selected_a_trigger = False
#                 triggers = ["schedule.monthly", "schedule.dayly", "schedule.weekly", "schedule.hourly"]
# 
# 
#                 for trigger in triggers:
# 
#                     selected_a_trigger = True
#                     is_trigger_edit = False
# 
#                     trigger_name = trigger[len("schedule."):]
#                     Trigger = trigger_class[trigger_name]
# 
#                     old_triggers = [ t for t in schedule.get_triggers() if isinstance(t, Trigger) ]
# 
#                     if old_triggers:
#                         is_trigger_edit = True
# 
#                     if not request.POST.get(trigger + '.active'):
# 
#                         for t in old_triggers:
#                             t.delete()
#                             session.delete(t)
# 
#                     else: # active
# 
#                         hour = request.POST.get(trigger + '.hour')
#                         if not hour:
#                             errors['schedule_hour'] = "Você deve informar a hora de execução do agendamento %s" % trigger_map[trigger_name]
#                         else:
#                             if Trigger is Hourly:
#                                 hour = strftime("%H:%M", strptime(hour, "%M"))
# 
#                             level = request.POST.get(trigger + '.level')
# 
#                             if not trigger_name in ["dayly", "hourly"]:
#                                 post_days = set(request.POST.getlist(trigger + '.day'))
# 
#                                 if not post_days and not is_trigger_edit:
#                                     errors['schedule_day'] = "Você deve selecionar um dia para a execução do agendamento %s"  % trigger_map[trigger_name]
#                                 else:
#                                     old_days = set([ unicode(t.day) for t in old_triggers ])
# 
#                                     if len(old_days) != len(post_days):
#                                         new_days = post_days - old_days
#                                         remove_days =  old_days - post_days
# 
#                                         for d in remove_days:
#                                             t = Trigger.objects.get(day=d,schedule=schedule)
#                                             t.delete()
#                                             session.delete(t)
# 
#                                         for d  in new_days:
#                                             Trigger.objects.create(day=d,
#                                                                    hour=hour,
#                                                                    level=level,
#                                                                    schedule=schedule)
#                             else:
#                                 try:
#                                     trigger = Trigger.objects.get(schedule=schedule)
#                                 except Trigger.DoesNotExist, error:
#                                     trigger = Trigger()
#                                     trigger.schedule = schedule
# 
#                                 trigger.hour = hour
#                                 trigger.level = level
#                                 session.add(trigger)
#                                 try:
#                                     trigger.save()
#                                 except ValidationError, error:
#                                     errors['schedule_hour'] = 'Horário do agendamento errado'
# 
# 
# 
#                             is_trigger_edit = False
# 
#                 if not selected_a_trigger:
#                     errors['schedule_name'] = "Você deve ativar pelo menos um tipo de agendamento"
# 
#             else:
#                 errors['schedule_name'] = "Você deve inserir um nome na configuração do agendamento"
# 
#             if not errors:
#                 schedule.save()
#                 session.add(schedule)
#                 messages.success(request, u"Agendamento atualizado com sucesso.")
#                 return redirect('nimbus.schedules.views.edit', object_id)
#             else:
#                 session.rollback()
#                 extra_content.update(**locals())
#                 extra_content.update( utils.dict_from_querydict(
#                                             request.POST,
#                                             lists=("schedule_monthly_day",
#                                                    "schedule_dayly_day",
#                                                    "schedule_hourly_day",
#                                                    "schedule_weekly_day")) )
# 
#                 return render_to_response(request, template, extra_content )