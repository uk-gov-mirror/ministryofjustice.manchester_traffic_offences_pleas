from .models import UserRating
import re


def safe_div(x, y):
    if y == 0:
        return 0
    return float(x)/ float(y)


def split_iter(message):
    """
    Splits a message into a generator of it's constituent words
    :param message:
    :return generator of message words:
    """
    return (x.group(0) for x in re.finditer(r"[A-Za-z']+", message))


def prepare_word_array(word_array, word_limit):
    blank_word_tuple = ("", 0)
    while len(word_array) < word_limit:
        word_array.append(blank_word_tuple)
    return word_array


def handle_new_score(word_array, new_word_tuple):
    where_to_add = None
    should_update = False
    for i, existing_word_tuple in enumerate(word_array):
        if new_word_tuple[1] > existing_word_tuple[1]:
            should_update = True
            where_to_add = i + 1
    if should_update:
        return amend_word_array(word_array, new_word_tuple, where_to_add)


def amend_word_array(word_array, new_word_tuple, where_to_add):
    word_array.insert(where_to_add, new_word_tuple)
    word_array.pop(0)
    return word_array


class RatingScorer:
    rating_dict = None
    words_and_ratings_count_dict = {}
    rating_totals = [0, 0, 0, 0, 0]
    rating_multiplication_factors = [-1.5, -1, 0, 1, 1.5]
    ratings = None
    positive_word_array = []
    negative_word_array = []
    word_limit = 5

    def __init__(self, start_date=None, end_date=None):
        # self.ratings = UserRating.objects.filter(last_update__gte=start_date).filter(last_update__lt=end_date)
        self.ratings = UserRating.objects.filter(comments__isnull=False, service_rating__isnull=False)
        self.rating_dict = {}
        self.positive_word_array = prepare_word_array(self.positive_word_array, self.word_limit)
        self.negative_word_array = prepare_word_array(self.negative_word_array, self.word_limit)
        self.ratings_to_dict()
        self.find_important_words()

    def ratings_to_dict(self):
        """
        Prepares a dict of every distinct word from all ratings and logs the count of their
         respective appearances in ratings for each service rating score.
         E.g. In the dictionary self.words_and_ratings_count_dict,
         {'hello': [0,1,4,3,1]} would infer that the word hello has been used in 0 very dissatisfied,
         1 dissatisfied, 4 neutral, 3 satisfied and 1 very satisfied service ratings.
        """
        for rating in self.ratings:
            rating_words = split_iter(str(rating.comments))
            for word in rating_words:
                if word not in self.words_and_ratings_count_dict:
                    self.add_new_word_to_dict(word)
                self.add_word_to_counts(word, rating.service_rating)

    def add_new_word_to_dict(self, word):
        self.words_and_ratings_count_dict[word] = [0, 0, 0, 0, 0]

    def add_word_to_counts(self, word, service_rating):
        self.rating_totals[service_rating - 1] += 1
        self.words_and_ratings_count_dict[word][service_rating - 1] += 1

    def find_important_words(self):
        """
        Based on the appearance of a word in UserRatings of varying service_ratings, a score is calculated for each
        word. Based on these words, the n (self.word_limit) most positive and negative words are recorded.
        """
        for word, word_scores in self.words_and_ratings_count_dict.iteritems():
            self.calculate_word_score(word, word_scores)

    def calculate_word_score(self, word, word_scores):
        score = 0
        for index in range(4):
            score += self.rating_score_contribution(word_scores, index)
        current_tuple = (word, score)
        self.save_top_five_scores(current_tuple)

    def rating_score_contribution(self, word_scores, index):
        term_frequency = safe_div(word_scores[index], self.rating_totals[index])
        rating_score_contribution = term_frequency * self.rating_multiplication_factors[index]
        return rating_score_contribution

    def save_top_five_scores(self, word_tuple):
        if word_tuple[1] > 0:
            self.positive_word_array = handle_new_score(self.positive_word_array, word_tuple)
        if word_tuple[1] < 0:
            neg_tuple = (word_tuple[0], abs(word_tuple[1]))
            self.negative_word_array = handle_new_score(self.negative_word_array, neg_tuple)

    def get_positive_words(self):
        return self.positive_word_array

    def get_negative_words(self):
        return self.negative_word_array
