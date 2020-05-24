from recipedb.db import get_db
import numpy as np


class Preprocessor(object):
    def __init__(self):
        db = get_db()
        self.matched_recipes = list(db.matched_recipes.find())
        self.food_base = list(db.FoodBase.find())
        self.ingredient_features, self.ingredient_features_indices, self.n_features = self.prepare_features(
            self.food_base)
        self.unit_base = list(db.UnitBase.find())
        self.unit_conversion_dict = {}
        for unit in self.unit_base:
            self.unit_conversion_dict[unit['unit_id']] = unit['conversion']

    def convert_unit_to_base(self, unit_id, qty):
        return self.unit_conversion_dict[unit_id]*qty

    def prepare_features(self, food_base):
        ingredient_features = list(map(lambda x: x['text'], self.food_base))
        ingredient_features.sort()
        ingredient_features_indices = {}
        i = 0
        for feature in ingredient_features:
            ingredient_features_indices[feature] = i
            i += 1
        return ingredient_features, ingredient_features_indices, len(ingredient_features)

    def process_matched_recipe(self, recipe):
        Y = np.zeros(self.n_features)
        matches = recipe['matches']
        for match in matches:
            unit = match['unit']
            matched_text = match['match']['text']
            if unit is not None:
                if unit['qty'] is None:
                    qty = 1
                else:
                    qty = unit['qty']
                converted_amount = self.convert_unit_to_base(
                    unit['unit']['unit_id'], qty)
            else:
                converted_amount = 1
            Y[self.ingredient_features_indices[matched_text]] = converted_amount
        return Y
