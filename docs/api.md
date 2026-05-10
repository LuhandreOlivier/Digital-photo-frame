# API Setup

## Architecture Overview

This project uses two APIs in sequence. YouVersion's public developer API returns the Verse of the Day as a structured **passage reference** (e.g. `JHN.3.16`), but does not include the verse text in its response. The Scripture API (api.bible) is then used to resolve that reference into readable verse text.

```
Device boots
    ↓
GET youversion.com/v1/verse_of_the_days/{day}
    ↓ returns passage_id: "JHN.3.16"
GET rest.api.bible/v1/bibles/{bible_id}/verses/JHN.3.16
    ↓ returns verse text + reference
Display renders the verse
```

Both API keys are stored in `settings.toml` and never appear in the source code.

---

## YouVersion API

### Registration

1. Go to **https://developers.youversion.com** and sign up for a developer account
2. Create a new App in the dashboard (name it anything — e.g. "Bible Display Device")
3. During registration you will be asked for:
   - **Website URL**: `https://youversion.com`
   - **Callback URL**: `https://youversion.com/callback`
   - **Google Play URL**: `https://play.google.com/store/apps/details?id=com.sirma.mobile.bible.android`
   - **Apple App Store URL**: `https://apps.apple.com/us/app/bible/id282935706`
4. Your `X-YVP-App-Key` will appear in your app settings once approved

### Endpoint

```
GET https://api.youversion.com/v1/verse_of_the_days/{day_of_year}
```

- `{day_of_year}` is an integer from 1 to 366 representing the current day of the year
- Header required: `X-YVP-App-Key: YOUR_KEY`

### Example Response

```json
{
  "passage_id": "JHN.3.16",
  "day": 119
}
```

---

## Scripture API (api.bible)

### Registration

1. Go to **https://scripture.api.bible** and sign up for a free account
2. Create an App in the dashboard
3. Your API key is displayed immediately — no review process required

### Endpoint

```
GET https://rest.api.bible/v1/bibles/{bible_id}/verses/{passage_id}
    ?content-type=text
    &include-notes=false
    &include-titles=false
```

- Header required: `api-key: YOUR_KEY`
- `content-type=text` returns plain text rather than HTML-encoded verse content

### Bible Version IDs

| Translation | ID |
|---|---|
| NIV (New International Version) | `d6e14a625393b4da-01` |
| KJV (King James Version) | `de4e12af7f28f599-02` |
| ESV (English Standard Version) | `f421fe261da7624f-01` |
| NLT (New Living Translation) | `65eec8e0b60e656b-01` |
| ASV (American Standard Version) | `685d1470fe4d5c3b-01` |

The project defaults to **NIV** (`d6e14a625393b4da-01`), which is the most widely used translation on YouVersion.

### Example Response

```json
{
  "data": {
    "content": "For God so loved the world that he gave his one and only Son...",
    "reference": "John 3:16"
  }
}
```

---

## settings.toml

Create this file in the root of the `CIRCUITPY` drive. Do **not** commit this file to version control — it contains your personal credentials.

```toml
WIFI_SSID = "YourNetworkName"
WIFI_PASSWORD = "YourWiFiPassword"
YOUVERSION_APP_KEY = "your-youversion-key-here"
SCRIPTURE_API_KEY = "your-scripture-api-key-here"
```

The Bible version ID is hardcoded in `code.py` as `BIBLE_ID = "d6e14a625393b4da-01"`. Change this constant if you want a different translation.

---

## Rate Limits

| API | Free Limit |
|---|---|
| YouVersion | Not publicly documented; 1 call/day is well within any limit |
| Scripture API | 5,000 requests/day per key |

This project makes at most 2 API calls per day (one to each API), so rate limits are not a concern in normal operation.
