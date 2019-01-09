from django.core.management.base import BaseCommand
from ...models import UserRatingAggregate, UserRating
from ...nlp import RatingScorer


class Command(BaseCommand):
    help = "Analyse feedback comments"

    def handle(self, *args, **options):
        r_scorer = RatingScorer()
        print r_scorer.get_positive_words()
        print r_scorer.get_negative_words()