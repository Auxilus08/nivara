# Nivara Product Flows

## 1. Navigation

Current location
    ->
Destination search
    ->
Destination selected
    ->
Routing provider
    ->
Candidate routes
    ->
Safety analysis
    ->
Fastest / Balanced / Safety Priority
    ->
Route comparison
    ->
User selects route
    ->
Optional Safe Trip

---

## 2. Route Comparison

Each candidate route can display:

- ETA
- distance
- contextual safety indicators
- incident activity
- activity/isolation indicators
- emergency accessibility
- explanation of major contributing factors

Do not describe a route as guaranteed safe.

---

## 3. Safe Trip

Start Safe Trip
    ->
Capture selected route
    ->
Set expected arrival
    ->
Optional trusted-contact sharing
    ->
Start journey
    ->
Track location according to settings
    ->
Monitor route
    ->
Detect significant deviation
    ->
Ask user if they are okay
    ->
I'm Safe / Need Help
    ->
Continue or escalate
    ->
Trip completion

---

## 4. Route Deviation

Location update
    ->
Compare current position with planned route
    ->
Determine whether deviation is significant
    ->
If no:
        continue monitoring

If yes:
        ask user whether they are okay

Actions:

I'm Safe
    ->
Continue trip

Need Help
    ->
Offer assistance / emergency workflow

A deviation alone is not proof of an emergency.

---

## 5. Check-In

User starts journey
    ->
Expected arrival configured
    ->
Journey continues
    ->
Arrival confirmed

OR

Expected arrival passes
    ->
Prompt user
    ->
I'm Safe / Need Help

---

## 6. Trusted Contacts

Settings
    ->
Trusted Contacts
    ->
Add contact
    ->
Configure sharing preference
    ->
Save

Possible operations:

- create
- list
- update
- delete

---

## 7. SOS

Hold SOS
    ->
Confirm intentional activation
    ->
Create emergency event
    ->
Capture current location
    ->
Notify configured contacts
    ->
Show nearby emergency resources
    ->
Continue location sharing according to settings
    ->
Emergency remains ACTIVE
    ->
ACKNOWLEDGED
    ->
RESOLVED

---

## 8. Find Assistance

User requests help
    ->
Query nearby resources
    ->
Filter by availability where possible
    ->
Rank by distance and contextual indicators
    ->
Display options
    ->
Navigate to selected location

---

## 9. Community Report

User selects report
    ->
Select category
    ->
Add description
    ->
Capture location
    ->
Submit
    ->
Validate
    ->
Store report
    ->
Apply confidence
    ->
Safety engine can use report

---

## 10. AI Incident Classification

Free-text report
    ->
AI classification
    ->
Structured incident candidate
    ->
Validation
    ->
Persist
    ->
Safety engine

AI should not bypass validation.

---

## 11. Privacy

User
    ->
Privacy settings
    ->
Configure:

- live location sharing
- trusted contact sharing
- emergency sharing
- retention

Settings
    ->
Stored
    ->
Applied by services

---

## 12. Emergency State

ACTIVE
    |
    v
ACKNOWLEDGED
    |
    v
RESOLVED

Only authorized operations may transition emergency state.

---

## 13. Demo Flow

Recommended hackathon demonstration:

1. Open Nivara.
2. Allow/select current location.
3. Search destination.
4. Display candidate routes.
5. Compare Fastest, Balanced and Safety Priority.
6. Show contextual indicators.
7. Start Safe Trip.
8. Simulate route deviation.
9. Show check-in prompt.
10. Demonstrate trusted contacts.
11. Demonstrate SOS flow.
12. Show nearby assistance resources.
13. Submit a community report.
14. Show report reflected in safety intelligence.
