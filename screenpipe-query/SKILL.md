---
name: screenpipe-query
description: Universal interface for querying screenpipe recordings - search screen text, audio transcriptions, find specific apps/windows, export videos, and analyze activity patterns. Use when searching screen history, finding past activities, or analyzing productivity data from screenpipe.
---

# Screenpipe Query - Universal Interface

Query your screenpipe recordings using natural language or structured filters. Search across screen text (OCR), audio transcriptions, app usage, and UI interactions.

## Quick Start

```bash
# Natural language search
@screenpipe-query "what was I working on this morning?"

# Find specific content
@screenpipe-query "email from Donghyun"

# App-specific search
@screenpipe-query "what did I do in Cursor today?"

# Time-range search
@screenpipe-query "meetings yesterday afternoon"
```

## Query Types

### 1. Natural Language Queries

Ask in plain English, the skill translates to API calls:

| Query | Translation |
|-------|-------------|
| "what was I doing at 3pm?" | `?start_time=15:00&end_time=15:30` |
| "emails about interviews" | `?q=interview&app_name=Gmail` |
| "conversation with Donghyun" | `?q=Donghyun&content_type=audio` |
| "code I wrote this morning" | `?app_name=Cursor&start_time=09:00` |

### 2. Structured Queries

Direct API parameter control:

```python
{
  "q": "protein design",
  "content_type": "ocr",
  "app_name": "Cursor",
  "start_time": "2026-01-30T09:00:00Z",
  "limit": 50
}
```

### 3. Complex Queries

Combine multiple filters:

```bash
@screenpipe-query "
  content: protein disaggregase
  apps: Cursor, Zotero
  time: yesterday 2pm-5pm
  include: screenshots
"
```

## API Reference

### Search Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (optional) | `"faculty interview"` |
| `content_type` | enum | `all`, `ocr`, `audio`, `ui` | `ocr` |
| `start_time` | ISO 8601 | UTC start time | `2026-01-30T09:00:00Z` |
| `end_time` | ISO 8601 | UTC end time | `2026-01-30T17:00:00Z` |
| `app_name` | string | Filter by application | `"Cursor"` |
| `window_name` | string | Filter by window title | `"dendron (Workspace)"` |
| `limit` | integer | Max results (default 10) | `100` |
| `offset` | integer | Pagination offset | `0` |
| `min_length` | integer | Min text length | `50` |
| `max_length` | integer | Max text length | `500` |
| `include_frames` | boolean | Include screenshots | `true` |
| `speaker_ids` | string | Filter audio by speaker | `"1,2"` |
| `speaker_name` | string | Filter by speaker name | `"Donghyun"` |

### Common Applications

```python
COMMON_APPS = [
    "Cursor",           # Code editor
    "Google Chrome",    # Browser
    "Safari",
    "Slack",            # Communication
    "zoom.us",          # Meetings
    "Microsoft Teams",
    "Gmail",            # Email
    "Zotero",          # References
    "Terminal",         # Shell
    "Microsoft Excel",
    "Microsoft PowerPoint"
]
```

## Query Patterns

### Time-Based Queries

**Relative time**:
```python
# Last hour
now = datetime.now()
start = (now - timedelta(hours=1)).isoformat() + 'Z'
query = f"?start_time={start}"

# Today
today_start = datetime.now().replace(hour=0, minute=0).isoformat() + 'Z'
query = f"?start_time={today_start}"

# Yesterday
yesterday = (datetime.now() - timedelta(days=1))
start = yesterday.replace(hour=0, minute=0).isoformat() + 'Z'
end = yesterday.replace(hour=23, minute=59).isoformat() + 'Z'
query = f"?start_time={start}&end_time={end}"
```

**Absolute time**:
```python
# Specific meeting
query = "?start_time=2026-01-29T15:30:00Z&end_time=2026-01-29T16:00:00Z"
```

### Content-Type Queries

**Screen text only**:
```bash
curl "http://localhost:3030/search?content_type=ocr&q=protein"
```

**Audio transcriptions only**:
```bash
curl "http://localhost:3030/search?content_type=audio&q=interview"
```

**Everything**:
```bash
curl "http://localhost:3030/search?content_type=all&q=disaggregase"
```

### Application-Specific Queries

**Find all Cursor activity**:
```python
{
  "app_name": "Cursor",
  "start_time": "2026-01-30T00:00:00Z",
  "limit": 200
}
```

**Gmail + Slack messages**:
```python
# Run two queries in parallel
query1 = {"app_name": "Gmail", "q": "interview"}
query2 = {"app_name": "Slack", "q": "interview"}
```

### Screenshot Extraction

**Get screens with screenshots**:
```python
{
  "q": "email",
  "include_frames": true,
  "limit": 10
}
```

**Save screenshot**:
```python
import base64

frame_base64 = result['content']['frame']
with open('screenshot.png', 'wb') as f:
    f.write(base64.b64decode(frame_base64))
```

## Query Translation Engine

Translate natural language to API calls:

### Time Extraction

```python
time_patterns = {
    r"this morning": lambda: (today_9am, today_noon),
    r"this afternoon": lambda: (today_noon, today_5pm),
    r"this evening": lambda: (today_5pm, today_9pm),
    r"yesterday": lambda: (yesterday_start, yesterday_end),
    r"last (\d+) hours?": lambda h: (now - timedelta(hours=h), now),
    r"at (\d+):(\d+)\s*(am|pm)": lambda h, m, p: parse_time(h, m, p),
}
```

### App Extraction

```python
app_aliases = {
    "code editor": "Cursor",
    "terminal": "Terminal",
    "email": "Gmail",
    "chat": "Slack",
    "zoom": "zoom.us",
    "excel": "Microsoft Excel",
}
```

### Intent Detection

```python
intents = {
    "what was I": "retrieve",
    "find": "search",
    "show me": "retrieve",
    "when did I": "search_time",
    "how long": "analyze_duration",
    "who did I": "search_people",
}
```

## Advanced Queries

### 1. Find Specific Email

```python
query = {
    "q": "Donghyun",
    "app_name": "Gmail",
    "content_type": "ocr",
    "start_time": "2026-01-27T00:00:00Z",
    "include_frames": true,
    "limit": 20
}
```

### 2. Meeting Transcription

```python
query = {
    "content_type": "audio",
    "start_time": "2026-01-29T15:30:00Z",
    "end_time": "2026-01-29T16:30:00Z",
    "app_name": "zoom.us",
    "limit": 500
}
```

### 3. Code Changes Analysis

```python
query = {
    "app_name": "Cursor",
    "window_name": "protein_clock",
    "start_time": "2026-01-30T09:00:00Z",
    "end_time": "2026-01-30T17:00:00Z",
    "min_length": 50,
    "limit": 200
}
```

### 4. Productivity Analysis

```python
# Get all activity for a day
query = {
    "start_time": "2026-01-30T00:00:00Z",
    "end_time": "2026-01-30T23:59:59Z",
    "limit": 2000
}

# Analyze
apps = Counter(item['content']['app_name'] for item in results)
focus_time = calculate_focus_sessions(results)
```

### 5. Find Context for Decision

```python
# Search around a specific time
decision_time = "2026-01-28T13:00:00Z"
query = {
    "start_time": (decision_time - timedelta(hours=1)).isoformat() + 'Z',
    "end_time": (decision_time + timedelta(hours=1)).isoformat() + 'Z',
    "content_type": "all",
    "limit": 100
}
```

## Export Video

Create video from screen recordings:

```python
{
    "tool": "export-video",
    "start_time": "2026-01-30T14:00:00Z",
    "end_time": "2026-01-30T15:00:00Z",
    "fps": 1.0  # Frames per second
}
```

Video saved to: `/tmp/screenpipe_export_TIMESTAMP.mp4`

## Response Processing

### Extract Information

```python
def process_results(results):
    for item in results['data']:
        if item['type'] == 'OCR':
            text = item['content']['text']
            app = item['content']['app_name']
            window = item['content']['window_name']
            timestamp = item['content']['timestamp']
            
        elif item['type'] == 'Audio':
            transcription = item['content']['transcription']
            speaker = item['content']['speaker']['id']
            device = item['content']['device_name']
```

### Group by Time

```python
def group_by_hour(results):
    hourly = defaultdict(list)
    for item in results['data']:
        ts = parse_timestamp(item['content']['timestamp'])
        hour = ts.hour
        hourly[hour].append(item)
    return hourly
```

### Analyze Patterns

```python
def analyze_app_usage(results):
    apps = Counter()
    durations = defaultdict(int)
    
    for item in results['data']:
        app = item['content']['app_name']
        apps[app] += 1
        # Estimate duration based on frame frequency
        durations[app] += 2  # Assuming 0.5 FPS = 2 sec/frame
    
    return apps, durations
```

## Query Optimization

### 1. Limit Results

Always set reasonable limits:
```python
# Bad: no limit (could return 10,000s of results)
query = {"q": "code"}

# Good: reasonable limit
query = {"q": "code", "limit": 100}
```

### 2. Use Time Filters

Reduce data volume:
```python
# Bad: search entire history
query = {"q": "meeting"}

# Good: search recent history
query = {
    "q": "meeting",
    "start_time": get_today_start(),
    "limit": 50
}
```

### 3. Filter by Content Type

Skip irrelevant data:
```python
# Bad: search everything for code
query = {"q": "function", "content_type": "all"}

# Good: OCR only for code
query = {"q": "function", "content_type": "ocr", "app_name": "Cursor"}
```

### 4. Pagination

For large result sets:
```python
offset = 0
all_results = []
while True:
    results = query(limit=100, offset=offset)
    if not results['data']:
        break
    all_results.extend(results['data'])
    offset += 100
```

## Usage Examples

### Example 1: Find Email Thread

```bash
@screenpipe-query "
  Find email conversation with Donghyun about interviews
  Include screenshots
"
```

Translates to:
```python
{
    "q": "Donghyun interview",
    "app_name": "Gmail",
    "content_type": "ocr",
    "include_frames": true,
    "limit": 20
}
```

### Example 2: Analyze Productivity

```bash
@screenpipe-query "
  How much time did I spend coding today?
"
```

Translates to:
```python
{
    "app_name": "Cursor",
    "start_time": today_start,
    "end_time": now,
    "limit": 500
}
# Then calculate duration from frame count
```

### Example 3: Meeting Summary

```bash
@screenpipe-query "
  Summarize my Zoom meeting yesterday at 3:30pm
"
```

Translates to:
```python
{
    "content_type": "audio",
    "app_name": "zoom.us",
    "start_time": "2026-01-29T15:30:00Z",
    "end_time": "2026-01-29T16:30:00Z",
    "limit": 200
}
```

## Troubleshooting

**Empty results**:
- Check time format (must be ISO 8601 UTC)
- Verify screenpipe is running: `curl http://localhost:3030/search?limit=1`
- Check app name spelling (case-sensitive)

**Too many results**:
- Add time filters
- Use more specific search terms
- Filter by app or window

**Poor OCR quality**:
- Check screenpipe language settings
- Increase FPS for better capture
- Try `min_length` filter to skip garbage

**Missing audio**:
- Verify audio recording enabled in screenpipe
- Check microphone permissions
- Look for "HyperX SoloCast" or your device name

## Integration

### With Daily Journal

```python
# Query for journal data
data = screenpipe_query(start=today, end=now, limit=1000)
insights = generate_insights(data)
timeline = create_timeline(data)
tasks = infer_tasks(data)
```

### With Dendron

```python
# Find knowledge to add
results = screenpipe_query(q="paper", app="Zotero", limit=50)
papers = extract_paper_info(results)
# Add to Dendron with dendron-add skill
```

### With Task Manager

```python
# Extract action items
results = screenpipe_query(content_type="audio", q="need to", limit=100)
tasks = extract_tasks_from_audio(results)
```

## API Endpoint

Default: `http://localhost:3030`

Custom port:
```bash
export SCREENPIPE_PORT=3030
@screenpipe-query "..."
```

## Related Skills

- **[[screenpipe-daily-journal]]** - Generate daily journals
- **[[dendron-add]]** - Add findings to knowledge base
- **[[task-manager]]** - Track tasks from screenpipe

## Script Location

Query helper: `/Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-query/scripts/query.py`

Run standalone:
```bash
python /Users/A.Y/Documents/Manual Library/Dendron/.cursor/skills/screenpipe-query/scripts/query.py "what was I doing at 2pm"
```
