# TELEGRAM STARS PAYMENT INTEGRATION

## OVERVIEW
Add Telegram Stars (XTR) payment system to the AetherLang bot.
Users pay with Telegram Stars to get credits for using AI engines.

**Location:** `/opt/aetherlang-bot/aetherlang_ultimate_bot.py`
**Service:** `systemctl restart aetherlang-bot`

---

## HOW TELEGRAM STARS WORK
- Telegram's built-in digital currency
- `provider_token` = "" (empty string, Stars don't need external provider)
- `currency` = "XTR" 
- Prices in Stars (integer, 1 Star minimum)
- Bot receives `pre_checkout_query` and `successful_payment` in updates
- IMPORTANT: Add "pre_checkout_query" and "successful_payment" to allowed_updates in polling

---

## PRICING MODEL

### Credit Packages:
| Package | Stars | Credits | Cost/Credit |
|---------|-------|---------|-------------|
| Starter | 150 ⭐ | 15 credits | 10 Stars/credit |
| Pro | 400 ⭐ | 50 credits | 8 Stars/credit |
| Ultimate | 900 ⭐ | 150 credits | 6 Stars/credit |

### Credit Costs Per Engine:
| Engine | Credits | Stars equiv (Pro) |
|--------|---------|-------------------|
| chef, molecular, omega, terra | 2 credits | ~16 Stars |
| marketing, cyber, oracle | 2 credits | ~16 Stars |
| crypto (with 5 exchanges) | 3 credits | ~24 Stars |
| apex, consulting, lab, academic | 4 credits | ~32 Stars |
| assembly, brain | 4 credits | ~32 Stars |
| blueprint (PDF) | 6 credits | ~48 Stars |
| Vision Chef (1-2 photos) | 5 credits | ~40 Stars |
| Vision Chef (3+ photos) | 8 credits | ~64 Stars |

### Free Tier:
- Every new user gets 3 FREE credits on first /start (enough for 1 standard engine test)
- /help and /status are always free
- /engines list is free

---

## IMPLEMENTATION

### 1. Database (SQLite)
Create/use file: `/opt/aetherlang-bot/credits.db`
```sql
CREATE TABLE IF NOT EXISTS user_credits (
    user_id INTEGER PRIMARY KEY,
    credits INTEGER DEFAULT 3,
    total_purchased INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    last_purchase TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,  -- 'purchase' or 'spend'
    amount INTEGER,
    stars_paid INTEGER DEFAULT 0,
    engine TEXT DEFAULT '',
    description TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Credit Functions (add to bot)
```python
import sqlite3

CREDITS_DB = "/opt/aetherlang-bot/credits.db"

def init_credits_db():
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS user_credits (
        user_id INTEGER PRIMARY KEY,
        credits INTEGER DEFAULT 3,
        total_purchased INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0,
        first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
        last_purchase TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, type TEXT, amount INTEGER,
        stars_paid INTEGER DEFAULT 0, engine TEXT DEFAULT '',
        description TEXT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def get_credits(user_id: int) -> int:
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
        conn.commit()
        conn.close()
        return 3
    conn.close()
    return row[0]

def spend_credits(user_id: int, amount: int, engine: str) -> bool:
    current = get_credits(user_id)
    if current < amount:
        return False
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("UPDATE user_credits SET credits = credits - ?, total_spent = total_spent + ? WHERE user_id = ?", 
              (amount, amount, user_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, engine, description) VALUES (?, 'spend', ?, ?, ?)",
              (user_id, amount, engine, f"Used {engine} engine"))
    conn.commit()
    conn.close()
    return True

def add_credits(user_id: int, amount: int, stars_paid: int):
    get_credits(user_id)  # ensure user exists
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("UPDATE user_credits SET credits = credits + ?, total_purchased = total_purchased + ?, last_purchase = CURRENT_TIMESTAMP WHERE user_id = ?",
              (amount, amount, user_id))
    c.execute("INSERT INTO transactions (user_id, type, amount, stars_paid, description) VALUES (?, 'purchase', ?, ?, ?)",
              (user_id, amount, stars_paid, f"Purchased {amount} credits for {stars_paid} Stars"))
    conn.commit()
    conn.close()

# Credit costs per engine
ENGINE_COSTS = {
    "chef": 2, "molecular": 2, "omega": 2, "terra": 2,
    "apex": 4, "consulting": 4, "lab": 4, "academic": 4,
    "assembly": 4, "brain": 4,
    "marketing": 2, "cyber": 2, "oracle": 2, "crypto": 3,
    "blueprint": 6, "vision": 5, "vision_multi": 8,
}
```

### 3. Payment Commands

#### /credits — Show balance
```python
if text == "/credits" or text == "/balance":
    credits = get_credits(user_id)
    msg = f"""💰 <b>Your Credits: {credits}</b>

📊 Credit costs:
- Recipe/Standard engines: 2 credits
- Crypto (5 exchanges): 3 credits
- Analysis/Strategy engines: 4 credits
- Blueprint PDF: 6 credits
- Vision Chef (photo): 5-8 credits

🛒 Buy more: /buy"""
    await send_msg(chat_id, msg)
    return
```

#### /buy — Show packages with inline buttons
```python
if text == "/buy" or text == "/shop" or text == "/store":
    keyboard = {"inline_keyboard": [
        [{"text": "⭐ 150 Stars → 15 Credits", "callback_data": "buy:starter"}],
        [{"text": "⭐ 400 Stars → 50 Credits (Best Value)", "callback_data": "buy:pro"}],
        [{"text": "⭐ 900 Stars → 150 Credits (Ultimate)", "callback_data": "buy:ultimate"}],
    ]}
    credits = get_credits(user_id)
    await tg("sendMessage", chat_id=chat_id, 
        text=f"🛒 <b>Buy Credits</b>\n\nCurrent balance: {credits} credits\n\nChoose a package:",
        reply_markup=keyboard, parse_mode="HTML")
    return
```

#### Handle buy callback → sendInvoice
```python
# In handle_callback function, add:
if data.startswith("buy:"):
    package = data.split(":")[1]
    packages = {
        "starter": {"title": "Starter Pack", "desc": "15 AI credits", "stars": 150, "credits": 15},
        "pro": {"title": "Pro Pack", "desc": "50 AI credits — Best Value!", "stars": 400, "credits": 50},
        "ultimate": {"title": "Ultimate Pack", "desc": "150 AI credits", "stars": 900, "credits": 150},
    }
    pkg = packages.get(package)
    if not pkg:
        return
    
    await tg("sendInvoice",
        chat_id=chat_id,
        title=pkg["title"],
        description=pkg["desc"],
        payload=f"credits_{package}_{user_id}",
        provider_token="",  # Empty for Stars
        currency="XTR",
        prices=[{"label": pkg["title"], "amount": pkg["stars"]}],
    )
```

### 4. Payment Handlers

#### Pre-checkout query (MUST answer within 10 seconds)
```python
async def handle_pre_checkout(update: dict):
    pcq = update.get("pre_checkout_query", {})
    if not pcq:
        return
    # Always approve (we validate later)
    await tg("answerPreCheckoutQuery", 
        pre_checkout_query_id=pcq["id"], 
        ok=True)

# Call this from main polling loop
```

#### Successful payment
```python
async def handle_successful_payment(update: dict):
    msg = update.get("message", {})
    payment = msg.get("successful_payment", {})
    if not payment:
        return
    
    chat_id = msg.get("chat", {}).get("id")
    user_id = msg.get("from", {}).get("id", 0)
    payload = payment.get("invoice_payload", "")
    stars = payment.get("total_amount", 0)
    
    # Parse payload: credits_starter_12345
    parts = payload.split("_")
    package = parts[1] if len(parts) >= 2 else ""
    
    credit_map = {"starter": 15, "pro": 50, "ultimate": 150}
    credits_to_add = credit_map.get(package, 0)
    
    if credits_to_add > 0:
        add_credits(user_id, credits_to_add, stars)
        new_balance = get_credits(user_id)
        await send_msg(chat_id, 
            f"✅ <b>Payment Successful!</b>\n\n"
            f"⭐ Paid: {stars} Stars\n"
            f"💰 Added: +{credits_to_add} credits\n"
            f"📊 New balance: {new_balance} credits\n\n"
            f"Enjoy your AI engines! 🚀")
```

### 5. Credit Check Before Engine Use

In `process_query()`, BEFORE executing any engine:
```python
# Check credits
cost = ENGINE_COSTS.get(engine_key, 1)
current_credits = get_credits(user_id)
if current_credits < cost:
    buy_keyboard = {"inline_keyboard": [
        [{"text": "🛒 Buy Credits", "callback_data": "buy:pro"}],
    ]}
    await tg("sendMessage", chat_id=chat_id,
        text=f"💰 Not enough credits!\n\nNeeded: {cost} | Balance: {current_credits}\n\n🛒 Buy more credits:",
        reply_markup=buy_keyboard, parse_mode="HTML")
    return "Credits insufficient"

# Deduct credits
spend_credits(user_id, cost, engine_key)
remaining = get_credits(user_id)
```

In Vision Chef handler (_vision_chef_process), before processing:
```python
cost = 8 if len(file_ids) >= 3 else 5
if get_credits(user_id) < cost:
    await send_msg(chat_id, "💰 Not enough credits for Vision Chef!\n🛒 /buy to get more")
    return
spend_credits(user_id, cost, "vision")
```

### 6. Update Polling Loop

In `main()`, update allowed_updates to include payment events:
```python
allowed = ["message", "callback_query", "pre_checkout_query"]
# In getUpdates call:
params = {
    "offset": offset,
    "timeout": 30,
    "allowed_updates": allowed
}
```

In the update processing loop:
```python
for update in updates:
    if "pre_checkout_query" in update:
        await handle_pre_checkout(update)
    elif "callback_query" in update:
        await handle_callback(update)
    elif "message" in update:
        msg = update["message"]
        if "successful_payment" in msg:
            await handle_successful_payment(update)
        else:
            await handle_message(update)
```

### 7. Update Welcome Message

Add to /start response:
```
💰 <b>Credits:</b> /credits — Check balance | /buy — Get more
🆕 New users get 5 FREE credits!
```

### 8. Add Credit Info to Engine Response Footer

After each engine response, add:
```
💰 Credits: X remaining (cost: Y)
```

---

## ADMIN COMMANDS (for owner only, user_id from ALLOWED_USERS)
```python
# /admin_credits USER_ID AMOUNT — Give credits
if text.startswith("/admin_credits") and user_id in ALLOWED_USERS:
    parts = text.split()
    if len(parts) == 3:
        target = int(parts[1])
        amount = int(parts[2])
        add_credits(target, amount, 0)
        await send_msg(chat_id, f"✅ Added {amount} credits to user {target}")
    return

# /admin_stats — Revenue stats
if text == "/admin_stats" and user_id in ALLOWED_USERS:
    conn = sqlite3.connect(CREDITS_DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), SUM(credits), SUM(total_purchased) FROM user_credits")
    users, total_credits, total_purchased = c.fetchone()
    c.execute("SELECT SUM(stars_paid) FROM transactions WHERE type='purchase'")
    total_stars = c.fetchone()[0] or 0
    c.execute("SELECT engine, COUNT(*), SUM(amount) FROM transactions WHERE type='spend' GROUP BY engine ORDER BY COUNT(*) DESC")
    engine_stats = c.fetchall()
    conn.close()
    
    lines = [f"📊 <b>Admin Stats</b>\n",
             f"👤 Users: {users}",
             f"⭐ Total Stars earned: {total_stars}",
             f"💰 Total credits purchased: {total_purchased or 0}",
             f"📊 Credits in circulation: {total_credits or 0}\n",
             f"<b>Engine Usage:</b>"]
    for eng, count, spent in engine_stats[:10]:
        lines.append(f"  {eng}: {count} uses ({spent} credits)")
    await send_msg(chat_id, "\n".join(lines))
    return
```

---

## TESTING CHECKLIST

1. `/credits` — Shows 3 free credits for new user
2. `/buy` — Shows 3 packages with inline buttons
3. Click "Pro Pack" — Invoice appears with Stars payment
4. Complete payment — Credits added, confirmation message
5. Use engine — Credits deducted, remaining shown
6. Try engine with 0 credits — "Not enough credits" + buy button
7. Send photo with 0 credits — "Not enough credits" message
8. `/admin_stats` — Shows revenue stats (owner only)

---

## IMPORTANT NOTES
- NEVER break existing functionality (Vision Chef, engines)
- `init_credits_db()` must be called on bot startup in `main()`
- Pre-checkout query MUST be answered within 10 seconds or payment fails
- Always check `provider_token=""` for Stars (not a real payment provider)
- Currency is "XTR" (Telegram Stars), NOT "USD"
- Star amounts must be integers >= 1
- Add appropriate error handling around all payment operations
- The `successful_payment` comes inside a `message` update, not separately
