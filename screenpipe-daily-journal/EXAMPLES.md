# Screenpipe Daily Journal - Examples

## Sleep-Aware Day Boundaries

### Example 1: Late-Night Work Session

**Scenario**: You work late into the night, going to bed at 3 AM.

```
Timeline:
Jan 30, 10:00 PM - Start coding
Jan 30, 11:30 PM - Still working
Jan 31, 12:30 AM - Continue working (past midnight)
Jan 31, 2:45 AM - Still active
Jan 31, 3:00 AM - Go to sleep
Jan 31, 11:00 AM - Wake up

Without intelligent boundaries:
- Jan 30 journal: 10 PM - 11:59 PM (2 hours) ❌
- Jan 31 journal: 12 AM - 3 AM + 11 AM onward (messy) ❌

With intelligent boundaries:
- Jan 30 journal: 11 AM (previous wake) - 3 AM (sleep) ✅
- Jan 31 journal: 11 AM (wake) - next sleep ✅
```

### Example 2: Normal Schedule

**Scenario**: You have a regular sleep schedule.

```
Timeline:
Jan 30, 9:00 AM - Wake up, start work
Jan 30, 6:00 PM - Evening work
Jan 30, 11:00 PM - Go to sleep
Jan 31, 8:00 AM - Wake up, start work

Without intelligent boundaries:
- Jan 30 journal: 12 AM - 11:59 PM (includes sleep) ❌
- Jan 31 journal: 12 AM - 11:59 PM (starts during sleep) ❌

With intelligent boundaries:
- Jan 30 journal: 9 AM - 11 PM ✅
- Jan 31 journal: 8 AM - next sleep ✅
```

### Example 3: No Clear Sleep Pattern

**Scenario**: You have sporadic activity with no 3+ hour gaps.

```
Timeline:
Jan 30, various short activities throughout
No gaps > 3 hours

Result:
- Falls back to 6 AM boundaries
- Jan 30: 6 AM - Jan 31, 6 AM
- More natural than midnight cutoff
```

### Example 4: Multiple Sleep Periods (Naps)

**Scenario**: You take a nap during the day.

```
Timeline:
Jan 30, 9:00 AM - Wake up
Jan 30, 2:00 PM - Nap (1 hour) - not detected as sleep (< 3 hours)
Jan 30, 3:00 PM - Resume work
Jan 30, 11:00 PM - Sleep (detected)

Result:
- Jan 30 journal: 9 AM - 11 PM
- Nap is included in the journal (part of the day)
- Main sleep (11 PM) ends the day
```

## Configuration Examples

### Conservative Sleep Detection

For light sleepers or those with frequent breaks:

```json
{
  "sleep_detection": {
    "min_gap_hours": 4.0,
    "default_wake_hour": 7,
    "late_night_cutoff_hour": 6
  }
}
```

### Aggressive Sleep Detection

For those who consistently take long breaks:

```json
{
  "sleep_detection": {
    "min_gap_hours": 2.5,
    "default_wake_hour": 6,
    "late_night_cutoff_hour": 5
  }
}
```

### Night Owl Schedule

For those who work late and wake late:

```json
{
  "sleep_detection": {
    "min_gap_hours": 3.0,
    "default_wake_hour": 10,
    "late_night_cutoff_hour": 8
  }
}
```

## Troubleshooting

### "My late-night work isn't being captured"

**Symptom**: Work from 1-3 AM shows up in next day's journal instead of previous day.

**Solution**: Check if there's continuous activity from previous evening. The system looks for:
1. Activity before midnight on previous day
2. Continuous activity (no 3+ hour gap) through early morning
3. If found, includes in previous day

**Debug**: Run with verbose output to see detected sleep periods:
```bash
python3 generate_journal_v2.py 2026-01-31 --debug
```

### "Sleep detection isn't working"

**Symptom**: Always using 6 AM fallback boundaries.

**Possible causes**:
1. No 3+ hour gaps in activity (adjust `min_gap_hours`)
2. Screenpipe recording stopped/started frequently
3. Background apps keeping system active

**Solution**: Review activity logs and adjust `min_gap_hours` in config.

### "Wrong wake time detected"

**Symptom**: Journal starts at wrong time (e.g., 3 AM instead of 11 AM).

**Possible cause**: System detected brief activity (checking phone) as "wake up".

**Solution**: 
1. Increase `min_gap_hours` to require longer sleep periods
2. Manually adjust journal if needed
3. Consider filtering out mobile device activity

## Best Practices

1. **Review the boundaries**: After generation, check the timeline to ensure boundaries make sense
2. **Adjust config gradually**: Start with defaults, then tune based on your patterns
3. **Manual override when needed**: The system is smart but not perfect - edit as needed
4. **Track your patterns**: Over time, you'll find optimal config values for your rhythm
