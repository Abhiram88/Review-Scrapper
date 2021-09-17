import os

from flask import Flask, redirect, url_for
import pandas as pd
from flask import render_template, request, jsonify
#from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import collections
import copy
from jinja2 import Environment
from pymongo import MongoClient


app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
review_db = MongoClient()
conn = review_db['review_scrapper']

#flipkart_url = 'https://www.flipkart.com/search?q=' + 'nokia'



@app.route('/')
def index():
    #return redirect(url_for('home'))
    return redirect(url_for('display_review'))

@app.route('/start')
def start():
    return render_template('scrapper.html')


@app.route('/home')
def home():
    review_db = MongoClient()
    conn = review_db['review_scrapper']

    mobile_models = []
    if conn.reviews_collection:
        review = conn.reviews_collection
        review_results = review.find()
        for item in review_results:
            #mobile_models.append(item['product'].title())
            mobile_models.append(item)
    else:
        return render_template('start.html')

    return render_template('home.html', models=mobile_models)


@app.route('/display/<string:keys>')
def display(keys):
    all_reviews = {}
    print(keys)
    for product in conn.reviews_collection.find():
        for key in product['comments'].keys():
            if key == keys:
                all_reviews[keys] = product['comments'][key]
    #print(all_reviews)
    return render_template('display.html', result=all_reviews)





@app.route('/display_review')
def display_review():
    return render_template('display_review.html')


@app.route('/scrapper', methods=['POST'])
def scrapper():
    reviews_list = collections.defaultdict(dict)
    search_query = request.form['prod']
    search_query = search_query.replace(" ", '%20')
    print(search_query)

    products, product_info = base_content(search_query)
    reviews_dataset = main_prog(product_info, search_query)
    #test(reviews_dataset)

    product_reviews = collections.defaultdict(dict)

    for i, v in reviews_dataset.items():
        space = ''
        if isinstance(v, list):
            space += "".join(v)
            product_reviews[i] = [space]
        else:
            product_reviews[i] = [v]
    print("******************")
    print(reviews_list)


    #return 'hello'
    return render_template('display.html', result=product_reviews, name=search_query)

@app.route('/test')
def test(data):
    print(data)
    for key, val in data.items():
        print(key)
        print(val)




@app.route('/index')
def display_page():
    reviews_data = main_prog()
    return render_template('index.html', reviews=reviews_data)



@app.route('/error')
def error():
    return render_template('error.html')




def base_content(search_string):
    products = []

    flipkart_url = 'https://www.flipkart.com/search?q='+search_string+'+&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'

    #print(flipkart_url)
    page = requests.get(flipkart_url)
    page_beautified = bs(page.content, 'html.parser')

    products = []
    links = []
    bigboxes = page_beautified.find_all("div", {"class": "bhgxx2 col-12-12"})
    #print(bigboxes[2:5])

    boxes_limit = len(bigboxes[:-1])
    print(boxes_limit)

    for linc in bigboxes[2:boxes_limit]:
       # divs = linc.div.div
        #print(linc)
        anchor = linc.find_all('a', title=True, href=True)
        img = linc.find_all('img')
        #print(anchor)
        for name in anchor:
            print(name)
            products.append(name['title'])
            links.append(name['href'])
    #print(products)
    #print(links)



    product_links = {}
    for i, j in zip(products, links):
        if i == None:
            continue
        else:
            #print(i)
            #print(j)
            product_links[i] = j
#    print(product_links)

    return products, product_links



def main_prog(product_info, search_query):
    all_reviews = []
    product_reviews = collections.defaultdict(dict)
    #product_reviews['comments'] = {}
    #product_reviews['product'] = search_query
    for key, val in product_info.items():
        model = key
        #print(key)
        product = get_product_info(val)
        review_page = find_review_page(product)

        if len(review_page) < 5:
            for i in review_page:
                #product_reviews['comments'][key] = i  need for mongo
                product_reviews[key] = i
                #print(i)
        else:
            review_pages = get_review_links(review_page)
            search_query = search_query.replace("+", " ")
            #product_reviews['product'] = search_query       important for MongoDB
            #product_reviews['comments'][key] = get_all_reviews(review_pages)   important for MongoDB
            product_reviews[key] = get_all_reviews(review_pages)   #need to remove for mongo

        ''' if review_page != 'skip':
            review_pages = get_review_links(review_page)
            product_reviews['product'] = search_query
            product_reviews['comments'][key] = get_all_reviews(review_pages)
        else:
            continue '''
    #   print("--------------")
   # print(product_reviews)
    return product_reviews


def get_product_info(product_link):
    base_url = 'https://www.flipkart.com'
    product = requests.get(base_url + product_link)
    product_page = bs(product.content, 'html.parser')

    return product_page


def find_review_page(review_link):

    review_page = review_link.find_all('div', {'class': ['col _39LH-M', 'col _3cycCZ']})
    less_review_pages = review_link.find_all('div', {'class': '_2t8wE0'})
    return_page = []
    less_reviews = []

    for page in review_page:
        for review_link in page.find_all('a'):
            return_page.append(review_link['href'])

    if len(return_page) < 5:
        for i in less_review_pages:
            less_reviews.append(i.text)
            print(i.text)
        return less_reviews
    else:
        return return_page[-1]



def get_review_links(page):
    #print(page)
    base_url = 'https://www.flipkart.com'
    print("------------")
    #print(page[0])
    page = base_url + page

    review_link = requests.get(page)
    review_link_cleaned = bs(review_link.content, 'html.parser')

    review_pages = []
    comm = review_link_cleaned.find_all('div', {'class': '_2zg3yZ _3KSYCY'})

    for link in comm:
        for li in link.find_all('a'):
            review_pages.append(li['href'])
    #print("review pages" + str(len(review_pages)))
    return review_pages


def get_all_reviews(links):
    base_url = 'https://www.flipkart.com'
    reviews_set = []

    for i in links:
        page = base_url + i

        get_page = requests.get(page)
        page_cleaned = bs(get_page.content, 'html.parser')

        reviews = page_cleaned.find_all('div', {'class': 'qwjRop'})
        for link in reviews:
            reviews_set.append(link.text)
            #print(link.text)

    #print(reviews_set)
    #print(len(reviews_set))
    return reviews_set



#reviews_collection = main_prog()
#print(reviews_collection)


if __name__ == '__main__':
   app.run(debug = True)
   #jinja_env = Environment(extensions=['jinja2.ext.loopcontrol'])
   app.jinja_env.add_extension('jinja2.ext.loopcontrols')
