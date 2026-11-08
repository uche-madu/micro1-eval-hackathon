# Schedule the Q3 audit review

Schedule eight meetings over Monday, Tuesday, and Wednesday, 09:00-17:00. Lunch is 12:00-13:00 and no meeting may overlap it. Rooms are A, B, and C; no room and no attendee may be double-booked. All times are local.

| Meeting | Duration | Attendees | Allowed day(s) | Allowed room(s) | Allowed window |
|---|---:|---|---|---|---|
| M1 | 60 | Alice, Bob | Mon | A | 09:00-11:00 |
| M2 | 90 | Bob, Chen | Tue or Wed | B | 10:00-12:00 |
| M3 | 45 | Alice, Dana | Wed | C | 09:00-12:00 |
| M4 | 60 | Chen, Dana | Tue or Wed | A | 13:00-16:00 |
| M5 | 120 | Alice, Chen, Dana | Wed | B | 13:00-16:00 |
| M6 | 30 | Bob, Dana | Tue | C | 09:00-10:00 |
| M7 | 60 | Alice, Bob, Chen, Dana, Evan | Wed | A | 15:00-17:00 |
| M8 | 90 | Alice, Bob, Chen | Mon or Tue | C | 10:30-12:00 or 14:00-16:00 |

Additional constraints:
- M2 must start after M6 ends.
- M8 must start after M1 ends.
- M5 must start after M4 ends.
- M7 must start after M5 ends.
- Meetings may not be split.

Return ONLY JSON:
```json
{"schedule": [{"meeting": "M1", "day": "Mon", "start": "09:00", "end": "10:00", "room": "A"}]}
```
Use 24-hour times. Every meeting must appear exactly once.
