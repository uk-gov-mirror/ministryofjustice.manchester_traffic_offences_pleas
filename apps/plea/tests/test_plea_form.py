import datetime
from mock import Mock, MagicMock, patch
from importlib import import_module
import socket
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test import Client
from django.test.client import RequestFactory
from django.template.context import RequestContext


from ..models import Case
from ..views import PleaOnlineForms
from ..forms import CompanyFinancesForm


class TestMultiPleaFormBase(TestCase):

    def get_request_mock(self, url, url_name="", url_kwargs=None):
        request_factory = RequestFactory()

        if not url_kwargs:
            url_kwargs = {}
        request = request_factory.get(url)
        request.resolver_match = Mock()
        request.resolver_match.url_name = url_name
        request.resolver_match.kwargs = url_kwargs
        return request

class TestMultiPleaForms(TestMultiPleaFormBase):
    def setUp(self):
        self.session = {}
        self.request_context = {}

        self.plea_stage_pre_data_1_charge = {"case": {"date_of_hearing": "2015-01-01",
                                                      "urn_0": "06",
                                                      "urn_1": "AA",
                                                      "urn_2": "0000000",
                                                      "urn_3": "00",
                                                      "number_of_charges": 1,
                                                      "company_plea": False},
                                             "your_details": {"name": "Charlie Brown",
                                                              "contact_number": "012345678",
                                                              "email": "charliebrown@example.org"}}

        self.plea_stage_pre_data_3_charges = {"case": {"date_of_hearing": "2015-01-01",
                                                       "urn_0": "06",
                                                       "urn_1": "AA",
                                                       "urn_2": "0000000",
                                                       "urn_3": "00",
                                                       "number_of_charges": 3,
                                                       "company_plea": False},
                                              "your_details": {"name": "Charlie Brown",
                                                               "contact_number": "012345678",
                                                               "email": "charliebrown@example.org"}}

        self.test_session_data = {
            "case": {
                "complete": True,
                "date_of_hearing": "2015-01-01",
                "urn": "06/AA/0000000/00",
                "number_of_charges": 3,
                "company_plea": False
            },
            'your_details': {"name": "Charlie Brown",
                   "contact_number": "07802639892",
                   "email": "test@example.org"},
            "plea": {
                "complete": True,
                "PleaForms": [
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    }
                ]
            },
            'your_money': {
                "complete": True,
                "you_are": "Employed",
                "employer_name": "test",
                "employer_address": "test",
                "employer_phone": "test",
                "take_home_pay_period": "Fortnightly",
                "take_home_pay_amount": "1000",
                "employer_hardship": True
            },
            'your_expenses': {
                "complete": True
            },
            'review': {
                "complete": True
            }
        }

    def test_case_stage_bad_data(self):
        form = PleaOnlineForms("case", "plea_form_step", self.session)
        form.load(self.request_context)
        form.save({}, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 4)

    def test_case_stage_urn_already_submitted(self):

        case = Case()
        case.urn = "06/AA/0000000/00"
        case.status = "sent"
        case.save()

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form = PleaOnlineForms("case", "plea_form_step", self.session)
        form.load(self.request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 1,
                   "company_plea": False},
                  self.request_context)

        response = form.render()

        self.assertEqual(form.current_stage.forms[0].errors.keys()[0], 'urn')
        self.assertEqual(response.status_code, 200)

    def test_case_stage_good_data(self):
        form = PleaOnlineForms("case", "plea_form_step", self.session)

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form.load(self.request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 1,
                   "company_plea": False},
                  self.request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

    def test_case_stage_redirects_to_company_stage(self):
        form = PleaOnlineForms("case", "plea_form_step", self.session)

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form.load(self.request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 1,
                   "company_plea": True},
                  self.request_context)

        response = form.render()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/plea/company_details/')

    def test_case_stage_redirects_to_your_money_stage(self):
        form = PleaOnlineForms("case", "plea_form_step", self.session)

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form.load(self.request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 1,
                   "company_plea": False},
                  self.request_context)

        response = form.render()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/plea/your_details/')

    def test_your_details_stage_bad_data(self):
        form = PleaOnlineForms("your_details", "plea_form_step", self.session)
        form.load(self.request_context)
        form.save({}, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 3)

    def test_your_details_stage_good_data(self):
        form = PleaOnlineForms("your_details", "plea_form_step", self.session)
        form.load(self.request_context)
        form.save({"name": "Test man",
                   "contact_number": "012345678",
                   "email": "test.man@example.org"},
                  self.request_context)
        response = form.render()
        self.assertEqual(response.status_code, 302)

    def test_plea_form_shows_errors_when_invalid(self):
        self.session.update({"case": {"complete": True,
                                      "date_of_hearing": "2015-01-01",
                                      "urn": "06/AA/0000000/00",
                                      "number_of_charges": 2},
                             "your_details": {"name": "Charlie Brown",
                                              "contact_number": "07802639892",
                                              "email": "test@example.org"}})

        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form.load(self.request_context)
        form.save({"name": "Test man",
                   "contact_number": "012345678",
                   "email": "test.man@example.org",
                   "date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 2,
                   "form-TOTAL_FORMS": 2,
                   "form-INITIAL_FORMS": "0",
                   "form-MAX_NUM_FORMS": 2},
                  self.request_context)
        response = form.render()

        self.assertEqual(len(form.current_stage.forms[0][0].errors), 1)
        self.assertEqual(len(form.current_stage.forms[0][1].errors), 1)

        self.assertEqual(response.status_code, 200)

    def test_plea_stage_redirects_when_valid(self):
        self.session.update({"case": {"complete": True,
                                      "date_of_hearing": "2015-01-01",
                                      "urn": "06/AA/0000000/00",
                                      "number_of_charges": 2,
                                      "company_plea": False},
                             "your_details": {"name": "Charlie Brown",
                                              "contact_number": "07802639892",
                                              "email": "test@example.org"}})

        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        form.load(self.request_context)
        form.save({"form-TOTAL_FORMS": "2",
                   "form-INITIAL_FORMS": "0",
                   "form-MAX_NUM_FORMS": "2",
                   "form-0-guilty": "guilty",
                   "form-0-guilty_extra": "lorem ipsum 1",
                   "form-1-guilty": "guilty",
                   "form-1-guilty_extra": "lorem ipsum 1"},
                  self.request_context)
        response = form.render()

        self.assertEqual(len(form.current_stage.forms[0][0].errors), 0)
        self.assertEqual(len(form.current_stage.forms[0][1].errors), 0)
        self.assertEqual(response.status_code, 302)

    def test_plea_stage_bad_data_single_charge(self):
        self.session.update(self.plea_stage_pre_data_1_charge)
        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        mgmt_data = {"form-TOTAL_FORMS": "1",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}
        mgmt_data.update({"form-0-guilty": "",
                          "form-0-guilty_extra": ""})

        # no form data, just the management stuff
        form.save(mgmt_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors[0]), 1)

    def test_plea_stage_good_data_single_charge(self):
        self.session.update(self.plea_stage_pre_data_1_charge)
        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        mgmt_data = {"form-TOTAL_FORMS": "1",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, self.request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

    def test_plea_stage_missing_data_multiple_charges(self):
        self.session.update(self.plea_stage_pre_data_3_charges)
        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        mgmt_data = {"form-TOTAL_FORMS": "3",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors[0]), 0)
        self.assertEqual(len(form.current_stage.forms[0].errors[1]), 1)
        self.assertEqual(len(form.current_stage.forms[0].errors[2]), 1)

    def test_plea_stage_bad_data_multiple_charges(self):
        self.session.update(self.plea_stage_pre_data_1_charge)
        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        mgmt_data = {"form-TOTAL_FORMS": "2",
                     "form-INITIAL_FORMS": "2",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].forms), 1)

    def test_plea_stage_good_data_multiple_charges(self):
        self.session.update(self.plea_stage_pre_data_1_charge)
        form = PleaOnlineForms("plea", "plea_form_step", self.session)

        mgmt_data = {"form-TOTAL_FORMS": "2",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1",
                          "form-1-guilty": "guilty",
                          "form-1-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, self.request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

    def test_plea_stage_redirects_to_company_finances(self):

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        fake_request = self.get_request_mock("/plea/plea/")
        request_context = RequestContext(fake_request)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": True
            },
            "your_details": {
                "complete": True
            },
            "your_money": {
                "complete": True
            },
            "plea": {

            }
        }

        form = PleaOnlineForms("plea", "plea_form_step", test_data)
        form.load(request_context)

        mgmt_data = {"form-TOTAL_FORMS": "1",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/plea/company_finances/")

    def test_plea_stage_skips_company_finances_when_not_guilty(self):
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        fake_request = self.get_request_mock("/plea/plea/")
        request_context = RequestContext(fake_request)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": True
            },
            "your_details": {
                "complete": True
            },
            "your_money": {
                "complete": True
            },
            "plea": {
            }
        }

        form = PleaOnlineForms("plea", "plea_form_step", test_data)
        form.load(request_context)

        mgmt_data = {"form-TOTAL_FORMS": "1",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "not_guilty",
                          "form-0-not_guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/plea/review/")

    def _get_your_money_stage(self):
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": False
            },
            "your_details": {
                "complete": True
            },
            "plea": {
                "complete": True
            }
        }

        form = PleaOnlineForms("your_money", "plea_form_step", test_data)

        form.load(self.request_context)

        return form

    def test_your_money_stage_loads(self):

        form = self._get_your_money_stage()

        response = form.render()

        self.assertEqual(response.status_code, 200)

    def test_your_money_employment_type_required(self):

        form = self._get_your_money_stage()

        form.save({}, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 1)

    def test_your_money_employed_option_with_required_fields_missing(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Employed"
        }

        form.save(test_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 4)

    def test_your_money_employed_option_with_valid_data(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Employed",
            "employed_your_job": "Window cleaner",
            "employed_take_home_pay_period": "Fortnightly",
            "employed_take_home_pay_amount": "1000",
            "employed_hardship": True
        }

        form.save(test_data, self.request_context)

        self.assertTrue(form.current_stage.forms[0].is_valid())

    def test_your_money_self_employed_option_with_required_fields_missing(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Self-employed"
        }

        form.save(test_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 4)

    def test_your_money_self_employed_option_with_valid_data(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Self-employed",
            "your_job": "Build trains",
            "self_employed_pay_period": "Fortnightly",
            "self_employed_pay_amount": "1000",
            "self_employed_hardship": False
        }

        form.save(test_data, self.request_context)

        self.assertTrue(form.current_stage.forms[0].is_valid())

    def test_your_money_benefits_option_with_required_fields_missing(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Receiving benefits"
        }

        form.save(test_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 5)

    def test_your_money_benefits_option_with_valid_data(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Receiving benefits",
            "benefits_details": "Some data about my benefits",
            "benefits_dependents": "Yes",
            "benefits_period": "Fortnightly",
            "benefits_amount": "1000",
            "receiving_benefits_hardship": False
        }

        form.save(test_data, self.request_context)

        self.assertTrue(form.current_stage.forms[0].is_valid())

    def test_your_money_other_option_with_required_fields_missing(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Other"
        }

        form.save(test_data, self.request_context)

        self.assertEqual(len(form.current_stage.forms[0].errors), 3)

    def test_your_money_other_option_with_valid_data(self):

        form = self._get_your_money_stage()

        test_data = {
            "you_are": "Other",
            "other_details": "woo woo woo",
            "other_pay_amount": "100",
            "other_hardship": False
        }

        form.save(test_data, self.request_context)

        self.assertTrue(form.current_stage.forms[0].is_valid())

    def test_review_stage_has_company_details_block(self):
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": True
            },
            "your_details": {
                "complete": True,
                "skipped": True
            },
            "company_details": {
                "company_name": "TEST COMPANY",
                "company_address": "TEST ADDRESS",
                "name": "TEST NAME",
                "position_in_company": "a director",
                "contact_number": "0800 TEST",
                "email": "test@test.com",
                "complete": True
            },
            "plea": {
                "PleaForms": [
                    {
                        "guilty": "not_guilty",
                        "not_guilty_extra": ""
                    }
                ],
                "complete": True
            },
            "your_money":  {
                "complete": True,
                "skipped": True
            },
            "company_finances": {
                "skipped": True,
                "complete": True
            }
        }

        form = PleaOnlineForms("review", "plea_form_step", test_data)

        form.load(self.request_context)
        response = form.render()

        self.assertContains(response, "<<SHOWCOMPANYDETAILS>>")
        self.assertContains(response, test_data["company_details"]["company_name"])
        self.assertContains(response, test_data["company_details"]["name"])
        self.assertContains(response, test_data["company_details"]["position_in_company"])
        self.assertContains(response, test_data["company_details"]["email"])
        self.assertContains(response, test_data["company_details"]["contact_number"])

        self.assertNotContains(response, "<<SHOWYOURDETAILS>>")
        self.assertNotContains(response, "<<SHOWCOMPANYFINANCES>>")
        self.assertNotContains(response, "<<SHOWINGEXPENSES>>")

    def test_review_stage_has_company_finances_block(self):
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": True
            },
            "your_details": {
                "complete": True,
                "skipped": True
            },
            "company_details": {
                "company_name": "TEST COMPANY",
                "company_address": "TEST ADDRESS",
                "name": "TEST NAME",
                "position_in_company": "a director",
                "contact_number": "0800 TEST",
                "email": "test@test.com",
                "complete": True
            },
            "plea": {
                "PleaForms": [
                    {
                        "guilty": "guilty",
                        "guilty_extra": ""
                    }
                ],
                "complete": True
            },
            "your_money":  {
                "complete": True,
                "skipped": True
            },
            "company_finances": {
                "complete": True
            }
        }

        form = PleaOnlineForms("review", "plea_form_step", test_data)

        form.load(self.request_context)
        response = form.render()

        self.assertContains(response, "<<SHOWCOMPANYDETAILS>>")
        self.assertContains(response, test_data["company_details"]["company_name"])
        self.assertContains(response, test_data["company_details"]["name"])
        self.assertContains(response, test_data["company_details"]["position_in_company"])
        self.assertContains(response, test_data["company_details"]["email"])
        self.assertContains(response, test_data["company_details"]["contact_number"])

        self.assertContains(response, "<<SHOWCOMPANYFINANCES>>")
        self.assertNotContains(response, "<<SHOWYOURDETAILS>>")
        self.assertNotContains(response, "<<SHOWINGEXPENSES>>")

    def test_review_stage_loads(self):
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": False
            },
            "your_details": {
                "complete": True
            },
            "plea": {
                "complete": True
            },
            "your_money":  {
                "complete": True
            }
        }

        form = PleaOnlineForms("review", "plea_form_step", test_data)

        form.load(self.request_context)
        response = form.render()

        self.assertTemplateUsed(response, "plea/review.html")
        self.assertIn("06/AA/0000000/00", response.content)

    def test_complete_stage_loads(self):

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": False
            },
            "your_details": {
                "complete": True
            },
            "plea": {
                "complete": True,
                "PleaForms": [
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    }
                ]
            },
            "your_money":  {
                "complete": True
            },
            "review": {
                "complete": True
            }
        }

        form = PleaOnlineForms("complete", "plea_form_step", test_data)
        fake_request = self.get_request_mock("/plea/complete")
        request_context = RequestContext(fake_request)

        form.load(request_context)
        response = form.render()

        self.assertIn(test_data["case"]["urn"], response.content)

    @patch("apps.plea.email.TemplateAttachmentEmail.send")
    @patch("apps.govuk_utils.forms.messages.add_message")
    def test_email_error_adds_message(self, add_message, send):
        send.side_effect = socket.error("Email failed to send, socket error")

        fake_session = {"case": {}, "your_details": {}, "plea": {"PleaForms": [{}]}, "review": {}}
        fake_session["case"]["date_of_hearing"] = datetime.date(2016, 1, 1)
        fake_session["case"]["urn"] = "06/AA/0000000/00"
        fake_session["case"]["number_of_charges"] = 1
        fake_session["case"]["company_plea"] = False
        fake_session["your_details"]["name"] = "Charlie Brown"
        fake_session["your_details"]["contact_number"] = "07802639892"
        fake_session["your_details"]["email"] = "test@example.org"
        fake_session['your_details']["national_insurance_number"] = "test NI number"
        fake_session['your_details']["driving_licence_number"] = "test driving number"
        fake_session['your_details']["registration_number"] = "test registration number"
        fake_session["plea"]["PleaForms"][0]["guilty"] = "guilty"
        fake_session["plea"]["PleaForms"][0]["guilty_extra"] = "lorem ipsum 1"

        form = PleaOnlineForms("review", "plea_form_step", fake_session)
        form.load(self.request_context)
        form.save({"understand": True, "receive_email": False}, self.request_context)
        form.process_messages({})
        self.assertEqual(add_message.call_count, 1)
        self.assertEqual(add_message.call_args[0][0], {})
        self.assertEqual(add_message.call_args[0][1], 40)

    def test_successful_completion_single_charge(self):
        fake_session = {}
        fake_request = self.get_request_mock("/plea/case")
        request_context = RequestContext(fake_request)

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form = PleaOnlineForms("case", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 1,
                   "company_plea": False},
                  request_context)
        response = form.render()
        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("your_details", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"name": "Charlie Brown",
                   "contact_number": "07802639892",
                   "email": "test@example.org"},
                  request_context)
        response = form.render()
        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("plea", "plea_form_step", fake_session)
        form.load(request_context)

        mgmt_data = {"form-TOTAL_FORMS": "1",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1"})

        form.save(mgmt_data, request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("review", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"understand": "True", "receive_email": False},
                  request_context)
        response = form.render()
        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("complete", "plea_form_step", fake_session)
        form.load(request_context)

        self.assertEqual(fake_session["case"]["date_of_hearing"], hearing_date)
        self.assertEqual(fake_session["case"]["urn"], "06/AA/0000000/00")
        self.assertEqual(fake_session["case"]["number_of_charges"], 1)
        self.assertEqual(fake_session["your_details"]["name"], "Charlie Brown")
        self.assertEqual(fake_session["your_details"]["contact_number"], "07802639892")
        self.assertEqual(fake_session["your_details"]["email"], "test@example.org")
        self.assertEqual(fake_session["plea"]["PleaForms"][0]["guilty"], "guilty")
        self.assertEqual(fake_session["plea"]["PleaForms"][0]["guilty_extra"], "lorem ipsum 1")
        self.assertEqual(fake_session["review"]["understand"], True)

    def test_successful_completion_multiple_charges(self):
        fake_session = {}
        fake_request = self.get_request_mock("/plea/case/")

        request_context = RequestContext(fake_request)
        hearing_date = datetime.date.today()+datetime.timedelta(30)

        form = PleaOnlineForms("case", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"date_of_hearing_0": str(hearing_date.day),
                   "date_of_hearing_1": str(hearing_date.month),
                   "date_of_hearing_2": str(hearing_date.year),
                   "urn_0": "06",
                   "urn_1": "AA",
                   "urn_2": "0000000",
                   "urn_3": "00",
                   "number_of_charges": 2,
                   "company_plea": False},
                  request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("your_details", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"name": "Charlie Brown",
                   "contact_number": "07802639892",
                   "email": "test@example.org"},
                  request_context)

        form = PleaOnlineForms("plea", "plea_form_step", fake_session)
        form.load(request_context)

        mgmt_data = {"form-TOTAL_FORMS": "2",
                     "form-INITIAL_FORMS": "0",
                     "form-MAX_NUM_FORMS": "1000"}

        mgmt_data.update({"form-0-guilty": "guilty",
                          "form-0-guilty_extra": "lorem ipsum 1",
                          "form-1-guilty": "guilty",
                          "form-1-guilty_extra": "lorem ipsum 2"})

        form.save(mgmt_data, request_context)
        response = form.render()

        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("review", "plea_form_step", fake_session)
        form.load(request_context)
        form.save({"understand": "True", "receive_email": False},
                  request_context)
        response = form.render()
        self.assertEqual(response.status_code, 302)

        form = PleaOnlineForms("complete", "plea_form_step", fake_session)
        form.load(request_context)

        self.assertEqual(fake_session["case"]["date_of_hearing"], hearing_date)
        self.assertEqual(fake_session["case"]["urn"], "06/AA/0000000/00")
        self.assertEqual(fake_session["case"]["number_of_charges"], 2)
        self.assertEqual(fake_session["case"]["company_plea"], False)
        self.assertEqual(fake_session["your_details"]["name"], "Charlie Brown")
        self.assertEqual(fake_session["your_details"]["contact_number"], "07802639892")
        self.assertEqual(fake_session["your_details"]["email"], "test@example.org")
        self.assertEqual(fake_session["plea"]["PleaForms"][0]["guilty"], "guilty")
        self.assertEqual(fake_session["plea"]["PleaForms"][0]["guilty_extra"], "lorem ipsum 1")
        self.assertEqual(fake_session["plea"]["PleaForms"][1]["guilty"], "guilty")
        self.assertEqual(fake_session["plea"]["PleaForms"][1]["guilty_extra"], "lorem ipsum 2")
        self.assertEqual(fake_session["review"]["understand"], True)

    def test_guilty_pleas_complete_page_content(self):

        fake_request = self.get_request_mock("/plea/complete")
        request_context = RequestContext(fake_request)

        stage_data = self.test_session_data

        form = PleaOnlineForms("complete", "plea_form_step", stage_data)
        form.load(request_context)

        response = form.render()

        self.assertContains(response, "<<GUILTY>>")

    def test_mixed_pleas_complete_page_content(self):

        fake_request = self.get_request_mock("/plea/complete")
        request_context = RequestContext(fake_request)

        stage_data = self.test_session_data

        stage_data['plea']['PleaForms'][0]['guilty'] = "not_guilty"

        form = PleaOnlineForms("complete", "plea_form_step", stage_data)
        form.load(request_context)

        response = form.render()

        self.assertContains(response, "<<MIXED>>")

    def test_not_guilty_pleas_complete_page_content(self):

        fake_request = self.get_request_mock("/plea/complete")
        request_context = RequestContext(fake_request)

        stage_data = self.test_session_data

        stage_data['plea']['PleaForms'] = [
            {
                'mitigation': 'asdf',
                'guilty': 'not_guilty'
            },
            {
                'mitigation': 'asdf',
                'guilty': 'not_guilty'
            },
            {
                'mitigation': 'asdf',
                'guilty': 'not_guilty'
            }
        ]

        form = PleaOnlineForms("complete", "plea_form_step", stage_data)
        form.load(request_context)

        response = form.render()

        self.assertContains(response, "<<NOTGUILTY>>")

    def test_case_stage_urn_in_session(self):

        urn = "06/AA/0000000/00"

        case = Case()
        case.urn = urn
        case.status = "sent"
        case.save()

        self.session['case'] = dict(urn=urn)

        stages = ['case', 'your_details', 'plea', 'your_money', 'review', 'complete']

        for stage in stages:

            form = PleaOnlineForms(stage, "plea_form_step", self.session)
            form.load(self.request_context)
            form.save({}, self.request_context)

            response = form.render()

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('urn_already_used'))

    def test_urn_not_success_is_not_blocked(self):

        urn = "06/AA/0000000/00"

        case = Case()
        case.urn = urn
        case.status = "network_error"
        case.save()

        self.session['case'] = dict(urn=urn)

        form = PleaOnlineForms("case", "plea_form_step", self.session)
        form.load(self.request_context)
        form.save({}, self.request_context)

        response = form.render()

        self.assertEqual(response.status_code, 200)

    def test_your_finances_employed_hardship_redirects_to_your_expenses(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Employed",
            "employed_your_job": "Window cleaner",
            "employed_take_home_pay_period": "Fortnightly",
            "employed_take_home_pay_amount": "1000",
            "employed_hardship": True
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/your_expenses/')

    def test_your_expenses_redirects_to_review_page(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_expenses", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "hardship_details": "ra ra ra",
            "household_accommodation": "0",
            "household_utility_bills": "0",
            "household_insurance": "100",
            "household_council_tax": "50",
            "other_bill_payers": True,
            "other_tv_subscription": "0",
            "other_travel_expenses": "20",
            "other_telephone": "40",
            "other_loan_repayments": "60",
            "other_court_payments": "30",
            "other_child_maintenance": "50"
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/plea/review/')

    def test_your_finances_employed_no_hardship_redirects_to_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Employed",
            "employed_your_job": "Window cleaner",
            "employed_take_home_pay_period": "Fortnightly",
            "employed_take_home_pay_amount": "1000",
            "employed_hardship": False
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/review/')

    def test_your_finances_self_employed_hardship_redirects_to_your_expenses(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Self-employed",
            "your_job": "Build trains",
            "self_employed_pay_period": "Fortnightly",
            "self_employed_pay_amount": "1000",
            "self_employed_hardship": True
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/your_expenses/')

    def test_your_finances_self_employed_no_hardship_redirects_to_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Self-employed",
            "your_job": "Build trains",
            "self_employed_pay_period": "Fortnightly",
            "self_employed_pay_amount": "1000",
            "self_employed_hardship": False
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/review/')

    def test_your_finances_benefits_hardship_redirects_to_your_expenses(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Receiving benefits",
            "benefits_details": "Some data about my benefits",
            "benefits_dependents": "Yes",
            "benefits_period": "Fortnightly",
            "benefits_amount": "1000",
            "receiving_benefits_hardship": True
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/your_expenses/')

    def test_your_finances_benefits_no_hardship_redirects_to_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Receiving benefits",
            "benefits_details": "Some data about my benefits",
            "benefits_dependents": "Yes",
            "benefits_period": "Fortnightly",
            "benefits_amount": "1000",
            "receiving_benefits_hardship": False
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/review/')

    def test_your_finances_other_hardship_redirects_to_your_expenses(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Other",
            "other_details": "woo woo woo",
            "other_pay_amount": "100",
            "other_hardship": True
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/your_expenses/')

    def test_your_finances_other_no_hardship_redirects_to_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_expenses")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Other",
            "other_details": "woo woo woo",
            "other_pay_amount": "100",
            "other_hardship": False
        }

        form.save(test_data, request_context)

        response = form.render()

        self.assertEqual(response.url, '/plea/review/')

    def test_hardship_calculations_on_review_page(self):

        session_data = self.test_session_data
        session_data['your_money']['hardship'] = True

        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_expenses", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "hardship_details": "ra ra ra",
            "household_accommodation": "0",
            "household_utility_bills": "0",
            "household_insurance": "100",
            "household_council_tax": "50",
            "other_bill_payers": True,
            "other_tv_subscription": "0",
            "other_travel_expenses": "20",
            "other_telephone": "40",
            "other_loan_repayments": "60",
            "other_court_payments": "30",
            "other_child_maintenance": "50"
        }

        form.save(test_data, request_context)

        form = PleaOnlineForms("review", "plea_form_step", session_data)

        form.load(request_context)

        response = form.render()

        self.assertContains(response, '150')
        self.assertContains(response, '200')
        self.assertContains(response, '350')

    def test_hardship_on_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Other",
            "other_details": "woo woo woo",
            "other_pay_amount": "100",
            "other_hardship": True
        }

        form.save(test_data, request_context)

        form = PleaOnlineForms("review", "plea_form_step", session_data)

        form.load(request_context)

        response = form.render()

        self.assertContains(response, '<<SHOWINGEXPENSES>>')

    def test_no_hardship_review(self):

        session_data = self.test_session_data
        fake_request = self.get_request_mock("/plea/your_money")
        request_context = RequestContext(fake_request)

        form = PleaOnlineForms("your_money", "plea_form_step", session_data)

        form.load(request_context)

        test_data = {
            "you_are": "Other",
            "other_details": "woo woo woo",
            "other_pay_amount": "100",
            "other_hardship": False
        }

        form.save(test_data, request_context)

        form = PleaOnlineForms("review", "plea_form_step", session_data)

        form.load(request_context)

        response = form.render()

        self.assertNotContains(response, '<<SHOWINGEXPENSES>>')


class TestYourExpensesStage(TestMultiPleaFormBase):

    def setUp(self):

        hearing_date = datetime.date.today()+datetime.timedelta(30)

        self.fake_request = self.get_request_mock("/plea/your_money")
        self.request_context = RequestContext(self.fake_request)

        self.test_data = {
            "case": {
                "complete": True,
                "date_of_hearing": hearing_date.strftime('%Y-%m-%d'),
                "urn": "06/AA/0000000/00",
                "number_of_charges": 1,
                "company_plea": False
            },
            "your_details": {
                "complete": True
            },
            "plea": {
                "complete": True,
                "PleaForms": [
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    },
                    {
                        "guilty": "guilty",
                        "guilty_extra": "something"
                    }
                ]
            },
            "your_money":  {
                "complete": True
            },
            "your_expenses": {

            },
            "review": {
                "complete": True
            }
        }

    def test_your_expenses_form_requires_validation(self):

        form = PleaOnlineForms("your_expenses", "plea_form_step", self.test_data)

        form.load(self.request_context)

        form.save({}, self.request_context)

        response = form.render()

        self.assertEquals(response.status_code, 200)
