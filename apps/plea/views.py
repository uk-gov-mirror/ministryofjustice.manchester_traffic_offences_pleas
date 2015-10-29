from django.utils.decorators import method_decorator
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import RequestContext, redirect
from django.views.generic import FormView

from brake.decorators import ratelimit

from apps.forms.stages import MultiStageForm
from apps.forms.views import StorageView

from .models import Case, Court
from .forms import CourtFinderForm
from .stages import (NoticeTypeStage,
                     CaseStage,
                     YourDetailsStage,
                     CompanyDetailsStage,
                     PleaStage,
                     YourStatusStage,
                     YourFinancesStage,
                     HardshipStage,
                     HouseholdExpensesStage,
                     OtherExpensesStage,
                     CompanyFinancesStage,
                     ReviewStage,
                     CompleteStage)
from .fields import ERROR_MESSAGES


class PleaOnlineForms(MultiStageForm):
    url_name = "plea_form_step"
    stage_classes = [NoticeTypeStage,
                     CaseStage,
                     YourDetailsStage,
                     CompanyDetailsStage,
                     PleaStage,
                     YourStatusStage,
                     YourFinancesStage,
                     HardshipStage,
                     HouseholdExpensesStage,
                     OtherExpensesStage,
                     CompanyFinancesStage,
                     ReviewStage,
                     CompleteStage]

    def __init__(self, *args, **kwargs):
        super(PleaOnlineForms, self).__init__(*args, **kwargs)

        self._urn_invalid = False

    def save(self, *args, **kwargs):
        """
        Check that the URN has not already been used.
        """
        try:
            saved_urn = self.all_data["case"]["urn"]
        except KeyError:
            saved_urn = None

        if saved_urn and not Case.objects.can_use_urn(saved_urn):
            self._urn_invalid = True

            return

        return super(PleaOnlineForms, self).save(*args, **kwargs)

    def render(self):
        if self._urn_invalid:
            return redirect("urn_already_used")

        return super(PleaOnlineForms, self).render()


class PleaOnlineViews(StorageView):
    def __init__(self, *args, **kwargs):
        super(PleaOnlineViews, self).__init__(*args, **kwargs)
        self.index = None
        self.storage = None

    def dispatch(self, request, *args, **kwargs):
        # If the session has timed out, redirect to case
        if not request.session.get("plea_data") and kwargs.get("stage") != "notice_type":
            return HttpResponseRedirect(reverse_lazy("plea_form_step", args=("notice_type",)))

        # Store the index if we've got one
        idx = kwargs.pop("index", None)
        if idx is not None:
            self.index = int(idx)

        # Load storage
        self.storage = self.get_storage(request, "plea_data")

        return super(PleaOnlineViews, self).dispatch(request, *args, **kwargs)

    def get(self, request, stage=None):
        if not stage:
            stage = PleaOnlineForms.stage_classes[0].name
            return HttpResponseRedirect(reverse_lazy("plea_form_step", args=(stage,)))

        form = PleaOnlineForms(self.storage, stage, self.index)
        case_redirect = form.load(RequestContext(request))
        if case_redirect:
            return case_redirect

        form.process_messages(request)

        if stage == "complete":
            self.clear_storage(request, "plea_data")

        return form.render()

    @method_decorator(ratelimit(block=True, rate=settings.RATE_LIMIT))
    def post(self, request, stage):
        nxt = request.GET.get("next", None)

        form = PleaOnlineForms(self.storage, stage, self.index)
        form.save(request.POST, RequestContext(request), nxt)

        if not form._urn_invalid:
            form.process_messages(request)

        request.session.modified = True
        return form.render()


class UrnAlreadyUsedView(StorageView):
    template_name = "urn_used.html"

    def post(self, request):

        del request.session["plea_data"]

        return redirect("plea_form_step", stage="case")


class CourtFinderView(FormView):
    template_name = "court_finder.html"
    form_class = CourtFinderForm

    def form_valid(self, form):
        try:
            court = Court.objects.get_by_urn(form.cleaned_data["urn"])
        except Court.DoesNotExist:
            court = False

        return self.render_to_response(self.get_context_data(form=form,
                                                             court=court,
                                                             submitted=True))

    def form_invalid(self, form):

        urn_is_invalid = False
        if "urn" in form.errors and ERROR_MESSAGES["URN_INCORRECT"] in form.errors["urn"]:
            urn_is_invalid = True

        return self.render_to_response(
            self.get_context_data(form=form,
                                  urn_is_invalid=urn_is_invalid))

