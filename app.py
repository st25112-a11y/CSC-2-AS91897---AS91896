import datetime
import json
import sqlite3

from flask import Flask, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'key'

def load_data():
    try:
        with open('data/classic_pizzas.json') as f:
            classic_pizzas = json.load(f)
        with open('data/gourmet_pizzas.json') as f:
            gourmet_pizzas = json.load(f)
        with open('data/sides.json') as f:
            sides = json.load(f)
        return classic_pizzas, gourmet_pizzas, sides
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading data: {e}")
        return {}, {}, {}

@app.route('/')
def index():
    return render_template('index.html', active_page='index')

@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route('/menu')
def menu():
    cart = session.get('cart', [])
    classic_pizzas, gourmet_pizzas, sides = load_data()
    menu_items = []

    for name, details in classic_pizzas.items():
        menu_items.append({
            "name": name,
            "price": details["price"],
            "stock": details["stock"]
        })

    for name, details in gourmet_pizzas.items():
        menu_items.append({
            "name": name,
            "price": details["price"],
            "stock": details["stock"]
        })

    for name, details in sides.items():
        menu_items.append({
            "name": name,
            "price": details["price"],
            "stock": details["stock"]
        })

    return render_template('menu.html', active_page='menu', menu_items=menu_items)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == '__main__':
    app.run(debug=True)