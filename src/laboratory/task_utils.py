from django.utils import timezone

from laboratory.models import Laboratory, InformsPeriod, Inform


def create_informsperiods(informscheduler, now=timezone.now()):
    last_update = informscheduler.last_execution
    if last_update is not None:
        last_close = last_update.close_application_date
        next_update = last_update.start_application_date + timezone.timedelta(
            days=informscheduler.period_on_days)
    else:
        next_update = informscheduler.start_application_date
        last_close = informscheduler.close_application_date



    last_close = last_close + timezone.timedelta(days=informscheduler.period_on_days)
    if next_update == now.today().date():
        labs = Laboratory.objects.filter(organization__pk=informscheduler.organization.pk)
        ip=InformsPeriod.objects.create(
            scheduler=informscheduler,
            organization=informscheduler.organization,
            inform_template=informscheduler.inform_template,
            start_application_date=next_update,
            close_application_date=last_close

        )
        for lab in labs:
            inform = Inform.objects.create(
                organization=informscheduler.organization,
                name="%s -- %s"%(informscheduler.name, lab.name),
                custom_form=informscheduler.inform_template,
                context_object=lab,
                schema=informscheduler.inform_template.schema,
            )
            ip.informs.add(inform)