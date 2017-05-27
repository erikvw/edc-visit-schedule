from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models import options


from ..site_visit_schedules import site_visit_schedules, RegistryNotLoaded, SiteVisitScheduleError
from ..visit_schedule import VisitScheduleModelError

if 'visit_schedule_name' not in options.DEFAULT_NAMES:
    options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('visit_schedule_name',)


class VisitScheduleMethodsModelMixin(models.Model):
    """A model mixin that adds methods used to work with the visit schedule.

    Declare with VisitScheduleFieldsModelMixin or the fields from
    VisitScheduleFieldsModelMixin
    """

    @property
    def visits(self):
        return self.schedule.get_visits()

    @property
    def schedule(self):
        """Returns a schedule object from Meta.visit_schedule_name or
        self.schedule_name.

        Declared on Meta like this:
            visit_schedule_name = 'visit_schedule_name.schedule_name'
        """
        try:
            _, schedule_name = self._meta.visit_schedule_name.split('.')
        except ValueError as e:
            raise VisitScheduleModelError(f'{self.__class__.__name__}. Got {e}') from e
        return self.visit_schedule.get_schedule(schedule_name=schedule_name)

    @property
    def visit_schedule(self):
        """Returns a visit schedule object from Meta.visit_schedule_name.

        Declared on Meta like this:
            visit_schedule_name = 'visit_schedule_name.schedule_name'
        """
        try:
            visit_schedule_name, _ = self._meta.visit_schedule_name.split('.')
        except ValueError as e:
            raise VisitScheduleModelError(f'{self.__class__.__name__}. Got {e}') from e
        try:
            visit_schedule = site_visit_schedules.get_visit_schedule(
                visit_schedule_name)
        except RegistryNotLoaded as e:
            raise VisitScheduleModelError(
                f'visit_schedule_name: \'{visit_schedule_name}\'. Got {e}') from e
        except SiteVisitScheduleError as e:
            raise VisitScheduleModelError(
                f'visit_schedule_name: \'{visit_schedule_name}\'. Got {e}') from e
        return visit_schedule

    def timepoint_datetimes(self, base_datetime, schedule):
        """Returns a calculated list of unadjusted datetimes in order
        of timepoint based on the schedule."""
        for visit in schedule.visits:
            if visit.base_interval == 0:
                timepoint_datetime = base_datetime
            else:
                timepoint_datetime = base_datetime + relativedelta(
                    **{visit.base_interval_unit: visit.base_interval})
            yield (visit, timepoint_datetime)

    class Meta:
        abstract = True


class VisitScheduleFieldsModelMixin(models.Model):
    """A model mixin that adds fields required to work with the visit
    schedule methods on the VisitScheduleMethodsModelMixin.

    Note: visit_code is not included."""

    visit_schedule_name = models.CharField(
        max_length=25,
        editable=False,
        help_text='the name of the visit schedule used to find the "schedule"')

    schedule_name = models.CharField(
        max_length=25,
        editable=False)

    class Meta:
        abstract = True


class VisitScheduleModelMixin(VisitScheduleFieldsModelMixin,
                              VisitScheduleMethodsModelMixin,
                              models.Model):

    """A model mixin that adds adds field attributes and methods that
    link a model instance to its schedule.

    This mixin is used with Appointment and Visit models via their
    respective model mixins.
    """

    visit_code = models.CharField(
        max_length=25,
        null=True,
        editable=False)

    class Meta:
        abstract = True
