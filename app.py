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

    return render_template('menu.html', active_page='menu', classic_pizzas=classic_pizzas, gourmet_pizzas=gourmet_pizzas, sides=sides)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        item = request.form.get('item')
        size = request.form.get('size')
        quantity = int(request.form.get('quantity'))
        del_or_pickup = request.form.get('del_or_pickup')
        address = request.form.get('address')
        customer_name = request.form.get('customer_name')
        contact = request.form.get('contact')
        instructions = request.form.get('instructions')

        if item:
            cart_item = {
                'item': item,
                'size': size,
                'quantity': quantity,
                'del_or_pickup': del_or_pickup,
                'address': address,
                'customer_name': customer_name,
                'contact': contact,
                'instructions': instructions
            }
            cart = session.get('cart', [])
            cart.append(cart_item)
            session['cart'] = cart
            flash(f'Added {quantity}x {size} {item} to your cart')
        return redirect(url_for('menu'))
    
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty. Please add items to your cart before checking out.')
        return redirect(url_for('menu'))

if __name__ == '__main__':
    app.run(debug=True)