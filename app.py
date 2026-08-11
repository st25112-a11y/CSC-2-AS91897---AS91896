import datetime
import json
import sqlite3
import random

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
    cart = session.get('cart', [])
    classic_pizzas, gourmet_pizzas, sides = load_data()

    all_pizzas = {**classic_pizzas, **gourmet_pizzas}

    feature_deal_pizza = random.choice(list(all_pizzas.keys()))
    feature_deal_side = random.choice(list(sides.keys()))

    pizza_price = float(all_pizzas[feature_deal_pizza].get('price', 0))
    side_price = float(sides[feature_deal_side].get('price', 0))
    feature_deal_price = pizza_price + (side_price * 0.8)

    feature_pizza_size = random.choice(["Small", "Medium", "Large"])
    feature_side_size = random.choice(["Small", "Medium", "Large"])

    popular_pizzas, popular_gourmet_pizzas, popular_sides = get_popular_items()

    return render_template('index.html', active_page='index', feature_deal=feature_deal_pizza, feature_deal_price=feature_deal_price, feature_pizza_size=feature_pizza_size, feature_side_size=feature_side_size, cart=cart, popular_pizzas=popular_pizzas, popular_gourmet_pizzas=popular_gourmet_pizzas, popular_sides=popular_sides, feature_deal_side=feature_deal_side)

@app.route('/add_featured_deal', methods=['POST'])
def add_featured_deal():
    pizza = request.form.get('pizza')
    pizza_size = request.form.get('pizza_size')
    side = request.form.get('side')
    side_size = request.form.get('side_size')

    cart = session.get('cart', [])
    
    cart.append({
        'item': pizza,
        'size': pizza_size,
        'quantity': 1,
        'instructions': 'Featured Deal',
        'is_deal': True 
    })
    
    cart.append({
        'item': side,
        'size': side_size,
        'quantity': 1,
        'instructions': 'Featured Deal',
        'is_deal': True 
    })
    
    session['cart'] = cart
    flash('Featured deal added directly to your cart!')
    return redirect(url_for('index'))

def get_popular_items(limit=3):
    conn = sqlite3.connect('dream_pizza.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT item_name, SUM(quantity) AS total_ordered
        FROM order_items
        GROUP BY item_name
        ORDER BY total_ordered DESC
    ''')
    results = c.fetchall()
    conn.close()

    classic_pizzas, gourmet_pizzas, sides = load_data()

    popular_pizzas = []
    popular_gourmet_pizzas = []
    popular_sides = []

    for row in results:
        name = row['item_name']
        if name in classic_pizzas and len(popular_pizzas) < limit:
            popular_pizzas.append({'name': name, 'total_ordered': row['total_ordered'], **classic_pizzas[name]})
        elif name in gourmet_pizzas and len(popular_gourmet_pizzas) < limit:
            popular_gourmet_pizzas.append({'name': name, 'total_ordered': row['total_ordered'], **gourmet_pizzas[name]})
        elif name in sides and len(popular_sides) < limit:
            popular_sides.append({'name': name, 'total_ordered': row['total_ordered'], **sides[name]})

    return popular_pizzas, popular_gourmet_pizzas, popular_sides

@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route('/menu')
def menu():
    cart = session.get('cart', [])
    classic_pizzas, gourmet_pizzas, sides = load_data()
    open_item = request.args.get('item')

    return render_template('menu.html', active_page='menu', classic_pizzas=classic_pizzas, gourmet_pizzas=gourmet_pizzas, sides=sides, cart=cart, open_item=open_item)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    conn = sqlite3.connect('dream_pizza.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''
        SELECT orders.id, orders.customer_name, orders.total, orders.order_date,
               order_items.item_name, order_items.size, order_items.quantity
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        ORDER BY orders.order_date DESC
    ''')

    orders = c.fetchall()
    conn.close()

    return render_template('order_history.html', orders=orders)

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
    total = total_price(cart)
    return render_template('invoice.html', invoice_number=invoice_number, name=customer_name, invoice_date=invoice_date, cart=cart, total=total)

@app.route('/cart', methods=['GET', 'POST'])
def cart():

    if request.method == 'POST':
        item = request.form.get('item')
        size = request.form.get('size')
        quantity = int(request.form.get('quantity', 1))
        instructions = request.form.get('instructions')

        if item:
            cart = session.get('cart', [])
            classic_pizzas, gourmet_pizzas, sides = load_data()
            unit_price = 0
            item_type = None

            if item in classic_pizzas:
                unit_price = float(classic_pizzas[item]['price'])
                item_type = 'pizza'
            elif item in gourmet_pizzas:
                unit_price = float(gourmet_pizzas[item]['price'])
                item_type = 'pizza'
            elif item in sides:
                unit_price = float(sides[item]['price'])
                item_type = 'side'

            current_pizza_qty = 0
            current_sides_qty = 0


            for i in cart:
                if i['item'] in classic_pizzas or i['item'] in gourmet_pizzas:
                    current_pizza_qty += i['quantity']
                elif i['item'] in sides:
                    current_sides_qty += i['quantity']

            if item_type == 'pizza':
                if current_pizza_qty + quantity > 5:
                    remaining_quantity = 5 - current_pizza_qty
                    if remaining_quantity > 0:
                        flash(f'You can only add {remaining_quantity} more pizzas to your cart')
                    else:
                        flash('You have reached the maximum quantity of pizzasin your cart')
                    return redirect(url_for('menu'))

            elif item_type == 'side':
                if current_sides_qty + quantity > 5:
                    remaining_quantity = 5 - current_sides_qty
                    if remaining_quantity > 0:
                        flash(f'You can only add {remaining_quantity} more sides to your cart')
                    else:
                        flash('You have reached the maximum quantity of sides in your cart')
                    return redirect(url_for('menu'))

            item_found = False
            for existing_item in cart:
                if (existing_item['item'] == item
                    and existing_item['size'] == size
                    and existing_item['instructions'] == instructions):

                    existing_item['quantity'] += quantity
                    item_found = True
                    break

            if not item_found:
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
            if item.get('is_deal'):
                price *= 0.8
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

        classic_pizzas, gourmet_pizzas, sides = load_data()

        for item in cart:
            item_name = item['item']
            qty_ordered = item['quantity']

            if item_name in classic_pizzas:
                classic_pizzas[item_name]['stock'] -= qty_ordered
                if classic_pizzas[item_name]['stock'] < 0:
                    classic_pizzas[item_name]['stock'] = 0

            elif item_name in gourmet_pizzas:
                gourmet_pizzas[item_name]['stock'] -= qty_ordered
                if gourmet_pizzas[item_name]['stock'] < 0:
                    gourmet_pizzas[item_name]['stock'] = 0

            elif item_name in sides:
                sides[item_name]['stock'] -= qty_ordered
                if sides[item_name]['stock'] < 0:
                    sides[item_name]['stock'] = 0

        with open('data/classic_pizzas.json', 'w') as f:
            json.dump(classic_pizzas, f, indent=4)
        with open('data/gourmet_pizzas.json', 'w') as f:
            json.dump(gourmet_pizzas, f, indent=4)
        with open('data/sides.json', 'w') as f:
            json.dump(sides, f, indent=4)

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