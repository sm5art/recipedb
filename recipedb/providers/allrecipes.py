import requests
from bs4 import BeautifulSoup
import gzip
import functools
from multiprocessing.dummy import Pool
import time

from recipedb.db import get_db
from recipedb.utils.logging import logger_factory

THREADS = 5
TEMP = "temp.gz"
db = get_db()
logger = logger_factory(__name__)
count = 0


def get_soup(html_str, parser='html.parser'):
    return BeautifulSoup(html_str, parser)


def get_request(endpoint):
    return requests.get(endpoint)


def get_sitemaps():
    gs_index = get_soup(get_request(
        'https://www.allrecipes.com/gsindex.xml').text, parser='xml')
    sitemaps = [s.loc.contents[0] for s in gs_index.find_all('sitemap')]
    return sitemaps


def get_sitemap_xml(sitemap):
    sitemap = get_request(sitemap)
    with open(TEMP, 'wb') as f:
        f.write(sitemap.content)
    with gzip.open(TEMP, 'rb') as f:
        file_content = f.read()
    return get_soup(file_content, parser='xml')


def get_recipes_from_sitemap(sitemap):
    sitemap1 = get_sitemap_xml(sitemap)
    url_tags = sitemap1.find_all('url')
    return [e.loc.contents[0] for e in url_tags]


def get_recipe_list():
    sitemaps = get_sitemaps()
    sitemaps_excluded = list(sitemaps)
    sitemaps_excluded.pop(4)  # removing the one wout recipes
    recipes = [get_recipes_from_sitemap(sitemap)
               for sitemap in sitemaps_excluded]
    return functools.reduce(lambda a, b: a+b, recipes)


def get_recipe_data(soup):
    title = soup.find(id="recipe-main-content").text
    rating = float(soup.find(class_="rating-stars")['data-ratingstars'])
    reviews_count = soup.find(class_="review-count").text.split()[0]
    categories = list(map(lambda x: x.text.strip(), soup.find_all(
        class_="toggle-similar__title")[2:]))
    ingredients = [e.text for e in filter(lambda x: x.get(
        'itemprop') == "recipeIngredient", soup.find_all(class_="recipe-ingred_txt"))]
    directions = [e.text.strip() for e in soup.find_all(
        class_="recipe-directions__list--item")[:-1]]
    image = soup.find(class_="rec-photo").get('src')
    data = {'title': title, 'image': image, 'categories': categories, 'rating': rating,
            'review_count': reviews_count, "ingredients": ingredients, "directions": directions}
    return data


def process_recipe(x):
    global count
    error = None
    data = None
    try:
        soup = get_soup(get_request(x).text)
        data = get_recipe_data(soup)
    except Exception as e:
        error = e
        logger.info(error)
        logger.info("OTHER ALLRECIPES VERSION %s" % x)
    if error is not None:
        error = repr(error)
    db.allrecipes.insert_one({"error": error, "src": x, "data": data})
    count += 1
    logger.info("%s  %s/%s recipes" % (x, count, N))


def main():
    global N
    recipes = get_recipe_list()
    N = len(recipes)
    start_time = time.time()
    with Pool(THREADS) as p:
        p.map(process_recipe, recipes)
    logger.info("Scraped %d recipes in %d seconds" %
                (N, time.time()-start_time))


if __name__ == "__main__":
    main()
