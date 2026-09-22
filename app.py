import datetime
import json
import sqlite3
import random
import time

from flask import Flask, jsonify, render_template, request, session, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = 'key'

def load_data():
    """
    Reads the menu items from JSON files (classic pizzas, gourmet pizzas, and sides).
    Returns them as three separate dictionaries. If a file is missing or corrupted, 
    it catches the error and returns empty dictionaries to prevent the app from crashing.
    """
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
    """
    Initializes the SQLite database. It creates two tables if they don't already exist:
    1. 'orders': Stores overall customer order info (name, address, total price).
    2. 'order_items': Stores the individual pizzas/sides belonging to a specific order.
    """
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

active_deal = {
    "pizza": None,
    "side": None,
    "pizza_size": None,
    "side_size": None,
    "price": 0,
    "expires_at": 0
}

def get_or_create_deal():
    """
    Checks if the current featured deal timer has expired. 
    If it has, it randomly selects a new pizza and side from the JSON data, 
    calculates a discounted price (20% off the side), and resets the 60-second timer.
    Returns the active deal dictionary.
    """
    global active_deal
    current_time = int(time.time())
    
    if current_time > active_deal["expires_at"]:
        classic_pizzas, gourmet_pizzas, sides = load_data()
        all_pizzas = {**classic_pizzas, **gourmet_pizzas}
        
        active_deal["pizza"] = random.choice(list(all_pizzas.keys()))
        active_deal["side"] = random.choice(list(sides.keys()))
        active_deal["pizza_size"] = random.choice(["Small", "Medium", "Large"])
        active_deal["side_size"] = random.choice(["Small", "Medium", "Large"])
        
        pizza_price = float(all_pizzas[active_deal["pizza"]].get('price', 0))
        side_price = float(sides[active_deal["side"]].get('price', 0))
        active_deal["price"] = pizza_price + (side_price * 0.8)
        
        active_deal["expires_at"] = current_time + 60 
        
    return active_deal

@app.route('/api/get_deal')
def api_get_deal():
    """
    An API endpoint that returns the current featured deal as JSON data.
    Used by the frontend JavaScript to update the deal without refreshing the page.
    """
    return jsonify(get_or_create_deal())

@app.route('/')
def index():
    """
    Renders the homepage. It fetches the user's cart, gets the current active 
    featured deal, calculates the most popular items to display, and passes 
    all this data to 'index.html'.
    """
    cart = session.get('cart', [])
    current_deal = get_or_create_deal()
    popular_pizzas, popular_gourmet_pizzas, popular_sides = get_popular_items()

    return render_template('index.html', 
        active_page='index', 
        feature_deal=current_deal["pizza"], 
        feature_deal_price=current_deal["price"], 
        feature_pizza_size=current_deal["pizza_size"], 
        feature_side_size=current_deal["side_size"],
        feature_deal_side=current_deal["side"],
        expires_at=current_deal["expires_at"],
        cart=cart, 
        popular_pizzas=popular_pizzas, 
        popular_gourmet_pizzas=popular_gourmet_pizzas, 
        popular_sides=popular_sides)

@app.route('/add_featured_deal', methods=['POST'])
def add_featured_deal():
    """
    Reads the hidden form fields from the Featured Deal section and adds 
    both the pizza and the side to the user's session cart. It tags them with 
    'is_deal': True so the checkout system knows to apply the discount.
    """
    pizza = request.form.get('pizza')
    pizza_size = request.form.get('pizza_size')
    side = request.form.get('side')
    side_size = request.form.get('side_size')

    classic_pizzas, gourmet_pizzas, sides = load_data()
    all_pizzas = {**classic_pizzas, **gourmet_pizzas}

    pizza_price = float(all_pizzas.get(pizza, {}).get('price', 0))
    side_base_price = float(sides.get(side, {}).get('price', 0))

    cart = session.get('cart', [])
    
    cart.append({
        'item': pizza,
        'size': pizza_size,
        'quantity': 1,
        'instructions': 'Featured Deal',
        'is_deal': True,
        'price': pizza_price
    })
    
    cart.append({
        'item': side,
        'size': side_size,
        'quantity': 1,
        'instructions': 'Featured Deal',
        'is_deal': True,
        'price': side_base_price * 0.8
    })
    
    session['cart'] = cart
    flash('Featured deal added directly to your cart!')
    return redirect(url_for('menu'))

def get_popular_items(limit=3):
    """
    Queries the database to find the items that have been ordered the most times.
    It groups order quantities by item name, sorts them highest to lowest, 
    and returns the top 3 (by default) items for each category (classic, gourmet, sides).
    """
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
    """Renders the About Us page."""
    return render_template('about.html', active_page='about')

@app.route('/menu')
def menu():
    """
    Renders the main Menu page. Loads all food items from JSON 
    and passes them to the template to be displayed.
    """
    cart = session.get('cart', [])
    classic_pizzas, gourmet_pizzas, sides = load_data()
    open_item = request.args.get('item')
    requested_diet = request.args.get('diet')

    filtered_classic = diet_filter(classic_pizzas, requested_diet)
    filtered_gourmet = diet_filter(gourmet_pizzas, requested_diet)
    filtered_sides = diet_filter(sides, requested_diet)

    return render_template('menu.html', active_page='menu', classic_pizzas=filtered_classic, gourmet_pizzas=filtered_gourmet, sides=filtered_sides, cart=cart, open_item=open_item, current_filter=requested_diet)

def diet_filter(items, diet_type):
    """
    Filters the provided items dictionary based on the specified diet type.
    """
    if diet_type in ['vegetarian', 'non-vegetarian']:
        return {
            name: details for name, details in items.items() 
            if str(details.get('diet_type', '')).lower() == diet_type.lower()
        }
    return items

@app.route('/contact')
def contact():
    """Renders the Contact page."""
    return render_template('contact.html')

@app.route('/order_history')
def order_history():
    """
    Fetches every past order from the SQLite database, joining the 
    'orders' table with the 'order_items' table so it can display 
    the customer info alongside what they actually ordered.
    """
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

    rows = c.fetchall()
    conn.close()

    grouped_orders = {}
    for row in rows:
        order_id = row['id']

        if order_id not in grouped_orders:
            grouped_orders[order_id] = {
                'id': order_id,
                'invoice_number': f"INV_{row['customer_name'].replace(' ', '_')}",
                'customer_name': row['customer_name'],
                'total': row['total'],
                'invoice_date': row['order_date'],
                'items': {}
            }

        item_label = f"{row['size']} ({row['item_name']})"
        grouped_orders[order_id]['items'][item_label] = {'quantity': row['quantity']}
    orders = list(grouped_orders.values())
    conn.close()

    return render_template('order_history.html', orders=orders)

@app.route('/cancel_saved_order/<int:order_id>', methods=['POST'])
def cancel_saved_order(order_id):
    """
    Cancels a previously saved order. It looks up the order in the database,
    restocks the items back into the JSON files, and then deletes the order
    """
    conn = sqlite3.connect('dream_pizza.db')
    c = conn.cursor()

    c.execute('SELECT item_name, quantity FROM order_items WHERE order_id = ?', (order_id,))
    items_to_restock = c.fetchall()

    classic_pizzas, gourmet_pizzas, sides = load_data()

    for item_name, quantity in items_to_restock:
        if item_name in classic_pizzas:
            classic_pizzas[item_name]['stock'] += quantity
        elif item_name in gourmet_pizzas:
            gourmet_pizzas[item_name]['stock'] += quantity
        elif item_name in sides:
            sides[item_name]['stock'] += quantity

    with open('data/classic_pizzas.json', 'w') as f:
        json.dump(classic_pizzas, f, indent=4)
    with open('data/gourmet_pizzas.json', 'w') as f:
        json.dump(gourmet_pizzas, f, indent=4)
    with open('data/sides.json', 'w') as f:
        json.dump(sides, f, indent=4)

    c.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
    c.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()

    flash(f'Order {order_id} has been cancelled and stock has been updated.')
    return redirect(url_for('order_history'))

@app.route('/help')
def help():
    """Renders the Help/FAQ page."""
    return render_template('help.html')

@app.route('/invoice')
def invoice():
    """
    Generates a final receipt. It looks up the 'last_order' stored in the 
    user's session after they checkout, calculates the totals, and formats 
    an invoice number before rendering the invoice page.
    """
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
    """
    Handles adding standard items to the cart. It enforces rules like a 
    maximum limit of 5 pizzas and 5 sides per order. If the user adds an item 
    that is already in the cart (same size and instructions), it simply 
    updates the quantity rather than creating a duplicate entry.
    """
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
                        flash('You have reached the maximum quantity of pizzas in your cart')
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
    """
    Filters the user's current session cart to remove any item that matches 
    the exact name and size requested. It then saves the updated cart back to the session.
    """
    item = request.form.get('item')
    size = request.form.get('size')
    cart = session.get('cart', [])
    cart = [i for i in cart if not (i['item'] == item and i['size'] == size)]
    session['cart'] = cart
    flash(f'Removed {size} {item} from your cart')
    return redirect(url_for('menu'))

def total_price(cart):
    """
    Loops through all items currently in the cart and calculates the total cost. 
    It checks if the item is tagged as a deal ('is_deal') to apply the 20% discount.
    """
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
    """
    Handles the final step of placing an order. 
    1. Saves customer details to the database ('orders' table).
    2. Saves individual ordered items to the database ('order_items' table).
    3. Subtracts the ordered quantities from the stock numbers in the JSON files.
    4. Saves the order details into 'last_order' for the invoice.
    5. Clears the user's active cart.
    """
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