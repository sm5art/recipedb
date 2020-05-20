import functools
import pandas as pd
import numpy as np
from multiprocessing import Pool
from fractions import Fraction
import time
from fuzzywuzzy import fuzz

from recipedb.db import get_db
from recipedb.utils.logging import logger_factory

THREADS = 20
THRESHOLD = 75
db = get_db()
logger = logger_factory(__name__)
food_base = list(db.FoodBase.find())
unit_terms = list(db.UnitTerms.find())
count = 0


def split_text_into_words(raw_text):
    return list(map(lambda x: x.strip().replace('(', '').replace(')', ''), raw_text.split()))


def parse_and_separate_units(raw_ingred_text):
    terms = split_text_into_words(raw_ingred_text)
    unit = None
    i = 0
    found = False
    for term in terms:
        for other_term in unit_terms:
            ratio = fuzz.ratio(term, other_term['text'])
            if ratio > THRESHOLD:
                unit = other_term
                found = True
        if found:
            break
        i += 1
    if found:
        terms.pop(i)
        qty = None
        while i >= 0:
            try:
                qty = float(Fraction(terms[i]))
                terms.pop(i)
                break
            except Exception:
                pass
            i = i - 1
        units = {'qty': qty, "unit": unit}
    else:
        units = None
    return units, ' '.join(terms)


def match_ingredient(ingred):
    matches = list(map(lambda x: fuzz.ratio(x['text'], ingred), food_base))
    return food_base[np.argmax(matches)]


def match_ingredients(ingredients):
    output = []
    for ingred in ingredients:
        unit, separated_text = parse_and_separate_units(ingred)
        match = match_ingredient(separated_text)
        output.append({"unit": unit, "match": match})
    return output


def process_recipe(recipe):
    global count
    matches = match_ingredients(recipe['data']['ingredients'])
    db.matched_recipes.insert_one(
        {"recipe_id": recipe['_id'], "matches": matches})
    count += 1
    logger.info("Matched recipe %d/%d" % (count, N))


def main():
    global N
    recipes = list(db.allrecipes.find({"error": {"$eq": None}}))
    N = len(recipes)
    start_time = time.time()
    logger.info("Beginning matching job with %d recipes" % len(recipes))
    with Pool(THREADS) as p:
        p.map(process_recipe, recipes)
    logger.info("Processed %d recipes in %f seconds" %
                (N, time.time()-start_time))


if __name__ == "__main__":
    main()
