# 🏆 كأس الشباب — Youth Conference Gamification

A full-stack Django application that turns a 50-person youth-conference into a FIFA-style competition between **France 🇫🇷, Argentina 🇦🇷, Spain 🇪🇸, and Portugal 🇵🇹**. Each participant has a QR-coded ID card; leaders scan them with their phone to award points, track attendance, and rank teams.

The whole UI is in **Egyptian Arabic** with a **World-Cup stadium** look (gradients, glowing cards, stadium lights, goal-popups, fanfare beeps).

---

## ✨ Features

| Page              | What it does                                                                                       |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| `/login/`         | Shared leader login (`leader` / `fifa2026` by default).                                            |
| `/scanner/`       | Mobile camera QR scanner. Pick activity → attendance (on-time / late / absent) → ±5 bonus → save. |
| `/live/`          | Full-screen projector view — one column per team, names turn green/yellow when scanned, GOAL! popup when a team finishes entry. |
| `/leaderboard/`   | FIFA-style team standings + top 10 individuals.                                                    |
| `/qr-codes/`      | Printable grid of every participant's QR card + download-all ZIP.                                  |
| `/admin/`         | Standard Django admin for editing teams, participants, activities, scans.                          |

**Scoring**

| Action                  | Points |
| ----------------------- | ------ |
| حضر في المعاد           | +15    |
| اتأخر                   | +5     |
| غاب                     | 0      |
| زر +5 / -5              | ±5     |
| أول فريق يكمل الدخول    | +20    |
| الثاني / الثالث / الرابع | +15 / +10 / 0 |

Duplicate scans on the same activity are **updated, not duplicated** — one row per (participant, activity).

---

## 🚀 Run locally

```bash
# 1. Create a venv
python3 -m venv venv
source venv/bin/activate          # on Windows: venv\Scripts\activate

# 2. Install
pip install -r requirements.txt

# 3. Set up the database
python manage.py migrate

# 4. Seed teams + activities + 50 Arabic-named participants
python manage.py seed_data

# 5. Run the server (bind to 0.0.0.0 so phones on the same Wi-Fi can connect)
python manage.py runserver 0.0.0.0:8000
```

Open **http://localhost:8000** on the projector laptop, and **http://<your-laptop-ip>:8000** on the leaders' phones.

> ⚠️ Browser cameras require **HTTPS** or **localhost**. On a phone, the easiest options are:
> - Use [`ngrok http 8000`](https://ngrok.com) to get a temporary HTTPS URL.
> - Or run on the laptop's localhost with the phone connected via USB and `chrome://inspect`.
> - Or generate a self-signed cert and use `runserver_plus` (django-extensions).

Default users created by the seed:

| Role   | Username | Password   |
| ------ | -------- | ---------- |
| Leader | `leader` | `fifa2026` |
| Admin  | `admin`  | `admin`    |

---

## 🗂️ Project structure

```
youth_conference/
├── manage.py
├── requirements.txt
├── README.md
├── config/                 # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── core/                   # Main app
    ├── models.py           # Team, Participant, Activity, Scan, TeamBonus
    ├── views.py            # Pages + JSON API
    ├── urls.py
    ├── services.py         # Scoring & entry-ranking logic
    ├── admin.py
    ├── management/commands/seed_data.py
    ├── templates/core/
    │   ├── base.html       # World-Cup themed layout
    │   ├── login.html
    │   ├── scanner.html    # html5-qrcode based camera scanner
    │   ├── live_entry.html # projector view
    │   ├── leaderboard.html
    │   └── qr_codes.html
    └── static/core/
        ├── css/app.css     # stadium lights, glowing cards, RTL
        └── js/             # app.js, scanner.js, live_entry.js
```

---

## 🔄 Live updates

The current build uses **AJAX polling every 3 seconds** for the live entry screen and every 5 seconds for the leaderboard — zero extra infrastructure required. If you'd rather use WebSockets, swap in [Django Channels](https://channels.readthedocs.io) and replace the `setInterval` calls in `live_entry.js`.

---

## 🖨️ Printing QR cards

1. Log in as a leader.
2. Open `/qr-codes/`.
3. Either click **🖨️ طباعة** to print the on-screen grid (CSS print-rules already hide nav etc.), or click **⬇️ تحميل الكل (ZIP)** to get every QR as a PNG, grouped per team.

---

## 🧪 Reset data mid-conference

```bash
python manage.py seed_data --reset
```

This wipes scans, bonuses, participants, resets team scores/ranks, then re-seeds with the original 50 names.

---

## 🎨 Customizing

- **Team names / colors / flags** → edit `TEAMS_DATA` in `core/management/commands/seed_data.py` (or use `/admin/`).
- **Activity list** → edit `activity_specs` in the same file.
- **Scoring rules** → `Scan.ATTENDANCE_POINTS` and `services.ENTRY_RANK_BONUSES`.
- **Which activity is the "entry" activity** → set `is_entry=True` on exactly one Activity via admin (default: "خدمة 1").
- **Which activity is currently being scanned** → set `is_active=True` on one Activity (defaults to the entry one). The scanner UI lets a leader override per-scan.

---

## 🛡️ Notes for production

This project is built for a single conference, on a trusted local Wi-Fi. Before exposing to the internet:

- Change `SECRET_KEY` in `config/settings.py`.
- Change `LEADER_PASSWORD`.
- Set `DEBUG = False` and configure `ALLOWED_HOSTS`.
- Put behind HTTPS (camera access requires it on real domains).
- Consider PostgreSQL instead of SQLite if you'll be scanning concurrently from many devices.

---

يلا، خلّونا نشوف مين هياخد الكاس! ⚽🏆
