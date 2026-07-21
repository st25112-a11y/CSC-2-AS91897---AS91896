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
    
def init_db():
    conn = sqlite3.connect('dream_pizza.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            contact TEXT,
            order_type TEXT,
            address TEXT,
            total REAL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            item_name TEXT,
            size TEXT,
            quantity INTEGER,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

    return render_template('menu.html', active_page='menu', classic_pizzas=classic_pizzas, gourmet_pizzas=gourmet_pizzas, sides=sides, cart=cart)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    return render_template('order_history.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/invoice')
def invoice():

    last_order = session.get('last_order', {})

    if not last_order:
        flash('No order found. Please place an order first.')
        return redirect(url_for('menu'))
    
    cart = last_order.get('cart', [])
    customer_name = last_order.get('name', 'Customer')
    
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    invoice_number = f"INV_{customer_name.replace(' ', '_')}"
    invoice_filename = f"{invoice_number}.txt"
    return render_template('invoice.html', invoice_number=invoice_number, name=customer_name, invoice_date=invoice_date, cart=cart)

@app.route('/cart', methods=['GET', 'POST'])
def cart():

    if request.method == 'POST':
        item = request.form.get('item')
        size = request.form.get('size')
        quantity = int(request.form.get('quantity', 1))
        instructions = request.form.get('instructions')

        if item:
            cart = session.get('cart', [])
            current_total_quantity = sum(i['quantity'] for i in cart)
            classic_pizzas, gourmet_pizzas, sides = load_data()
            unit_price = 0

            if item in classic_pizzas:
                unit_price = float(classic_pizzas[item]['price'])
            elif item in gourmet_pizzas:
                unit_price = float(gourmet_pizzas[item]['price'])
            elif item in sides:
                unit_price = float(sides[item]['price'])

            cart = session.get('cart', [])
            current_total_quantity = sum(i['quantity'] for i in cart)

            if current_total_quantity + quantity > 5:
                remaining_quantity = 5 - current_total_quantity
                if remaining_quantity > 0:
                    flash(f'You can only add {remaining_quantity} more to your cart')
                else:
                    flash('You have reached the maximum quantity for this item in your cart')
                return redirect(url_for('menu'))

            cart_item = {
                'item': item,
                'size': size,
                'quantity': quantity,
                'instructions': instructions,
                'price': unit_price
            }

            cart.append(cart_item)
            session['cart'] = cart
            flash(f'Added {quantity}x {size} {item} to your cart')
            return redirect(url_for('menu'))
    return redirect(url_for('menu'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    item = request.form.get('item')
    size = request.form.get('size')
    cart = session.get('cart', [])
    cart = [i for i in cart if not (i['item'] == item and i['size'] == size)]
    session['cart'] = cart
    flash(f'Removed {size} {item} from your cart')
    return redirect(url_for('menu'))

def total_price(cart):
    classic_pizzas, gourmet_pizzas, sides = load_data()
    total = 0
    for item in cart:
        if item['item'] in classic_pizzas:
            price = float(classic_pizzas[item['item']]['price'])
        elif item['item'] in gourmet_pizzas:
            price = float(gourmet_pizzas[item['item']]['price'])
        elif item['item'] in sides:
            price = float(sides[item['item']]['price'])
        else:
            price = 0
        total += price * item['quantity']
    return total

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])

    if not cart:
        flash('Your cart is empty. Please add items to your cart before checking out.')
        return redirect(url_for('menu'))

    if request.method == 'POST':
        del_or_pickup = request.form.get('del_or_pickup')
        address = request.form.get('address')
        customer_name = request.form.get('name')
        contact = request.form.get('contact')

        conn = sqlite3.connect('dream_pizza.db')
        c = conn.cursor()

        c.execute('''
            INSERT INTO orders (customer_name, contact, order_type, address, total)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_name, contact, del_or_pickup, address, total_price(cart)))

        order_id = c.lastrowid

        for item in cart:
            c.execute('''
                INSERT INTO order_items (order_id, item_name, size, quantity)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item['item'], item['size'], item['quantity']))
        
        conn.commit()
        conn.close()

        session['last_order'] = {
        'cart': cart,
        'name': customer_name
        }

        session.pop('cart', None)
        flash('Order has been placed')
        return redirect(url_for('invoice'))

    return render_template('checkout.html', active_page='checkout', cart=cart, total=total_price(cart))

if __name__ == '__main__':
    app.run(debug=True)