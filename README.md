Bilkul ready hai! Yeh README aapke code ki functionalities, endpoints aur structure ko perfect tareeke se explain karti hai. Aap isay seedha copy-paste kar sakte hain.

---

# 🚀 Facebook Ads Manager API (DRF)

Yeh ek advanced Django Rest Framework (DRF) based integration hai jo **Meta Business SDK** ko use karte huay Facebook Ads management ko automate karti hai. Is mein Campaign creation se lekar granular targeting aur creative management tak sab kuch aik hi ViewSet mein handle kiya gaya hai.

## 🛠 Features

* **OAuth 2.0 Flow:** Seamless Facebook Login aur Access Token management.
* **Full CRUD:** Campaigns, Ad Sets, aur Ads ki mukammal management.
* **Smart Budgeting:** CBO (Campaign Budget Optimization) aur ABO (Ad Set Budget Optimization) ka auto-detection aur conflict handling.
* **Advanced Targeting:** Interests, Behaviors, aur Demographics search aur implementation.
* **Creative Factory:** Bulk image processing aur Ad Creative generation.
* **Special Category Support:** Housing, Employment, aur Credit campaigns ke liye auto-restriction logic.

---

## 🏗 API Endpoints

### 🔐 Authentication

| Action | Method | URL Endpoint | Description |
| --- | --- | --- | --- |
| `Get Login URL` | `GET` | `/fb-manager/get_login_url/` | Facebook Login dialog ka URL generate karta hai. |
| `Callback` | `POST` | `/fb-manager/handle_callback/` | Code exchange karke token save karta hai. |

### 📈 Campaign Management

| Action | Method | URL Endpoint | Description |
| --- | --- | --- | --- |
| `List Campaigns` | `GET` | `/fb-manager/get_campaigns/` | Ad Account ki tamam campaigns fetch karta hai. |
| `Create` | `POST` | `/fb-manager/create_campaign/` | Nayi campaign banata hai (CBO & iOS 14 support). |
| `Update` | `POST` | `/fb-manager/update_campaign/` | Name, Status aur Budget update karta hai. |
| `Toggle` | `POST` | `/fb-manager/toggle_campaign_status/` | Campaign ko Active/Paused karta hai. |

### 🎯 Ad Set & Targeting

| Action | Method | URL Endpoint | Description |
| --- | --- | --- | --- |
| `List Ad Sets` | `GET` | `/fb-manager/get_ad_sets/` | Campaign ke specific Ad Sets dikhata hai. |
| `Create Ad Set` | `POST` | `/fb-manager/create_ad_set/` | Detailed targeting aur scheduling ke sath creation. |
| `Search` | `GET` | `/fb-manager/search_interests/` | Interests/Behaviors fetch karne ke liye Meta search. |

### 🎨 Ads & Creatives

| Action | Method | URL Endpoint | Description |
| --- | --- | --- | --- |
| `Create Creative` | `POST` | `/fb-manager/create_ad_creative/` | Image upload aur link setup karta hai. |
| `Create Ad` | `POST` | `/fb-manager/create_ad/` | Final Ad ko live karne ke liye. |

---

## 📝 Setup & Configuration

### 1. Requirements

```bash
pip install facebook-business requests pytz django-environ

```

### 2. Implementation Details

* **Budgeting:** Budget frontend se simple numbers mein liya jata hai aur backend usay Meta ke required **Cents** format (x100) mein convert karta hai.
* **Timezones:** Ad Set ki scheduling ke liye system automatically Ad Account ka timezone fetch karta hai taake scheduling accurate ho.
* **Conflict Handling:** System check karta hai ke agar Campaign CBO mode mein hai, to Ad Set level budget update ko block kar diya jaye.

---

## ⚠️ Security Note

Is code mein `APP_ID` aur `APP_SECRET` hardcoded hain. Production environment mein inhein **Environment Variables** (`.env`) mein rakhna zaroori hai taake aapka sensitive data secure rahe.

---

**Next Step:** Kya aap chahte hain ke main is mein frontend ke liye aik sample **Axios/Fetch request** ka section bhi add karoon?
