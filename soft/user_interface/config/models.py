from django.db import models
from . import parameters as params


# Configuration
#   - ContinuousRule
#   - StandardRule
#       - StandardRuleCondition
#   - BankRule
#       - BankRuleState
#           - BankRuleStateCondition
#   - ChaseRule
#       - ChaseRuleState


# LedWall config model
class Configuration(models.Model):
    name = models.CharField(max_length=100, null=True)  # Configuration's name
    description = models.TextField(null=True)           # If necessary, add a description
    creation = models.DateTimeField(auto_now_add=True, auto_now=False,
                                verbose_name="Creation")
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.active:
            try:
                temp = Configuration.objects.get(active=True)
                if self != temp:
                    temp.active = False
                    temp.save()
            except Configuration.DoesNotExist:
                pass
        super(Configuration, self).save(*args, **kwargs)


# Rules

class Rule(models.Model):
    name = models.CharField(max_length=100)             # Rule's name
    config = models.ForeignKey('Configuration', on_delete=models.CASCADE)         # Configuration the rule belong to

    class Meta:
        abstract = True


class ContinuousRule(Rule):
    midi_cc = models.IntegerField()                     # Midi control to link
    continuous_param = models.IntegerField(choices=params.CONTINUOUS_PARAM, default=params.BPM_CONTINUOUS)    # Param to link
    scale_down = models.IntegerField()                  # Setting full scale
    scale_up = models.IntegerField()

    def __str__(self):
        return self.name


class StandardRule(Rule):
    note = models.IntegerField()                        # Midi note
    event_param = models.IntegerField(choices=params.EVENTS_PARAM, default=params.BEAT_EVENT)    # Param to link
    max_duration = models.IntegerField(default=0)       # Note duration in ms, 0 --> infinite

    def __str__(self):
        return self.name


class BankRule(Rule):
    max_duration = models.IntegerField(null=True)       # Max duration of a state

    def __str__(self):
        return self.name


class ChaseRule(Rule):
    event_param = models.IntegerField(choices=params.EVENTS_PARAM, default=params.BEAT_EVENT)    # Param to link
    state_duration = models.IntegerField()              # Duration of a state
    random_states = models.BooleanField()               # Set state order to random

    def __str__(self):
        return self.name


# Conditions

class Condition(models.Model):
    # Boolean condition
    bool_param = models.IntegerField(choices=params.BOOLEAN_PARAM, null=True, blank=True)    # Param to link
    bool_active_on_false = models.BooleanField(default=False)
    # Continuous condition
    continuous_param = models.IntegerField(choices=params.CONTINUOUS_PARAM, null=True, blank=True, default=params.BPM_CONTINUOUS)
    operator = models.CharField(
        max_length=3,
        choices=(('<', '<'),('=', '='),('>', '>')),
        default='<')
    value = models.IntegerField(null=True, blank=True)                                      # Value to compare with

    class Meta:
        abstract = True

    def __str__(self):
        if self.bool_param:
            disp = self.get_bool_param_display()
            if self.bool_active_on_false:
                disp = "not " + disp
            return disp
        else: return str(self.get_continuous_param_display()) + self.operator + str(self.value)


class StandardRuleCondition(Condition):
    rule = models.ForeignKey('StandardRule', on_delete=models.CASCADE)            # Rule's the condition belongs to


class BankRuleStateCondition(Condition):
    state = models.ForeignKey('BankRuleState', on_delete=models.CASCADE)           # State's the condition belongs to


class ChaseRuleCondition(Condition):
    rule = models.ForeignKey('ChaseRule', on_delete=models.CASCADE)               # State's the condition belongs to


# States

class State(models.Model):
    name = models.CharField(max_length=100)  # State name
    note = models.IntegerField()  # Midi note

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BankRuleState(State):
    rule = models.ForeignKey('BankRule', on_delete=models.CASCADE)                # Rule this action belongs to
    priority = models.IntegerField()                    # Priority between 1 to 100


class ChaseRuleState(State):
    rule = models.ForeignKey('ChaseRule', on_delete=models.CASCADE)               # Rule this action belongs to
