# -*- coding: utf-8 -*-
"""
test_synthlint.py — pytest suite for SynthLint.

Covers:
  * each of the six shipped checks, positive AND negative
  * every exemption that keeps a check off TIMBR's own devices — anaphora,
    data listings, the staccato register, measurement qualifiers, negated
    modals — with the real copy that forced each one
  * the full derive/validate corpus as fixtures, both splits, run as a contract
  * the calibration statistics RECOMPUTED on every run, so a threshold that
    stops being true fails the suite instead of becoming folklore
  * the EFFECTIVE pass bar (the tell count at which pass flips), not the value
    of the threshold constant
  * the dropped triad check: that it is documented, and that it is not shipped
  * output shape (the orchestrator contract)
  * source mutation, with three no-op controls that MUST survive before any
    kill is trusted

Run: cd synthlint && python3 -m pytest test_synthlint.py -q
"""

import os
import re
import statistics
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import synth_config as C          # noqa: E402
import synthlint                  # noqa: E402
from synthlint import (           # noqa: E402
    burstiness,
    check_ai_vocabulary,
    check_burstiness,
    check_contrastive_frames,
    check_hedge_stacking,
    check_repeated_openers,
    check_transition_density,
    contrastive_frames,
    hedge_stacks,
    is_spec_list,
    repeated_opener_runs,
    run_synthlint,
    spec_list_fields,
    spec_list_rows,
    split_paragraphs,
    split_sentences,
    transition_openers,
    word_count,
)

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===========================================================================
# CORPUS — the derive / validate split, verbatim
# ===========================================================================
# Real TIMBR prose. Provenance:
#   vol11:*          Seattle-Magazine-Engine/runs/vol11_slu/copy.py, the S dict
#                    — shipped Seattle Series Vol 10 copy. Prose slots only;
#                    workout line-lists, kickers and titles are not prose and
#                    are excluded.
#   sample_issue:*   timbr_eval/sample_issue.json
#   magazine_pass:*  timbr_eval/fixtures/magazine_pass.json (SYNTHETIC test
#                    data by its own notice — every venue, person and figure in
#                    it is fabricated — but written in the owner-approved
#                    register, which is the property this module is calibrated
#                    against).
# Held here as literals rather than read from disk on purpose: these are the
# measurements every threshold in synth_config was derived from, and a corpus
# that can change underneath the suite is not a calibration record. It also
# keeps the suite green while other agents edit fixtures/.
#
# DERIVATION SPLIT — thresholds were tuned against these.
TIMBR_DERIVATION = {
    'magazine_pass:Nutrition':
        'Marisol Quintaine, 34, has ordered the same breakfast at the same counter for two years, and her reasons have nothing to do with discipline. She trains at six, starts a hospital shift at eight, and has about twenty minutes in between to put roughly 40 grams of protein somewhere it will stay. Four rooms in this city solve that problem for her. Three of them she found by accident.\n\nBrindlemoor Kitchen, 2140 Fenwold Avenue Northwest, Ballard. The turkey and white bean bowl is 41g protein, 29g carbs, 19g fat, $16. The smoked trout plate with rye is 39g protein, 31g carbs, 21g fat, $17. The egg and barley skillet is 42g protein, 28g carbs, 20g fat, $14. Average spend with coffee lands near $18. The room seats twenty-two, it is loud at the counter and quiet at the window, and the staff know their regulars by order rather than by name. Best on weekday mornings between seven and nine, before the stroller hour arrives and the queue reaches the door.\n\nQuintaine\'s morning is the trout plate, always, and her friends find this funny. "It is fish at seven in the morning, I know exactly how that sounds," she says. Her partner has stopped commenting. Her daughter, who is nine, calls it the sad breakfast and eats half of it anyway.\n\nOstrey Larder, 617 Harkness Street, Georgetown. The braised short rib and farro bowl is 43g protein, 32g carbs, 22g fat, $19. The chickpea and lamb plate is 40g protein, 30g carbs, 20g fat, $17. The cold roast chicken with beans is 38g protein, 27g carbs, 18g fat, $15. Average spend $20. The vibe is warehouse-adjacent and deliberately unfussy, six long tables and a chalkboard that gets rewritten twice a week, and the lunch crowd is half tradespeople and half whoever came off the 6am platform session down the block. Best between eleven and one on Tuesdays and Wednesdays.\n\nPriyal Odderly, 41, a night-shift charge nurse who trains after work rather than before it, eats the short rib bowl at eleven in the morning and calls it dinner. Her routine inverted four years ago and never inverted back. "The hardest part was never the food, it was finding anywhere that wanted to feed me at that hour," she says. She keeps a list on her phone. Ostrey is at the top of it.\n\nVantry Coffee Room, 3308 Ombrey Street, Wallingford. The cottage cheese and stone fruit bowl is 40g protein, 28g carbs, 18g fat, $13. The salmon toast with soft egg is 41g protein, 30g carbs, 22g fat, $16. The barley and yoghurt cup is 39g protein, 31g carbs, 19g fat, $12. Average spend $15. It is a coffee room first and a kitchen second, four seats at the window and a bench along the wall, and the espresso is the reason most people came the first time. Best from six to eight on weekday mornings, when the food comes out fastest.\n\nSallowmere Grill, 1122 Draycott Way, Beacon Hill. The chicken and rice plate is 44g protein, 33g carbs, 21g fat, $16. The grilled halibut with beans is 40g protein, 26g carbs, 20g fat, $21. The lentil and egg bowl is 38g protein, 32g carbs, 19g fat, $13. Average spend $19. The grill has been in the same family for two decades and it looks it, in the good way: vinyl booths, a counter with eight stools, and a television nobody watches. Best after seven in the evening, Thursday through Saturday, when the kitchen slows down enough to talk.\n\nQuintaine\'s list took two years to assemble and it is shorter than she expected. Her rule is not nutritional. A place has to be quick, it has to be on a route she already takes, and somebody there has to recognise her. The macros came second. "I could hit the numbers with a tub of powder and I would hate my life," she says. Her daughter is learning the orders. That is how a list becomes a habit in this city, one accidental Tuesday at a time.',
    'magazine_pass:Recovery':
        'Sleep is the recovery protocol. Everything else in this section is a rounding error against it.\n\n7 to 9 hours, on a consistent schedule, in a cold dark room. The evidence for this is stronger than the evidence for every modality below combined, and it is the one nobody sells.\n\nCut caffeine 8 hours out. Alcohol is a sedative and a sleep-architecture wrecker: it shortens the time to fall asleep and destroys the back half of the night. Two drinks on a Friday costs a Saturday session.\n\nSecond tier: protein and calories. Muscle repair is a construction job and it stops when the materials stop. Under-eating for a week undoes more than any cold plunge recovers.\n\nContrast therapy is next, and the verdict is narrower than the marketing. Thistlecross Barbell in Georgetown runs a contrast protocol three evenings a week: 3 minutes cold at 52 degrees, 10 minutes hot, twice through. Members sleep better on the nights they use it. Better sleep is a real outcome, and it is probably the whole mechanism.\n\nCold water immersion after lifting is a different matter. Cold blunts the inflammatory signal that drives hypertrophy adaptation, and blunting that signal within four hours of a hard set is working against the session. Plunge on rest days. Plunge after conditioning. Not after a heavy squat block.\n\nFoam rolling: 90 seconds per muscle group, and the effect is neurological rather than structural. Nothing is being released. Tissue is not being remodelled by a piece of foam. Range of motion improves for about 20 minutes and the discomfort drops, which is worth the 90 seconds and nothing more.\n\nMassage sits in the same category with better evidence and a higher price. Once a month is a reasonable line for most training loads.\n\nCompression boots are pleasant and the data is thin. Twenty minutes in a pair of boots is twenty minutes with the legs elevated and the phone out of reach, which has value that has nothing to do with compression.\n\nWalking is the most underrated line in this section. 8,000 to 10,000 steps on a rest day moves blood through repairing tissue without adding fatigue.\n\nIt costs nothing but the time. Nobody sells it, which is most of the reason nobody mentions it.\n\nSauna: better evidence than the boots, worse reputation, earned entirely by the people selling it. 15 to 20 minutes, two or three times a week, after training rather than before.\n\nThe cardiovascular adaptations are real. The calorie figures on the wall chart are not.\n\nIllness gets one rule, because most lifters get it wrong in the same direction. Symptoms above the neck: half volume, no top sets. Fever, or anything below the neck: nothing at all.\n\nThree days at 60 percent costs less than the fortnight a relapse takes.\n\nStretching gets a demotion. Static stretching before a session reduces force output for up to 30 minutes. After a session it does very little for soreness. Mobility work for a specific restricted joint is training, not recovery, and it belongs in the warm-up where it earns its place.\n\nNow the deload, which is the recovery tool with the strongest evidence and the lowest compliance rate in this city. Every fourth week: volume at 60 percent, intensity at 80, same movements. Skipping it is the most common reason an intermediate lifter stalls in March.\n\nHeart rate variability tracking deserves one paragraph and one warning. Trend lines over three weeks are useful. Single-day readings are noise, and a number on a screen at 6am has ended more good sessions than any injury.\n\nKelverstone Athletic Club in Ballard put a sauna in last year and its coaching staff track exactly one recovery metric: whether a member trained four times the week before. The simplicity is the point.\n\nRanked by evidence quality, the order is not close. Sleep. Food. Deload weeks. Then everything with a price tag attached.\n\nThe industry sells the last category hardest. That is the only tell that matters.',
    'magazine_pass:Supplements':
        'Creatine monohydrate: the one product in this category with a verdict that is not in dispute.\n\n5 grams daily. No loading phase. No cycling. No timing protocol worth the attention it gets.\n\nThe evidence base is the largest in sports nutrition and it has been stable for two decades. Output rises in repeated high-intensity sets. Training volume rises with it. That is the whole mechanism, and it is enough.\n\nCost: roughly $25 for a three-month tub of the unflavoured monohydrate. Anything sold at four times that price with a proprietary blend on the label is selling the label.\n\nVitamin D is the second entry and the local one. Seattle sits at 47 degrees north, and between October and April this city does not produce meaningful amounts through skin at all. Blood testing is the only sensible way in. Numbers first, dose second, retest at 12 weeks.\n\nNobody needs a megadose. 1000 to 2000 IU daily covers most deficient adults, and the 50,000 IU weekly protocols belong to clinical correction, under supervision, with a lab behind them.\n\nMagnesium glycinate. Not oxide. Oxide is cheap because it is poorly absorbed, which is a fact about chemistry rather than a marketing position.\n\n400mg, taken in the evening. The sleep effect in deficient adults is real and modest. In adults who are not deficient it is close to nothing, which is the sentence most labels leave off.\n\nProtein powder is a convenience, not a supplement. The target is 0.7 to 1 gram per pound of bodyweight per day, and food gets most people most of the way there. Powder closes a gap. It does not open a door.\n\nWhey isolate for the lactose-sensitive. Whey concentrate for everyone else, at two-thirds the price. Casein at night is optional and the difference is small enough to ignore.\n\nBeta-alanine earns a qualified yes and one caveat that is not about safety. 3 to 5 grams daily raises muscular carnosine over four to six weeks, with a measurable effect in efforts between one and four minutes. Outside that window the effect disappears. The tingling is harmless and unrelated to whether it works.\n\nCaffeine is the most reliable performance drug in the building and it is legal, cheap, and already in the fridge. 3mg per kilogram of bodyweight, 45 minutes out. Past 6mg per kilogram the returns turn negative and the sleep debt starts compounding.\n\nNow the ones this magazine will not endorse. Collagen for joint pain: the trials are small, industry-funded, and inconsistent. Testosterone boosters: no product sold over a counter in this city has moved total testosterone in a healthy adult in any trial worth citing. Fat burners: caffeine, priced at a 900 percent markup, with a botanical on the front.\n\nGreens powders deserve their own line. 40 dollars a month for a scoop that contains a rounding error of actual vegetables, sold on the promise of covering a diet nobody has audited. Eat a vegetable. It costs less.\n\nThe honest summary of this category is short. Two products with strong evidence, three with narrow and specific uses, and an industry built on the eleven percent of buyers who never open the second tub.\n\nBuy the boring one. It is the only one that works.',
    'magazine_pass:Training':
        'Winter in Seattle is a volume season, and the strength rooms that stay busy through it program differently from the ones that empty out. Racks that sit idle at four in the afternoon in July are three deep by five in January. That pattern held at every facility surveyed for this issue, and it held hardest at the older rooms in the industrial south end.\n\nThe Ferrowgate Human Performance Lab, an independent research group attached to Ombrey College, tracked 214 intermediate lifters across two Seattle facilities for 16 weeks and released the session logs in November. Training volume rose 31 percent between October and February. Adherence rose with it, from 61 percent of planned sessions to 78 percent. "The seasonal pattern is not motivation, it is daylight and schedule," says Dr. Imelda Vosskirk, who directs the lab. "There are fewer competing hours in this city in winter, so the extra sets are simply available."\n\nThat availability is the argument for a base block. A base block is not a peak block. It is the eight to twelve weeks in which an intermediate lifter accumulates the work that a later intensity phase will express, and the research group\'s logs suggest most lifters in the sample were skipping it entirely.\n\nCoaches in the city have started to say the same thing out loud. At Thistlecross Barbell in Georgetown, the coaching staff moved the entire membership onto a shared four-day template in October, a change the head of programming, Wendell Marnowitz, described as overdue. "Everybody wanted to test a single," Marnowitz said. "Nobody wanted the ninety sessions that make the single possible."\n\nThe template below is the one Marnowitz uses, reproduced with the room\'s permission and checked against the lab\'s volume figures. It is intermediate, hypertrophy-focused, and written for a full gym. Four days: Monday upper, Tuesday lower, Thursday upper, Friday lower. Rest between all working sets is 45 to 60 seconds, held static across the block. Exercises rotate weekly, so nothing repeats inside the four-week cycle.\n\nThistlecross Barbell, 5460 Hallowmere Street South, Georgetown, opens at five on weekdays and runs coached base-block sessions at six and at noon. The room\'s other change was administrative. Lifters on the template log their working sets on a shared board by the chalk bin, which is how the staff found the week 4 attrition problem in the first place. Kelverstone Athletic Club in Ballard copied the board in December and reported the same drop.\n\nWeek 1 establishes the baseline. Monday upper: Bench Press 4x6, Chest-Supported Row 3x8, Seated Overhead Press 3x10, Rope Pushdown 3x12, Hammer Curl 3x12. Tuesday lower: Back Squat 4x6, Romanian Deadlift 3x8, Walking Lunge 3x10, Seated Leg Curl 3x12, Standing Calf Raise 4x15. Thursday upper: Incline Dumbbell Press 4x8, Chest-Supported Row 3x10, Lateral Raise 3x15, Overhead Triceps Extension 3x12, Incline Curl 3x12. Friday lower: Trap Bar Deadlift 4x5, Hack Squat 3x10, Hip Thrust 3x12, Leg Extension 3x15, Seated Calf Raise 4x15. Warm-up is one specific ramp per session. Cool-down is one.\n\nWeek 2 adds volume, not load. Every primary movement takes one additional working set at the week 1 weight, which puts the four-day total at 52 hard sets against week 1\'s 44. The lab\'s logs are unusually clear on this point: of the 214 lifters, the group that added sets before adding load reported 19 percent fewer missed sessions over the following month than the group that did the reverse.\n\nWeek 3 raises intensity. Sets return to the week 1 count and the primary lifts move up by roughly 5 percent, with the rep ranges tightening: Bench Press 5x4, Back Squat 5x4, Trap Bar Deadlift 4x3, and the accessory work holding at 3x10 to 3x12 through the week. This is the only week in the cycle where a lifter should expect to finish a session with something left in reserve on the last set, because the reserve is the point of the arc.\n\nWeek 4 deloads. Volume drops to roughly 60 percent of week 2 and intensity to 80 percent of week 3, which in practice means the same movements at 3x6 with a weight the lifter could take for ten. Coaches lose more athletes at this stage of a block than at any other, and the reason is boring rather than psychological. A deload feels like nothing. Nothing is what it is supposed to feel like.\n\nVosskirk is careful about what the data does not say. The Ferrowgate sample was intermediate, it was self-selected, and it ran for 16 weeks, which is long enough to see adherence and too short to see much else. "Anybody who tells a room this is settled science is selling something," she said. Two commercial programming companies contacted for this piece declined to comment on their own volume recommendations, and a third did not respond before publication.\n\nWhat the logs do settle is narrower and more useful. Volume accumulated in the dark months shows up in the spring numbers, adherence follows availability rather than enthusiasm, and the block that gets skipped is always the unglamorous one in the middle.',
    'sample_issue:Culture':
        "Seattle's gyms are getting more serious. The signal is in the equipment orders.\n\nRogue Fitness reported a 34% increase in commercial barbell orders to Washington State facilities in 2025. At Rainier Barbell on 12th Avenue, the squat rack count went from 6 to 18 between January 2024 and January 2026. At Iron Works in Fremont, membership applications tripled after they removed the cardio floor and replaced it with platforms.\n\nThis is not a story about equipment. This is a story about what the city decided to want.\n\nThe shift started in South Lake Union. Tech workers with disposable income and data-driven approaches to everything started applying the same rigour to training. HRV tracking. Progressive overload spreadsheets. Coaches on retainer.\n\nIt spread. Beacon Hill got a strength-only gym in March 2025. Capitol Hill has four now. Queen Anne added one in January 2026.\n\nThe boutique cardio studios that defined Seattle fitness five years ago are either converting or closing. Not because they failed. Because the city moved on.",
    'sample_issue:Nightlife':
        'After the gym, before the bar: Fuel House on Eastlake.\n\nHigh protein, low drama. Counter service. No wait.\n\nFor the bar: Navy Strength in Belltown. Serious cocktails. Loud enough that you do not need to perform conversation.\n\nQuieter option: Canon on Pike. The whiskey list is the point. The barstools do not move. That is the idea.\n\nThursday night is the night. The training crowd moves as one.',
    'sample_issue:Nutrition':
        "Jade Kim orders the same thing every Tuesday: the black sesame smoothie and a side of turkey avocado toast. She started coming to Bluebird Provisions on Capitol Hill in January because it was on her walk to Rainier Barbell. Now it is part of the training routine.\n\nBluebird Provisions, 123 Broadway E, Capitol Hill. Turkey Avocado Toast (38g protein, 29g carbs, 18g fat, $14). Black Sesame Protein Smoothie (41g protein, 32g carbs, 22g fat, $12). Egg White Scramble Bowl (42g protein, 28g carbs, 19g fat, $16). Best: weekday 7-9am.\n\nFuel House, 456 Eastlake Ave E, South Lake Union. Steak Power Bowl (44g protein, 31g carbs, 21g fat, $18). Chicken Rice Stack (40g protein, 33g carbs, 20g fat, $15). Tuna Poke Build (39g protein, 28g carbs, 22g fat, $16). Best: lunch 11am-1pm.\n\nGreen District, 789 Queen Anne Ave N, Queen Anne. Steak + Egg Protein Salad (41g protein, 27g carbs, 23g fat, $17). Grilled Chicken Power Bowl (43g protein, 30g carbs, 19g fat, $16). Turkey Quinoa Stack (38g protein, 32g carbs, 21g fat, $15).\n\nBig Mario's, 1009 E Pike St, Capitol Hill. Post-workout high-protein pizza. Pepperoni + Egg Slice (39g protein, 31g carbs, 20g fat, $9). Chicken Pesto Slice (42g protein, 29g carbs, 22g fat, $10). Best: post-9pm Friday.",
    'sample_issue:Recovery':
        'Active recovery outperforms passive rest.\n\nCold exposure. Cascade Athletic Club on Capitol Hill runs contrast therapy: 3 minutes cold (50 degrees F), 10 minutes hot, repeat twice. Weekly. Members report improved HRV within 6 weeks.\n\nSleep is the non-negotiable. 7-9 hours. HRV drops 18% on sub-6-hour nights per Whoop data from 12,000 users.\n\nFoam rolling: 90 seconds per muscle group post-session. Not instead of sleep. In addition to.\n\nThe vibrant recovery community at Fremont Hot Yoga adds breathwork sessions Tuesdays.',
    'sample_issue:Social':
        "Mia Tanaka, 29, coordinates the largest informal lifting crew in South Lake Union. Twelve people. Five nationalities. One shared Google Sheet tracking PRs.\n\n'We started because the gym was intimidating alone,' she says. 'Now the gym is the social event.'\n\nThe group trains together Tuesday and Thursday evenings at Rainier Barbell. After: dinner at Fuel House on Eastlake. The ritual is as locked as the programme.\n\nThis is the pattern across Seattle right now. Fitness as the organising logic of social life. The Thursday night dinner reservation built around when the squat session ends, not the other way around.",
    'sample_issue:Supplements':
        'Creatine monohydrate. 5g. Daily. Nothing else comes close.\n\nThe evidence is not ambiguous. 700+ peer-reviewed studies. Increases phosphocreatine stores. Improves output in high-intensity sets. Costs $25 for three months.\n\nMagnesium glycinate. Not oxide. 400mg before bed. Sleep quality improves in 3-4 weeks. Delve into the research if you want the mechanism.\n\nProtein powder: only if whole food falls short. Target 0.8g per pound of bodyweight from food first. Powder fills the gap.\n\nEverything else is marketing. Budget accordingly.',
    'sample_issue:Training':
        "Seattle's strength culture has a new centre of gravity. It is not CrossFit. It is not Pilates. It is the barbell.\n\nRainier Barbell on 12th Avenue Capitol Hill opened in January 2026 with 18 squat racks and a six-month waitlist. Matt Torres, 31, head coach, says the demand surprised even him. 'We thought we'd fill 40% capacity in year one. We hit 90% by March.'\n\nThe numbers support it. USA Weightlifting registered 23% more competitive athletes in Washington State in 2025 than 2024. Seattle Parks and Recreation added strength programming to 11 community centres this year, up from 4 in 2023.\n\nThis is not a fitness trend. This is a structural shift in how the city moves.\n\nWeek 1 Baseline:\nMonday Upper: Bench Press 4x6, Barbell Row 3x8, Overhead Press 3x10, Tricep Pushdown 3x12.\nTuesday Lower: Back Squat 4x6, Romanian Deadlift 3x8, Leg Press 3x10, Leg Curl 3x12.\nThursday Upper: Incline Dumbbell Press 4x8, Cable Row 3x10, Lateral Raise 3x12, Bicep Curl 3x12.\nFriday Lower: Deadlift 4x5, Bulgarian Split Squat 3x10, Leg Extension 3x12, Calf Raise 4x15.",
    'vol11:anchor_venue':
        'At 311 Terry Ave N, Flow Fitness opens at 5:30am on weekdays, and the weight floor is why this pair belongs here: full dumbbell sets, cable systems, and a functional training area with room to hinge. Sixty classes a week run around it — Strength, FlowFIT, FF Cycle, FlowBarre, WERQ, Yoga — for the days the structure helps. A dumbbell hinge and a cable pull-through cover most of what glutes and hamstrings actually ask for. Load them honestly. Afterward there is a dry sauna and towel service, and validated parking in the 321 Terry Ave N garage before 8:30am, after 4pm, or all weekend. Classic runs $119.99 a month and weekdays run to 10pm. Do the heavy half here.',
    'vol11:back_left_body':
        'A new issue every month — one neighborhood, one pair, one standard. Nothing else changes.',
    'vol11:back_right_body':
        '30% off any digital purchase at TIMBR — guides, programs, and single issues. It applies at checkout, nothing to sign. The library is at timbr.fit.',
    'vol11:city_intro':
        'South Lake Union runs from Denny Way north to the lake, and this volume walks two doors. On Terry, a weight floor of dumbbells and cables with sixty classes a week around it. On Thomas, eighteen Megaformers and a count that refuses to hurry. Load first. Then coffee, twice: an espresso bar named for its brew temperature, and a green-tiled room on 9th that locks the door at four. Glutes and hamstrings take load two ways — heavy, then slow — and six minutes of Thomas Street separate the rooms that do each. The next two pages walk both doors: addresses, hours, the terms that matter. Turn the page. None of this was estimated.',
    'vol11:counter_venue':
        'MOOV SLU is the counterweight at 777 Thomas St, six mostly flat minutes from the weight floor: eighteen Megaformers, every one the current sixth-generation Lagree M3K, running the genuine method since 2021. Nothing swings, nothing rests. Slow eccentric work asks a hamstring a different question than a heavy set does. Butts & Guts is the obvious booking here; Full Body, Advanced, Intro to Lagree, Upper Body, and Upper Body + Extra Core fill the rest. The schedule runs in blocks, not straight through: Monday is 6 to 9am, 11am to 1pm, then 4 to 8pm. Flow loads the work. This room is where it stays.',
    'vol11:cover_body':
        'Seattle trains early and lines up for coffee after — the lake, the hills, the gray morning on foot. Vol 10 carries glutes and hamstring through South Lake Union: fifty minutes of work, a ristretto on Terry, and the right rooms for the night off. It reads less like a workout and more like a city worth exploring. Train like a local — wherever you are.',
    'vol11:editor_body':
        "Let's be straight about what this is, and what it isn't. It isn't a transformation or a six-week miracle — those promises sell magazines, and they don't survive a real Tuesday. What's here is one muscle pair, glutes and hamstring, programmed across four weeks you can actually run: fifty minutes a session, all levels, form before load, start high and end low, and stop the moment something hurts. We wrote it the way a good coach writes a plan — to be followed, not admired. Then we did the part most guides skip: we set the work into a real neighborhood, South Lake Union, because training never happens in a vacuum. It happens in a city, on a morning, between two doors six flat minutes apart: a weight floor on Terry that opens at 5:30 on weekdays, and eighteen Megaformers on Thomas that refuse to hurry. Glutes and hamstrings take load two ways, heavy and slow. Four weeks run both. Then coffee, twice, and both counters shut at four — go early. When the work is done: mini-golf in a converted auto showroom, oxtail pho on Terry, a heated patio on the water. So Vol 10 reads less like a workout and more like the map of one honest morning: the session, the plate, the people, and the place around them. The deal holds: we write the session, the city is yours to walk, the work is yours to do. One pair, one neighborhood, one standard we won't dress up — that's the series, and this is the tenth one.",
    'vol11:editor_closer':
        "Every gym, café, and address in here passed a live check before we printed a word — that's the standard. The rest is on you: show up, hinge, sleep, come back three days later. Train like a local. — TIMBR",
    'vol11:editor_standfirst':
        'Volume ten walks South Lake Union — glutes and hamstring, four honest weeks, zero shortcuts to sell.',
    'vol11:micronutrients':
        'MICRONUTRIENTS. Four compounds that protect the work: vitamin D, magnesium, zinc, iron. Seattle is dark half the year. Go get the bloodwork.',
    'vol11:nutri_carb':
        'CARBOHYDRATE. The fuel macro. Heavy hinging burns stored fuel fast, and an empty tank shows up in week three. Earn them on training days. Pick whole carbs — oats, brown rice, potatoes, beans, fruit — that digest slow.',
    'vol11:nutri_fat':
        'FAT. The hormone macro. It carries vitamins A, D, E, and K — cut it to zero and fat-soluble micros can’t absorb. Hold 0.3–0.4g per pound a day. Choose whole sources: avocado, nuts, olive oil, salmon.',
    'vol11:nutri_protein':
        'PROTEIN. The repair macro. Aim for 0.7–1g per pound of bodyweight a day, spread across meals, and land 30–40g inside two hours of the last set. Eggs, chicken, salmon, Greek yogurt — build each plate on it.',
    'vol11:nutri_standfirst':
        'Slow eccentrics tear the biggest muscle you own. Three macros rebuild it: protein, carbs, fat. Four micros protect it — D, magnesium, zinc, and iron. The floor, not the fad.',
    'vol11:post_meal_body':
        'A ~180g sockeye fillet, skin crisped in a dry pan, over ⅔ cup of jasmine rice. No oil needed: the fish brings its own. It lands 40g protein, 30g carbs, 15g fat.',
    'vol11:post_stack_body':
        'Magnesium glycinate before bed, gentler on the gut than oxide. Vitamin D3 through the winter, when the sun is down by five.',
    'vol11:pre_meal_body':
        '~330g of liquid egg whites scrambled soft, with a 55g slice of sourdough — it lands 40g protein, 30g carbs. Fast fuel. Nothing heavy at the first hinge.',
    'vol11:pre_stack_body':
        'Caffeine sharpens the nervous system. Creatine refills phosphate stores. L-citrulline opens blood flow. ',
}


# HELD-OUT SPLIT — never inspected while a threshold was being chosen. The
# finished module was run against these cold. All six passed at 100.
TIMBR_HELDOUT = {
    'magazine_pass:Culture':
        'The cheapest room in a Seattle neighbourhood is usually the last one anybody photographs and the first one leased out from under the people using it. Strength gyms in this city have spent a decade in buildings nobody else wanted, on floors poured for light manufacturing, behind doors that still carry the old tenant\'s name in vinyl. That decade is closing. The closing shows up in the paperwork long before it shows up on the door.\n\nPublic records list 41 industrial parcels in Georgetown, SoDo and Interbay that changed ownership between January 2023 and January 2026. Nine carried a fitness tenant at the time of sale. Six of those nine are now vacant, converted, or held for a use the previous tenant could not match, according to filings compiled by the Ombrey College urban research seminar, which has tracked the corridor since 2019.\n\nThe rent numbers are the whole story and they are not complicated. Industrial space in the corridor leased at an average of 94 cents per square foot per month in 2019. The same class of space leased at $1.71 in the fourth quarter of 2025, an 82 percent increase over six years, in a category of tenant whose revenue per square foot does not move at that speed. A strength gym sells time under a barbell. There is a ceiling on how much time fits in a room.\n\nQuarrenden Barbell held 8,400 square feet on a side street in SoDo for eleven years and closed in March. "We were never going to out-bid a distribution tenant, and everyone in the building knew it two renewals ago," says Rosalind Thackerill, who owned the room and now coaches out of two rented slots elsewhere. Thackerill is precise about the arithmetic rather than bitter about it. The room needed 310 paying members at $89 a month to survive the new figure. It had 244.\n\nThat gap, roughly a quarter of a membership base, turns up repeatedly in the closures the seminar documented. It is small enough to look survivable in a spreadsheet and large enough to be unbridgeable in a neighbourhood where the next hundred members would have to come from somewhere.\n\nThe buildings do not sit empty. Two of the six became last-mile logistics space, one became a climbing facility with a different capital structure behind it, and one is under permit review for offices. A representative for the ownership group holding two of the parcels declined to discuss an active listing. The brokerage that handled three of the sales did not respond to two requests for comment before publication.\n\nWhat replaced the closed rooms is where the city\'s fitness culture actually gets decided, and it is not one thing. Kelverstone Athletic Club in Ballard took on 130 of Quarrenden\'s members and added a second platform bay to hold them. Marrowfen Rowing Club in Eastlake, which pays a fraction of the corridor rate because it sits on a lease signed in 2011, has a waitlist of 200 and no room to grow into. The pattern is consolidation, not disappearance: fewer rooms, larger, further from the neighbourhoods that used them.\n\n"The equipment survives every one of these closures, it just ends up further from the bus," says Corwin Delabole, a commercial broker who has handled industrial leasing in the corridor for nine years and who tracked six of the nine tenancies. Delabole notes that transit time is the variable operators underrate. A room 20 minutes further out loses the members who trained on the way home from work, and those members are the ones who paid every month without negotiating.\n\nThe seminar\'s data supports the point in a narrow way. Among the 244 members of the closed SoDo room, 61 percent joined a new facility within four months. That figure sounds like resilience. It is also a 39 percent attrition rate in a population that had already proved it would pay to train, which is the most reliable population a gym can hold.\n\nNone of this is a Seattle story alone, and the seminar is careful to say so. Comparable industrial corridors in Portland and Oakland produced similar figures over similar windows, and the researchers describe the local variation as modest. What is local is the timing. This city\'s strength scene was built almost entirely inside a single class of building, in a single stretch of years, by operators who signed the cheapest leases available at the time. The leases were the culture\'s infrastructure. They were never going to be permanent, and almost nobody planned as though they were temporary.\n\nThe rooms that survived did one of two things. They bought, which almost none could, or they signed long in a year when signing long looked overcautious. Thistlecross Barbell in Georgetown signed a fifteen-year lease in 2018 and was called reckless for it at the time. That contract is the only reason the room still has a floor.\n\nThe next test arrives in 2027, when a cluster of the corridor\'s remaining leases comes up together. The seminar counts eleven fitness tenancies inside that window. Nothing about the rent trend suggests those renewals will be quiet, and nothing about the last three years suggests the city will notice until the vinyl comes off the doors.',
    'magazine_pass:Nightlife':
        'Thursday is the night in this city and it has been for years. Friday belongs to people with a commute.\n\nThe training crowd moves in a fixed order, and the order is worth stealing.\n\nStart at Fennimore Tavern, 900 Sedgeby Street, Belltown. Doors at four. The kitchen runs until midnight, which in this city is a genuine service and not a small one. The bar list is short and unapologetic: six beers, four cocktails, no menu of forty things nobody orders. Loud enough to skip the small talk. Quiet enough at the back four tables to hear a conversation.\n\nOrder the grilled chicken plate. 44 grams of protein at 7pm on a Thursday is the difference between a good Friday session and a wasted one.\n\nSecond stop: Corbie Bar in Fremont, three blocks from the water and up a staircase nobody photographs. Cocktails are the point here and they are made by people who take them seriously without saying so. The whiskey list runs to 60 bottles. Prices sit between 14 and 18 dollars, which is honest for what arrives.\n\nThe room holds about forty. Go before nine or stand.\n\nThird, and only if the night has earned it: The Halvard Room in Pioneer Square. Doors at nine. Music until two. This is the one room in the rotation where the volume makes conversation impossible, and that is the correct choice for a night that has run out of things to discuss.\n\nThe rules for the whole circuit are simple and they are not negotiable.\n\nEat first. A training week does not survive four hours of drinking on an empty stomach, and the person who eats at the first stop is the person still standing at the third.\n\nTwo drinks is the line that costs nothing. Three costs Saturday morning. Five costs the weekend and most of Monday.\n\nWater between rounds. Not a wellness tip, just arithmetic.\n\nSunday is not a night out. Sunday is the day the week gets planned, and every crew in this city that has lasted more than two years protects it.\n\nMarrowfen Rowing Club in Eastlake runs the best version of this. Its crews finish on the water at seven on Thursday, eat at Fennimore by eight, and nobody is out past eleven. The next morning at six there are twelve people on the dock.\n\nThe venues in this rotation are not the loudest rooms in Seattle and they are not the cheapest. They are the three that let a person who trains hard have an actual social life without paying for it twice.\n\nThursday. Fennimore, Corbie, Halvard. Home by midnight if the week matters.\n\nNobody does the whole circuit twice in one month. That is the only rule anyone breaks.',
    'magazine_pass:Social':
        'Odalys Brenmark, 27, keeps the least glamorous document in Seattle fitness on her phone, and eleven people plan their week around it. It is a shared spreadsheet with four columns: name, day, session, and a box for whoever is bringing the car. Her friends call it the ledger. She calls it the only reason any of them still train together after three years.\n\nThe group formed the way most of them do, out of a coincidence nobody planned. Four of them joined Pennwhistle Run Club in Wallingford in the same month, discovered they were all bad at the same hill, and started meeting on Sundays because Sunday was the day none of them had anything else. The run club is still the anchor. The spreadsheet is the thing that survived two moves, one baby, a broken foot and a job in Tacoma.\n\nWhat makes it work is that it asks for almost nothing. Nobody is expected at every session. There is no streak to protect and no chart of who showed up most, which Brenmark removed from the file in the first year after watching two people quietly stop replying. "The moment it turned into a scoreboard, half of us were losing," she says. Her rule now is that the ledger records plans, not performance.\n\nThe car column is the part outsiders find strange and the group finds essential. Three of the eleven do not drive. Two of the sessions are at a room in Georgetown that is forty minutes by bus and twelve by car, and a training plan that ignores that arithmetic is a training plan for whoever already owns a vehicle. Brenmark\'s own week is built around the two mornings her neighbour drives past her block anyway.\n\nPriyal Odderly joined the group last spring through a coworker and immediately broke its rhythm, because a night-shift nurse cannot make a Sunday morning. The group did not adjust for her. It added a row. There is now a Wednesday afternoon slot with two names in it, and on most weeks it is the smallest session on the sheet and the one that has never once been cancelled.\n\nMoney sits in the file too, in a column that appeared one week without ceremony. Six of the eleven are on the cheapest membership tier at Kelverstone Athletic Club, two pay drop-in rates when they can, and three have a home setup and meet the others outside. Nobody is asked which category they are in. The column names a place and nothing else, so nobody arrives at a door that will cost them eighteen dollars they had not planned for.\n\nThe social part, the part that made it last, happens after. Sunday sessions end at a table at Vantry Coffee Room in Wallingford, four seats and a bench that the group has taken over so often the staff push two tables together without being asked. Some weeks nine people come to the table and two came to the run. Brenmark counts that as a full week.\n\n"People think the hard part is the training," she says. "The hard part is being the person who sends the message on a Tuesday when nobody has replied since Friday." She has been that person for three years. In April she added a second name to the top of the ledger, a rotating slot, because being that person forever is how a group ends.\n\nThe document is not clever. It is a spreadsheet with eleven names and a column for a car, and it has outlasted three gym memberships, two apps and one very expensive wearable. In a city where most training is solitary by default, the ledger is a small piece of infrastructure that happens to be made of people.',
    'vol11:anchor_cafe':
        "Six minutes and three tenths of a mile from the weight floor, 203°F Coffee Co sits at 610 Terry Ave N and takes its name from a number: 203 degrees Fahrenheit, the temperature it brews at. The menu is Northern Italian and ristretto-first, which means smaller, denser, and far less forgiving of a bad shot. Order the 203 ESP, the house espresso blend, and take its tasting notes at face value rather than as a pitch: chocolate, cherry, almond, vanilla. Look down while it lands — the concrete floor is stamped with the logo. The counter runs seven days and closes at 4pm, so this is a morning stop, which suits a session that started at 5:30. Sit for ten minutes. Hamstrings aren't due anywhere.",
    'vol11:counter_cafe':
        "Three minutes from MOOV, at 234 9th Ave N, Evoke Cafe Bar runs green subway tile, wood-crate shelving stacked with plants, and a La Marzocco on the counter. Mikayla Benedict owns it, and House of Eve besides. The avocado toast and the cinnamon swirl croissant are the repeats, and they're the right two things to order after Lagree. Open 7am weekdays, 8am weekends, shut by four either way. Take the long way back.",
    'vol11:night_body':
        "The Night Off\nSouth Lake Union · Westlake Avenue · Fairview Avenue\n\nSome nights the smartest recovery is a night off. South Lake Union has the rooms. Flatstick Pub runs nine holes of indoor mini-golf and its own game, Duffleboard, in 11,000 square feet of old auto showroom, to 1am on weekends. Ba Bar has poured oxtail pho on Terry since 2011, its vegan window, Ba Bar Green, at the same address. Duke's Seafood does halibut and salmon seven ways on a heated covered patio, seaplane and Queen Anne views, to 11pm. Rest is part of the program. So is showing up for the people you train near. Take the night — cheers.",
}


# Adversarial corpus: prose written to read like LLM-generated fitness and
# lifestyle copy. Severity and tell-mix deliberately varied — some blatant,
# some carrying nothing but a flat rhythm.
#
# DERIVATION SPLIT.
ADV_DERIVATION = {
    'adv01_vocab_blatant':
        "In today's fast-paced world, finding time for fitness can feel like an impossible task. But here's the thing: it doesn't have to be.\n\nStrength training plays a crucial role in long-term health, and Seattle boasts a wide range of state-of-the-art facilities designed to meet you wherever you are. Moreover, the city's fitness community showcases what happens when passion meets accessibility.\n\nLet's dive in. When it comes to building a sustainable routine, consistency underscores everything. Furthermore, a plethora of studies confirm that the best programme is the one you actually follow.\n\nIn conclusion, the path forward is simpler than you think. It's important to note that progress is rarely linear, and that's perfectly okay.\n",
    'adv02_transitions':
        "Seattle's strength scene has changed a great deal over the past five years. New rooms have opened in Georgetown and Ballard, and older gyms have added platforms to keep pace with demand.\n\nMoreover, the shift has been driven as much by cost as by taste. Industrial rent has climbed steadily since 2019, and operators who signed short leases have felt it first.\n\nFurthermore, the membership base itself has shifted. Younger lifters arrive with more information and less patience, and they expect coaching rather than equipment.\n\nAdditionally, the equipment itself has become a differentiator. A room with four platforms and a competition bar draws a different crowd than a room with twenty treadmills.\n\nOverall, the picture is one of consolidation rather than decline. In summary, fewer rooms are serving more people, and the rooms that survive are the ones that bought early or signed long.\n",
    'adv03_flat_subtle':
        'Recovery is the part of training that most lifters get wrong. The work happens in the gym but the adaptation happens afterward. Sleep is the single largest lever available to anyone who trains regularly. Seven to nine hours a night gives the body the window it needs to repair. Nutrition is the second lever and it matters nearly as much. Protein intake should be spread across the day rather than concentrated. Carbohydrate replaces the fuel that hard sessions burn through. Hydration supports every process that recovery depends on. Active recovery keeps blood moving without adding meaningful fatigue. A short walk on a rest day is often better than complete stillness. Foam rolling can reduce the sensation of tightness after a heavy session. Massage offers similar benefits with a longer duration of effect. Cold exposure has become popular but the evidence remains genuinely mixed. Heat exposure appears to offer cardiovascular benefits that are worth considering. Deload weeks are scheduled reductions in volume and intensity every fourth week. Most intermediate lifters skip them and stall as a direct result.\n',
    'adv04_openers':
        'Progressive overload is the foundation of every effective training programme in existence.\n\nThis means that the demands placed on the muscle must increase over time. This allows the body to adapt to a stimulus it has not encountered before. This ensures that progress continues rather than stalling after the first few months. This creates a training environment where improvement is the expected outcome.\n\nIt is worth understanding what overload actually looks like in practice. It is not simply about adding weight to the bar every single session. It is about accumulating more quality work over a training block. It is a longer game than most beginners expect it to be.\n\nThese principles apply across every experience level and every training goal. These adjustments should be made gradually rather than all at once. These small changes compound into significant results over a period of months.\n',
    'adv05_contrastive':
        "Strength training isn't just about lifting heavy things. It's about building a body that serves you for decades.\n\nThe modern gym is not just a place to exercise, it's a community hub where people find accountability and support.\n\nNutrition isn't just about hitting macros. It's not about restriction, it's about building a relationship with food that lasts.\n\nRecovery is more than just rest days. It's not merely the absence of training but rather the active process through which adaptation occurs.\n\nThe goal isn't just to look better. The goal is to move better, feel better, and live longer.\n",
    'adv06_hedges':
        'Creatine supplementation may potentially offer benefits for individuals engaged in resistance training. The research could possibly suggest an effect on high-intensity output, though it is possible that individual responses might vary considerably.\n\nIt may be that the timing of the dose is somewhat less important than the total daily intake. Some evidence seems to possibly indicate that a loading protocol perhaps offers a faster route to saturation.\n\nBeta-alanine could perhaps provide a modest benefit in efforts lasting between one and four minutes. It is possible that the tingling sensation might be related to the mechanism, although it may possibly be incidental.\n\nVitamin D might potentially matter more at northern latitudes. It could conceivably be worth testing before supplementing, though this may possibly depend on the individual.\n',
    'adv07_mixed_mid':
        "Seattle's fitness landscape has evolved considerably in recent years, and the transformation shows no signs of slowing down.\n\nWhen it comes to finding the right gym, there are a myriad of factors to consider. Location matters. Equipment matters. Coaching matters most of all.\n\nMoreover, the rise of boutique studios has fundamentally changed what people expect from a training environment. These spaces offer curated experiences that traditional gyms struggle to match.\n\nIt's worth noting that this isn't just a Seattle phenomenon. Cities across the country are seeing similar patterns emerge.\n\nAt the end of the day, the best gym is the one you'll actually go to. Essentially, consistency beats novelty every time.\n",
    'adv08_subtle_flat':
        'The four-day upper-lower split remains one of the most reliable structures available. It divides the week into two upper-body sessions and two lower-body sessions. Each session includes one primary compound movement and three or four accessories. The primary movement is trained in a lower rep range for strength development. The accessories are trained in a higher rep range for volume accumulation. Rest periods between working sets should sit around ninety seconds for accessories. Primary lifts benefit from a longer rest period of two to three minutes. Progression is managed by adding a small amount of weight each week. Alternatively, an additional repetition can be added at the same load. Deload weeks should be scheduled every fourth or fifth week of training. Volume is reduced by roughly forty percent during a deload week. Intensity is held closer to normal to preserve neural adaptations. Furthermore, the split accommodates most schedules without much difficulty. It requires four sessions rather than five or six each week.\n',
    'adv09_listicle':
        "Picture this: it's Monday morning and you're standing in front of a cutting-edge gym, ready to begin.\n\nHere are five things that will transform your training.\n\nFirst, prioritise compound movements. These exercises play a vital role in developing full-body strength and are a testament to the efficiency of classical programming.\n\nSecond, track your progress. Without a doubt, the lifters who write things down make faster progress than the ones who don't.\n\nThird, sleep more. Needless to say, recovery is where the magic happens.\n\nFourth, eat enough protein. A wide array of studies underscores the importance of adequate intake.\n\nFifth, be patient. At the end of the day, the results come to those who stay consistent.\n\nTo sum up: the fundamentals work. There's no need to overcomplicate things.\n",
    'adv10_brand_subtle':
        "We believe movement should feel like something you look forward to. Our studios are designed around that idea. Every class is built to meet you where you are, whatever your starting point.\n\nOur coaches bring years of experience to every session they lead. They understand that progress looks different for everyone. They adjust the work to fit the person rather than the other way around.\n\nThe space itself was designed with intention. Natural light fills the main floor throughout the day. Equipment is arranged to encourage movement rather than crowding. The locker rooms were built to feel calm rather than functional.\n\nMembership is designed to be flexible. You can pause at any time without penalty. There are no long-term contracts and no cancellation fees.\n\nWe'd love to have you. Book a free introductory session and see how it feels.\n",
    'adv11_supp_mid':
        "Supplements occupy a complicated place in the world of fitness, and separating signal from noise is not always straightforward.\n\nCreatine monohydrate is the one product that consistently delivers. It's a testament to good science that a supplement this cheap remains this effective. Five grams a day is all that's required.\n\nProtein powder plays a crucial role for those who struggle to hit their intake through whole food alone. It's important to note that powder is a convenience rather than a necessity.\n\nBeta-alanine may potentially help in the one-to-four minute range, though it could possibly be less useful outside that window.\n\nMoreover, the supplement industry showcases a groundbreaking talent for marketing products with unprecedented claims and limited evidence. In essence, most of what's on the shelf is unnecessary.\n",
    'adv12_night_mid':
        "Navigating the complexities of a social life while training seriously is one of the great challenges of the modern fitness enthusiast.\n\nThe good news is that it doesn't have to be a trade-off. It's not about choosing between the two, it's about designing a week that accommodates both.\n\nStart by identifying your non-negotiable sessions. These are the workouts that anchor your week. These sessions should be protected at all costs. These are the ones you build everything else around.\n\nFurthermore, alcohol deserves an honest conversation. A drink or two won't derail your progress. A heavy night, however, will cost you the following day and possibly the one after that.\n\nOverall, the goal is balance rather than perfection. At the end of the day, a training programme you can live with beats a perfect one you abandon.\n",
}


# HELD-OUT SPLIT — written before calibration, not looked at during it. All
# four failed cold.
ADV_HELDOUT = {
    'adv13_HO_blatant':
        "In the ever-evolving landscape of modern wellness, one truth remains constant: movement matters.\n\nSeattle boasts a vibrant array of options for anyone looking to begin. From boutique studios to state-of-the-art strength facilities, the city offers a one-stop shop for every conceivable goal.\n\nMoreover, the community aspect cannot be overstated. Group training plays a vital role in adherence, and it's a testament to human nature that we show up more reliably when someone is expecting us.\n\nFurthermore, the barrier to entry has never been lower. A myriad of apps, a plethora of free content, and a wide range of affordable memberships have democratised access in unprecedented ways.\n\nIn conclusion, there has never been a better time to start. Needless to say, the hardest step is the first one.\n",
    'adv14_HO_moderate':
        'The hip hinge is the movement pattern that underpins most lower-body strength work, and learning it properly pays dividends for years.\n\nIt is a pattern that many lifters never fully develop. It is often confused with a squat, which loads the knees rather than the hips. It is the reason so many deadlifts look like awkward leg presses. It is worth spending several weeks getting right.\n\nFurthermore, the hinge transfers directly to athletic movement. Sprinting, jumping, and changing direction all depend on the ability to load and extend the hips forcefully.\n\nStart with a dowel against the spine. Push the hips back until the hamstrings load. Keep the shins close to vertical throughout the movement. Return to standing by driving the hips forward rather than lifting the chest.\n\nOverall, patience here saves a great deal of frustration later.\n',
    'adv15_HO_subtle_flat':
        'Nutrition for strength athletes rests on a small number of well-established principles. Protein supports the repair of tissue damaged during training sessions. Carbohydrate replenishes the glycogen that intense work depletes over time. Fat supports hormone production and the absorption of certain vitamins. Total calorie intake determines whether the body gains or loses mass. Meal timing has a smaller effect than the total daily intake does. Protein distribution across the day appears to offer a modest advantage. Whole foods should form the foundation of any reasonable eating pattern. Supplements fill gaps rather than replacing the underlying structure. Hydration influences performance more than most lifters seem to appreciate. Micronutrients matter even though they receive far less attention than macros. Fibre supports digestion and helps regulate the appetite over longer periods. Consistency across weeks matters far more than perfection on any single day.\n',
    'adv16_HO_subtle_mixed':
        "Group training isn't just a business model, it's a genuine answer to the adherence problem that has dogged the fitness industry for decades.\n\nThe mechanism could possibly be simpler than it appears. People show up when other people expect them. That may potentially be the whole of it.\n\nWhen it comes to choosing a group, the variables that matter are unglamorous. Schedule. Distance. Whether the coach knows your name. The equipment is largely beside the point, though a room with enough bars for everyone certainly helps.\n\nIt's worth noting that this doesn't work for everyone. Some lifters genuinely train better alone, and there's no virtue in forcing a social structure onto someone who finds it draining.\n\nEssentially, the best training environment is the one that gets you through the door on a Tuesday in February.\n",
}

ALL_TIMBR = dict(TIMBR_DERIVATION, **TIMBR_HELDOUT)
ALL_ADV = dict(ADV_DERIVATION, **ADV_HELDOUT)


# ---------------------------------------------------------------------------
# SPEC LISTS — real, shipped, and NOT prose
# ---------------------------------------------------------------------------
# The locked exercise table from PRINCIPLES.txt Sec. 12, one page each from
# three shipped volumes plus the two that found the bug. Verbatim from
# Seattle-Magazine-Engine/runs/<vol>/draft.json and runs/vol11_slu/copy.py.
#
# HELD SEPARATE FROM TIMBR_DERIVATION ON PURPOSE. These slots were excluded
# from the derivation corpus as "not prose" (see the provenance note above),
# and no threshold in synth_config was tuned against them. They are the
# VALIDATION case that found the false positive: run cold against the finished
# module, vol11's two scored 52 and 44. Folding them into the derivation corpus
# after the fact would erase that, so they get their own contract instead.
#
# vol09/vol10 are included for shape variety, not volume: their rep ranges
# ("3 × 8–10") put an en dash on some rows and not others, which is why the
# skeleton test asks for a shared CORE of delimiters rather than an identical
# signature per row.
TIMBR_SPEC_LISTS = {
    'vol09:workout_p4':
        '- Wall Slides: 3 × 12 — blades down and back\n- Dumbbell Bench Press: 4 × 8 — full range\n- Incline Barbell Press: 3 × 8 — touch high\n- Dumbbell Flyes: 3 × 12 — slight bend, big stretch\n- Floor Press: 3 × 10 — dead stop each rep\n- T-Bar Rows: 4 × 8 — chest up, drive the elbows\n- Chest-Supported Row: 3 × 10 — no body english\n- Inverted Rows: 3 × 10–12 — body tight\n- Renegade Rows: 2 × 10 / side — push and pull, finisher',
    'vol09:workout_p5':
        '- Wall Slides: 3 × 15 — slower\n- Dumbbell Bench Press: 4 × 6 — heavier\n- Incline Barbell Press: 3 × 6 — heavier, controlled\n- Dumbbell Flyes: 3 × 10 — heavier, same stretch\n- Floor Press: 3 × 8 — heavier, dead stop\n- T-Bar Rows: 4 × 6 — heavier, strict\n- Chest-Supported Row: 3 × 8 — pause at the top\n- Feet-Elevated Inverted Rows: 3 × 8–10 — harder line\n- Renegade Rows: 2 × 8 / side — heavier bells, finisher',
    'vol10:workout_p4':
        '- Glute Bridge March: 3 × 10 / side — hips level\n- Front Squats: 4 × 8 — elbows high\n- Hack Squats: 3 × 10 — knees forward, safe depth\n- Curtsy Lunges: 3 × 10 / leg — glute medius\n- Barbell Glute Bridge: 3 × 10 — pause at top\n- Goblet Squats: 3 × 12 — upright, deep\n- Lateral Lunges: 3 × 10 / side — push off hard\n- Sissy Squats: 3 × 8–10 — hold support, quads long\n- Sled Push: 2 × 20m — low and hard, finisher',
    'vol10:workout_p5':
        '- Banded Bridge March: 3 × 12 / side — band over hips\n- Front Squats: 4 × 5–6 — heavier\n- Hack Squats: 4 × 8 — add plates\n- Curtsy Lunges: 3 × 8 / leg — add dumbbells\n- Barbell Glute Bridge: 3 × 8 — heavier, longer pause\n- Goblet Squats: 3 × 10 — heavier bell\n- Lateral Lunges: 3 × 8 / side — add a dumbbell\n- Assisted Sissy Squats: 3 × 10–12 — deeper range\n- Sled Push: 2 × 30m — heavier, drive, finisher',
    'vol11:workout_p4':
        '- Banded Good Mornings: 3 × 15 — activation, learn the hinge\n- Bulgarian Split Squat: 4 × 8 / leg — dumbbells, long stride\n- B-Stance Hip Thrust: 3 × 10 / leg — bench at the blades, hips level\n- Cable Pull-Through: 3 × 12 — hinge back, finish tall\n- Cable Hip Abduction: 3 × 15 / side — glute medius, stand tall\n- Single-Leg Romanian Deadlift: 3 × 10 / leg — dumbbell, hips square\n- Hamstring Bridge: 3 × 12 — heels on a bench, hips high\n- Cable Leg Curl: 3 × 12 / leg — ankle strap, no hip swing\n- Dumbbell Reverse Lunge: 2 × 12 / leg — long step back, finisher',
    'vol11:workout_p5':
        '- Banded Good Mornings: 3 × 20 — heavier band, pause at the bottom\n- Bulgarian Split Squat: 4 × 6 / leg — heavier bells, three seconds down\n- B-Stance Hip Thrust: 3 × 12 / leg — heavier dumbbell, two-count at the top\n- Cable Pull-Through: 3 × 15 — heavier stack, squeeze the lockout\n- Cable Hip Abduction: 3 × 20 / side — heavier, pause at end range\n- Single-Leg Romanian Deadlift: 3 × 8 / leg — heavier, three seconds down\n- Single-Leg Hamstring Bridge: 3 × 10 / leg — one heel on the bench\n- Cable Leg Curl: 3 × 10 / leg — heavier, slow the return\n- Dumbbell Reverse Lunge: 2 × 15 / leg — heavier bells, no rest between legs',
}


# ---------------------------------------------------------------------------
# THE EVASIONS — adversarial slop wearing a list's clothes
# ---------------------------------------------------------------------------
# Built by transforming the adversarial corpus rather than written by hand, so
# the content is provably the same slop and only the SHAPE has changed. Three
# escalating attempts, each defeating one more clause of the detector:
#
#   _bulleted        every sentence prefixed "- ", full stops kept. The lazy
#                    evasion: what an agent does when told "make it a list".
#   _bulleted(strip) same, full stops removed.
#   _forged_rows     every sentence rewritten into a compliant spec row —
#                    marker, no full stop, ":" and "×" and "—" on every row,
#                    two numbers per row. This one IS detected as a spec list,
#                    which is the point: it is caught by the field measurement
#                    rather than by the detector, and that is the guarantee the
#                    exemption rests on.
def _bulleted(text, keep_stops=True):
    lines = []
    for s in split_sentences(text):
        lines.append("- " + (s if keep_stops else re.sub(r"[.!?]+$", "", s)))
    return "\n".join(lines)


def _forged_rows(text, where="cue"):
    """Slop forced into "- Label: 3 × 10 — cue", prose in one field or the other."""
    lines = []
    for i, s in enumerate(split_sentences(text)):
        body = re.sub(r"[.!?]+$", "", s)
        lines.append(f"- Point {i + 1}: 3 × 10 — {body}" if where == "cue"
                     else f"- {body}: 3 × 10 — go")
    return "\n".join(lines)


#: The four adversarial texts whose ONLY tell is a flat rhythm, or nearly so —
#: the ones an exemption would set free. Asserted to be exactly that set by
#: TestSpecListRhythm.test_a_flat_rhythm_is_the_whole_case_against_these.
FLAT_ONLY_ADV = ["adv03_flat_subtle", "adv08_subtle_flat",
                 "adv10_brand_subtle", "adv15_HO_subtle_flat"]

#: Neutral padding for the synthetic texts below: TIMBR-shaped prose that
#: carries no tell of its own (bursty, no repeated openers, no banned
#: vocabulary), so a synthetic text's tell count is exactly what was injected
#: into it. Asserted clean by TestFiller.
FILLER = (
    "The room on Terry opens at five thirty on weekdays. Load them honestly. "
    "Sixty classes a week run around the weight floor, for the days the "
    "structure helps. Go early. Afterward there is a dry sauna, towel service, "
    "and validated parking in the garage before eight thirty. Six minutes and "
    "three tenths of a mile separate the two doors, and both counters shut at "
    "four. Sit for ten minutes. Hamstrings are not due anywhere. "
)


class TestFiller:
    """The padding used by the synthetic tests has to be clean, or every
    threshold those tests pin is measuring the padding instead."""

    def test_the_filler_carries_no_tells(self):
        r = run_synthlint(FILLER * 3)
        assert r["violations"] == [] and r["score"] == C.SCORE_START


# ===========================================================================
# Segmentation — every statistic in this module is computed on top of it
# ===========================================================================
class TestSegmentation:

    def test_a_single_newline_ends_a_sentence(self):
        # night_body sets its heading and its dateline on their own lines with
        # no terminal punctuation. Gluing them onto the prose that follows
        # would corrupt every sentence-length statistic in Check 5.
        assert split_sentences("The Night Off\nSouth Lake Union · Westlake") == [
            "The Night Off", "South Lake Union · Westlake"]

    def test_a_single_newline_separates_paragraphs(self):
        # The magazine sections in this repo are single-newline separated.
        # Treating a section as one paragraph erases Check 2's denominator.
        assert split_paragraphs("Alpha.\nBravo.\nCharlie.") == [
            "Alpha.", "Bravo.", "Charlie."]

    def test_blank_lines_also_separate_paragraphs(self):
        assert split_paragraphs("Alpha.\n\n\nBravo.") == ["Alpha.", "Bravo."]

    def test_terminal_punctuation_splits_sentences(self):
        assert split_sentences("Train first. Then coffee! Why not?") == [
            "Train first.", "Then coffee!", "Why not?"]

    def test_an_abbreviation_does_not_end_a_sentence(self):
        s = split_sentences('"The pattern is daylight," says Dr. Imelda Vosskirk, '
                            'who directs the lab. Volume rose 31 percent.')
        assert len(s) == 2
        assert "Dr. Imelda Vosskirk" in s[0]

    def test_a_decimal_point_does_not_end_a_sentence(self):
        assert len(split_sentences("Classic runs $119.99 a month.")) == 1

    def test_empty_and_whitespace_yield_nothing(self):
        assert split_sentences("") == []
        assert split_sentences("   \n\n  ") == []
        assert split_paragraphs("") == []

    def test_word_count_counts_numbers_and_hyphenates(self):
        assert word_count("Bulgarian split squat: 4 x 8 per leg") == 8
        assert word_count("single-leg work") == 2


# ===========================================================================
# CHECK 1 — extended AI vocabulary
# ===========================================================================
class TestAIVocabulary:

    def test_flags_a_connector_phrase(self):
        v, p, hf = check_ai_vocabulary(
            "When it comes to training, the floor is what matters.")
        assert len(v) == 1 and "when it comes to" in v[0]
        assert p == -C.TELL and hf is False

    def test_counts_every_occurrence(self):
        _, p, _ = check_ai_vocabulary("Moreover. Moreover. Moreover.")
        assert p == -3 * C.TELL

    def test_is_case_insensitive_and_boundary_bounded(self):
        assert check_ai_vocabulary("MOREOVER, the room is loud.")[1] == -C.TELL
        # substring, not the word: must not fire
        assert check_ai_vocabulary("Moreoverture is not a word.")[1] == 0

    def test_clean_timbr_copy_scores_nothing(self):
        assert check_ai_vocabulary(TIMBR_DERIVATION["vol11:editor_body"]) == ([], 0, False)

    def test_hard_fail_at_the_derived_saturation_point(self):
        four = ("Moreover. Furthermore. In summary. In conclusion.")
        five = four + " Needless to say."
        assert check_ai_vocabulary(four)[2] is False
        assert check_ai_vocabulary(five)[2] is True
        assert C.VOCAB_HARD_FAIL_HITS == 5

    def test_no_term_is_priced_by_both_linters(self):
        # The de-duplication invariant. If prohiblint ever adds one of these
        # terms, the filter in synth_config must remove it from here.
        # Read through synth_config's own handle rather than re-importing
        # prohiblint: that is the list the filter actually ran against, and
        # `import prohiblint` resolves to a different object depending on which
        # directory pytest was started from.
        assert set(t.lower() for t in C.EXTENDED_AI_VOCAB).isdisjoint(
            set(t.lower() for t in C._PROHIB_AI_BLOCKLIST))

    def test_the_dedup_filter_is_live_not_decorative(self):
        # Today the intersection with prohiblint is empty, so the filter is a
        # no-op and nothing observable would change if it were deleted. Prove
        # the MECHANISM instead: re-execute synth_config against a stubbed
        # prohiblint that owns two of our terms, and assert they are ceded.
        stub = types.ModuleType("prohiblint")
        stub.AI_BLOCKLIST = ["moreover", "Boasts"]
        saved = {k: sys.modules.get(k)
                 for k in ("prohiblint", "prohiblint.prohiblint")}
        try:
            sys.modules["prohiblint"] = stub
            sys.modules.pop("prohiblint.prohiblint", None)
            src = open(os.path.join(MODULE_DIR, "synth_config.py")).read()
            mod = types.ModuleType("stubbed_config")
            mod.__file__ = os.path.join(MODULE_DIR, "synth_config.py")
            exec(compile(src, "<stubbed_config>", "exec"), mod.__dict__)
        finally:
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        assert "moreover" not in mod.EXTENDED_AI_VOCAB
        assert "boasts" not in mod.EXTENDED_AI_VOCAB
        assert set(mod.VOCAB_CEDED_TO_PROHIBLINT) == {"moreover", "boasts"}

    def test_measurement_and_position_words_are_not_on_the_list(self):
        # "additionally" / "overall" are tells only paragraph-initially, which
        # is Check 2's job; "roughly" is how PRINCIPLES Sec. 8 qualifies a
        # number honestly. None of them may be a lexical ban.
        low = {t.lower() for t in C.EXTENDED_AI_VOCAB}
        for term in ("additionally", "overall", "roughly", "approximately",
                     "about", "around", "may", "might", "could"):
            assert term not in low


# ===========================================================================
# CHECK 2 — formulaic transition density
# ===========================================================================
_P = "The room opens at five and the racks are full by six.\n"


class TestTransitionDensity:

    def test_paragraph_initial_transitions_are_found(self):
        text = "Moreover, the racks fill early.\n" + _P + "Overall, it holds.\n"
        assert [t.lower() for _, t in transition_openers(text)] == [
            "moreover", "overall"]

    def test_mid_sentence_use_is_not_a_transition(self):
        # "overall volume rose 31 percent" is a measurement, not a signpost.
        text = "The overall volume rose 31 percent.\n" + _P + _P
        assert transition_openers(text) == []
        assert check_transition_density(text) == ([], 0, False)

    def test_one_hit_is_presence_not_density(self):
        # Priced once by Check 1. Check 2 is the surcharge for the HABIT.
        # 1 of 4 paragraphs = 0.25, over the rate. Only the two-hit gate
        # keeps it clean, which is the point of the gate.
        text = "Moreover, the racks fill early.\n" + _P * 3
        assert len(transition_openers(text)) == 1
        assert len(split_paragraphs(text)) == 4
        assert check_transition_density(text) == ([], 0, False)
        assert check_ai_vocabulary(text)[1] == -C.TELL

    def test_two_hits_over_the_rate_fire(self):
        text = ("Moreover, the racks fill early.\n"
                "Furthermore, the coaching changed.\n" + _P * 3)
        v, p, hf = check_transition_density(text)
        assert len(v) == 1 and "0.40" in v[0]
        assert p == -C.TRANSITION_DENSITY_BASE_TELLS * C.TELL and hf is False

    def test_penalty_grows_with_density(self):
        two = "Moreover, a.\nFurthermore, b.\n" + _P * 3
        four = ("Moreover, a.\nFurthermore, b.\nAdditionally, c.\n"
                "Overall, d.\n" + _P)
        assert check_transition_density(four)[1] < check_transition_density(two)[1]

    def test_two_hits_under_the_rate_do_not_fire(self):
        text = "Moreover, a.\nFurthermore, b.\n" + _P * 18
        assert len(transition_openers(text)) == 2
        assert check_transition_density(text) == ([], 0, False)

    def test_a_text_with_too_few_paragraphs_is_not_rated(self):
        # Two paragraphs, both opening with a transition — a rate of 1.00 on a
        # denominator of two, which is not a rate.
        text = "Moreover, the racks fill early.\nFurthermore, the coaching changed."
        assert len(split_paragraphs(text)) == 2
        assert len(transition_openers(text)) == 2
        assert check_transition_density(text) == ([], 0, False)

    def test_real_timbr_copy_never_opens_a_paragraph_this_way(self):
        for name, text in ALL_TIMBR.items():
            assert transition_openers(text) == [], name


# ===========================================================================
# CHECK 3 — contrastive frames
# ===========================================================================
class TestContrastiveFrames:

    @pytest.mark.parametrize("text,expected", [
        ("Strength training isn't just about lifting heavy things.", "nt-just"),
        ("The gym is not just a place to exercise.", "not-just"),
        ("It's not about the weight on the bar.", "not-about"),
        ("It is not merely rest but rather the process of adaptation.", "but-rather"),
        ("The room is more than just a floor.", "more-than-just"),
    ])
    def test_each_pattern_fires_on_the_shape_it_owns(self, text, expected):
        assert expected in [n for n, _ in contrastive_frames(text)]

    @pytest.mark.parametrize("text", [
        # TIMBR states the negation and the correction as SEPARATE sentences
        # and never props them up with an intensifier. All of this is house
        # voice, verbatim or in its shape, and none of it may fire.
        "It is not CrossFit. It is not Pilates. It is the barbell.",
        "This is not a fitness trend. This is a structural shift.",
        "This is not a story about equipment. This is a story about the city.",
        "Not because they failed. Because the city moved on.",
        "It reads less like a workout and more like a city worth exploring.",
        "Protein powder is a convenience, not a supplement.",
        "Not a wellness tip, just arithmetic.",
        "The effect is neurological rather than structural.",
        "The pattern is consolidation, not disappearance.",
        "Magnesium glycinate. Not oxide.",
    ])
    def test_timbr_contrast_is_not_a_contrastive_frame(self, text):
        assert contrastive_frames(text) == []

    def test_one_frame_is_never_a_violation(self):
        # One frame in 71 words is 3.5 per 250w, over the rate. Only the
        # two-frame gate keeps it clean: a single pivot is a sentence, not a
        # fingerprint.
        text = "Strength training isn't just about lifting heavy things. " + FILLER
        assert len(contrastive_frames(text)) == 1
        assert word_count(text) > C.CONTRASTIVE_MIN_WORDS
        assert len(contrastive_frames(text)) * C.CONTRASTIVE_RATE_WINDOW / \
            word_count(text) > C.CONTRASTIVE_RATE_MAX
        assert check_contrastive_frames(text) == ([], 0, False)

    def test_two_frames_over_the_rate_fire(self):
        text = ("Strength training isn't just about lifting. It's not about "
                "the bar. " + FILLER)
        assert len(contrastive_frames(text)) == 2
        v, p, hf = check_contrastive_frames(text)
        assert len(v) == 1 and p == -C.CONTRASTIVE_BASE_TELLS * C.TELL
        assert hf is False

    def test_two_frames_diluted_below_the_rate_do_not_fire(self):
        # 307 words: 1.63 frames per 250w, under the threshold. Doubling the
        # window would put the same two frames at 3.26 and fire, so this pins
        # CONTRASTIVE_RATE_WINDOW too.
        text = ("Strength training isn't just about lifting. It's not about "
                "the bar. " + FILLER * 4)
        assert len(contrastive_frames(text)) == 2
        assert word_count(text) == 307
        assert check_contrastive_frames(text) == ([], 0, False)

    def test_penalty_grows_with_frame_count(self):
        base = FILLER
        two = "It isn't just a gym. It's not about weight. " + base
        five = ("It isn't just a gym. It's not about weight. It is not just a "
                "floor. It's not about the bar. It is more than just a room. "
                + base)
        assert check_contrastive_frames(five)[1] < check_contrastive_frames(two)[1]

    def test_a_caption_is_too_short_to_rate(self):
        # A standfirst, not a body: two frames, but only 26 words behind them.
        caption = ("It isn't just a gym. It's not about weight. The room on "
                   "Terry opens at five thirty on weekdays.")
        assert len(contrastive_frames(caption)) == 2
        assert 10 < word_count(caption) < C.CONTRASTIVE_MIN_WORDS
        assert check_contrastive_frames(caption) == ([], 0, False)

    def test_the_min_words_gate_does_not_swallow_a_hundred_word_text(self):
        # The regression this constant exists for: at 120 the gate exempted
        # adv05_contrastive, a 98-word text carrying eight frames, and it
        # scored a clean 100.
        r = run_synthlint(ADV_DERIVATION["adv05_contrastive"])
        assert r["passed"] is False
        assert r["flags"]["contrastive_frames"]["penalty"] < 0

    def test_real_timbr_copy_carries_no_frames_at_all(self):
        for name, text in ALL_TIMBR.items():
            assert contrastive_frames(text) == [], name


# ===========================================================================
# CHECK 4 — hedge stacking
# ===========================================================================
class TestHedgeStacking:

    @pytest.mark.parametrize("text", [
        "Creatine may potentially offer a benefit.",
        "The research could possibly suggest an effect.",
        "It seems to possibly indicate a faster route.",
        "The dose might perhaps matter less than the total.",
    ])
    def test_adjacent_hedges_stack(self, text):
        assert len(hedge_stacks(text)) == 1
        assert check_hedge_stacking(text)[1] == -C.HEDGE_STACK_TELLS * C.TELL

    def test_an_epistemic_frame_plus_a_hedge_stacks(self):
        assert hedge_stacks("It is possible that the response might vary.")

    @pytest.mark.parametrize("text", [
        "The logs suggest most lifters were skipping it entirely.",
        "Better sleep is a real outcome, and it is probably the mechanism.",
        "Range of motion improves for about 20 minutes.",
        "Volume drops to roughly 60 percent of week two.",
    ])
    def test_a_single_hedge_is_not_a_stack(self, text):
        assert hedge_stacks(text) == []

    def test_a_negated_modal_is_negation_not_hedging(self):
        # magazine_pass Culture, verbatim shape: "held for a use the previous
        # tenant could not match". "could not" is a fact about ability.
        assert hedge_stacks(
            "held for a use the previous tenant could not possibly match") == []

    def test_measurement_qualifiers_are_not_hedges(self):
        # The real false positive that shaped the lexicon: magazine_pass
        # Nutrition, verbatim.
        line = ("She trains at six and has about twenty minutes in between to "
                "put roughly 40 grams of protein somewhere it will stay.")
        assert hedge_stacks(line) == []
        assert hedge_stacks("It is roughly about the same distance.") == []

    def test_hedges_in_different_clauses_do_not_stack(self):
        assert hedge_stacks(
            "Members often report better sleep, and the effect is typically "
            "small.") == []

    def test_hedges_too_far_apart_in_one_clause_do_not_stack(self):
        # One clause, no punctuation and no conjunction between them: seven
        # words apart is co-occurrence, not compounding.
        assert C.HEDGE_STACK_MAX_GAP_WORDS == 2
        assert hedge_stacks(
            "Members often report better sleep on the nights they typically "
            "use it.") == []

    def test_a_clause_is_priced_once_however_many_hedges_it_carries(self):
        stacks = hedge_stacks("It may possibly potentially help a little.")
        assert len(stacks) == 1

    def test_hard_fail_at_three_stacks(self):
        two = ("It may potentially help. The dose could possibly matter.")
        three = two + " The effect might perhaps persist."
        assert check_hedge_stacking(two)[2] is False
        assert check_hedge_stacking(three)[2] is True
        assert C.HEDGE_STACK_HARD_FAIL == 3

    def test_one_stack_alone_does_not_fail_a_text(self):
        # The corroboration rule: no single regex hit rejects a text by itself.
        text = "It may potentially help. " + FILLER * 2
        r = run_synthlint(text)
        assert r["flags"]["hedge_stacking"]["penalty"] == -2 * C.TELL
        assert r["score"] == C.PASS_THRESHOLD and r["passed"] is True

    def test_this_is_not_prohiblints_or_voicelints_single_hedge_list(self):
        # voice_config.FITT_NEGATIVE[0] flags ONE hedge word. This check needs
        # two compounding, which is a different and stronger defect.
        single = "The evidence might support it."
        assert re.search(r'\b(?:might|could|perhaps|possibly|seems|appear|'
                         r'suggest|may)\b', single)          # FITT would flag
        assert hedge_stacks(single) == []                    # SynthLint does not


# ===========================================================================
# CHECK 5 — burstiness
# ===========================================================================
def _uniform(n, words):
    return " ".join([("word " * (words - 1) + "end.") for _ in range(n)])


class TestBurstiness:

    def test_burstiness_is_population_stdev(self):
        n, mean, sd, cv = burstiness("One two. One two three four.")
        assert n == 2 and mean == 3.0
        assert sd == pytest.approx(1.0)          # pstdev; sample stdev is 1.414
        assert cv == pytest.approx(1 / 3)

    def test_a_flat_text_fires(self):
        v, p, hf = check_burstiness(_uniform(12, 12))
        assert len(v) == 1 and "Flat sentence rhythm" in v[0]
        assert p < 0 and hf is False

    def test_penalty_grows_as_the_rhythm_flattens(self):
        flat = _uniform(12, 12)                       # CV 0.000
        less = " ".join(_uniform(1, w) for w in
                        [12, 15, 9, 13, 14, 10, 12, 16, 8, 12, 14, 10])
        assert burstiness(flat)[3] < burstiness(less)[3] < C.BURSTINESS_CV_FLOOR
        assert check_burstiness(flat)[1] < check_burstiness(less)[1]

    def test_a_text_with_too_few_sentences_is_not_measured(self):
        # vol11:post_stack_body is two 11-word sentences: CV 0.09, and
        # entirely legitimate.
        text = TIMBR_DERIVATION["vol11:post_stack_body"]
        n, mean, sd, cv = burstiness(text)
        assert n < C.BURSTINESS_MIN_SENTENCES and cv < C.BURSTINESS_CV_FLOOR
        assert check_burstiness(text) == ([], 0, False)

    def test_the_staccato_register_is_exempt(self):
        # PRINCIPLES Sec. 7: "Short declaratives. Fragments allowed for punch."
        # A section written in four-word lines is uniform because uniformity is
        # the device there.
        text = _uniform(12, 4)
        n, mean, sd, cv = burstiness(text)
        assert mean < C.BURSTINESS_MIN_MEAN_WORDS and cv < C.BURSTINESS_CV_FLOOR
        assert check_burstiness(text) == ([], 0, False)

    def test_a_bursty_text_does_not_fire(self):
        text = ("Train first. The room on Terry opens at five thirty on "
                "weekdays and the weight floor is the reason this pair belongs "
                "here. Load them honestly. Sixty classes a week run around it, "
                "for the days the structure helps. Go early. Afterward there is "
                "a dry sauna, towel service, and validated parking before eight "
                "thirty. Do the heavy half here. Hamstrings are not due "
                "anywhere.")
        assert burstiness(text)[3] > C.BURSTINESS_CV_FLOOR
        assert check_burstiness(text) == ([], 0, False)

    def test_no_real_timbr_text_comes_near_the_floor(self):
        for name, text in ALL_TIMBR.items():
            n, mean, sd, cv = burstiness(text)
            if n >= C.BURSTINESS_MIN_SENTENCES and mean >= C.BURSTINESS_MIN_MEAN_WORDS:
                assert cv >= C.BURSTINESS_CV_FLOOR, (name, cv)


# ===========================================================================
# CHECK 5, PART TWO — spec-list detection
# ===========================================================================
#: A spec list stripped to the minimum that still satisfies every clause.
_ROWS = ("- Wall Slides: 3 × 12 — blades down\n"
         "- Floor Press: 3 × 10 — dead stop\n"
         "- T-Bar Rows: 4 × 8 — chest up\n"
         "- Goblet Squats: 3 × 12 — upright")

#: The same rows under an unmarked heading that carries the same skeleton and
#: no full stop, so the ONLY clause it fails is "every line is a row".
_HEADED_ROWS = "Week one: 3 × 10 — base block\n" + _ROWS

#: Four rows that each carry a structural delimiter, but not the SAME one.
#: Union of two, intersection of none: not one skeleton.
_MIXED_DELIMS = ("- Sleep is the lever: it is free\n"
                 "- Food is the second — it is not\n"
                 "- Walking is underrated: it costs nothing\n"
                 "- Deloads get skipped — they should not be")


class TestSpecListDetection:
    """The detector, clause by clause. Every clause is pinned by a
    counterexample that fails ONLY that clause, so a clause that stops doing
    anything fails a test instead of quietly widening the exemption."""

    @pytest.mark.parametrize("name", sorted(TIMBR_SPEC_LISTS))
    def test_every_real_spec_list_is_detected(self, name):
        assert is_spec_list(TIMBR_SPEC_LISTS[name]) is True

    @pytest.mark.parametrize("name", sorted(TIMBR_DERIVATION))
    def test_no_real_prose_is_mistaken_for_a_list(self, name):
        assert is_spec_list(TIMBR_DERIVATION[name]) is False

    @pytest.mark.parametrize("name", sorted(ALL_ADV))
    def test_no_adversarial_text_is_a_list_as_written(self, name):
        assert is_spec_list(ALL_ADV[name]) is False

    def test_rows_are_returned_with_the_marker_stripped(self):
        bodies = spec_list_rows(_ROWS)
        assert len(bodies) == 4
        assert bodies[0] == "Wall Slides: 3 × 12 — blades down"

    def test_a_non_list_returns_none_not_an_empty_list(self):
        # None and [] must be distinguishable: one means "declined", the other
        # would mean "a list with no rows", which cannot happen.
        assert spec_list_rows(FILLER) is None
        assert spec_list_fields(FILLER) == []

    def test_three_rows_are_not_a_format(self):
        assert C.SPEC_LIST_MIN_ROWS == 4
        assert is_spec_list("\n".join(_ROWS.split("\n")[:3])) is False

    def test_one_prose_line_disqualifies_the_whole_text(self):
        # Detection is whole-text. Prose with a table in it is not a spec list,
        # and is measured exactly as before — the conservative direction.
        assert is_spec_list(_ROWS + "\nThe room opens at five thirty.") is False
        assert is_spec_list("The room opens at five thirty.\n" + _ROWS) is False

    def test_an_unmarked_heading_row_disqualifies_it_too(self):
        # Isolates the "every line" clause from the clauses after it. This
        # heading has no full stop and carries the same skeleton as the rows,
        # so it clears every other clause; it is refused because it has no
        # marker, which is the whole of the whole-text rule.
        assert is_spec_list(_HEADED_ROWS) is False
        assert all(C.SPEC_LIST_MARKER_RE.match(r) is None
                   for r in _HEADED_ROWS.split("\n")[:1])

    def test_a_row_that_ends_in_a_full_stop_is_a_sentence(self):
        assert is_spec_list(_ROWS.replace("upright", "upright.")) is False

    def test_one_shared_dash_is_not_a_template(self):
        # The failure mode the brief named outright: do not exempt anything
        # that merely has a dash in it. These four rows share the em dash and
        # nothing else.
        one_delim = ("- Sleep is the lever — it is free\n"
                     "- Food is the second — it is not\n"
                     "- Walking is underrated — it costs nothing\n"
                     "- Deloads get skipped — they should not be")
        assert set.intersection(*(set(C.SPEC_LIST_DELIM_RE.findall(r))
                                  for r in one_delim.split("\n"))) == {"—"}
        assert C.SPEC_LIST_MIN_SHARED_DELIMITERS == 2
        assert is_spec_list(one_delim) is False

    def test_rows_sharing_no_delimiter_are_not_a_template(self):
        assert is_spec_list("- alpha\n- bravo\n- charlie\n- delta") is False

    def test_different_delimiters_on_different_rows_are_not_one_skeleton(self):
        # The clause is an INTERSECTION over rows, not a union. Each row here
        # carries a structural delimiter and the four of them carry two between
        # them, but no delimiter is on every row, so they were not filled from
        # one template.
        per_row = [set(C.SPEC_LIST_DELIM_RE.findall(r))
                   for r in _MIXED_DELIMS.split("\n")]
        assert len(set.union(*per_row)) == 2
        assert set.intersection(*per_row) == set()
        assert is_spec_list(_MIXED_DELIMS) is False

    def test_the_skeleton_is_a_shared_core_not_an_identical_signature(self):
        # vol09/vol10 rep ranges ("3 × 8–10") put an en dash on some rows and
        # not others. An exact per-row signature match would reject four of the
        # six lists here — five of the eight shipped — so the clause asks for a
        # shared CORE instead, and the core is the same on every one.
        for name, text in TIMBR_SPEC_LISTS.items():
            shared = set.intersection(*(set(C.SPEC_LIST_DELIM_RE.findall(b))
                                        for b in spec_list_rows(text)))
            assert shared == {":", "×", "—"}, name
        varied = sorted(n for n, t in TIMBR_SPEC_LISTS.items()
                        if len({tuple(C.SPEC_LIST_DELIM_RE.findall(b))
                                for b in spec_list_rows(t)}) > 1)
        assert varied == ["vol09:workout_p4", "vol09:workout_p5",
                          "vol10:workout_p4", "vol10:workout_p5"]

    def test_enumerators_and_other_bullet_glyphs_count_as_markers(self):
        for marker in ("*", "•", "1.", "2)"):
            rows = "\n".join(f"{marker} Wall Slides: {i} × 12 — blades down"
                             for i in range(4))
            assert is_spec_list(rows) is True, marker

    def test_a_letter_enumerator_is_not_a_marker(self):
        # Deliberately absent: "a)" and "A." collide with initials at line
        # start, and no TIMBR format uses them.
        rows = "\n".join(f"a) Wall Slides: {i} × 12 — blades down"
                         for i in range(4))
        assert is_spec_list(rows) is False

    def test_the_field_is_the_longest_one_not_the_last(self):
        fields = spec_list_fields(TIMBR_SPEC_LISTS["vol11:workout_p4"])
        assert fields[0] == "activation, learn the hinge"
        # Prose in the LABEL position is found there instead.
        moved = _forged_rows(ADV_DERIVATION["adv10_brand_subtle"], where="label")
        assert spec_list_fields(moved)[0].startswith("We believe movement")


# ===========================================================================
# CHECK 5, PART TWO — the rhythm unit, and the evasions it has to survive
# ===========================================================================
class TestSpecListRhythm:

    @pytest.mark.parametrize("name", sorted(TIMBR_SPEC_LISTS))
    def test_every_real_spec_list_passes_clean(self, name):
        # The bug, as a contract. vol11's two scored 52 and 44.
        r = run_synthlint(TIMBR_SPEC_LISTS[name])
        assert r["passed"] is True, r["violations"]
        assert r["score"] == C.SCORE_START, r["violations"]
        assert r["violations"] == []

    @pytest.mark.parametrize("name", sorted(TIMBR_SPEC_LISTS))
    def test_the_rows_really_are_flat_and_that_is_the_point(self, name):
        # Not "the check happens not to fire" — the rows are well under the
        # floor, and the exemption is the only thing standing between them and
        # a violation.
        n, mean, sd, cv = burstiness(TIMBR_SPEC_LISTS[name])
        assert n >= C.BURSTINESS_MIN_SENTENCES
        assert cv < C.BURSTINESS_CV_FLOOR, (name, cv)
        assert check_burstiness(TIMBR_SPEC_LISTS[name]) == ([], 0, False)

    @pytest.mark.parametrize("name", sorted(TIMBR_SPEC_LISTS))
    def test_the_exemption_is_earned_by_the_field_not_granted(self, name):
        # The field IS measured. It clears on the staccato gate, which is the
        # same exemption a four-word declarative gets, applied to a four-word
        # coaching cue.
        text = TIMBR_SPEC_LISTS[name]
        fields = spec_list_fields(text)
        mean = statistics.mean([word_count(f) for f in fields])
        assert len(fields) >= C.BURSTINESS_MIN_SENTENCES
        assert mean < C.BURSTINESS_MIN_MEAN_WORDS, (name, mean)

    def test_a_flat_rhythm_is_the_whole_case_against_these(self):
        # Why the exemption had to be narrow: for three of these four, the
        # rhythm check is the ONLY check that fires. Switch it off on a shape
        # and they walk.
        for name in FLAT_ONLY_ADV:
            flags = run_synthlint(ALL_ADV[name])["flags"]
            fired = {k for k, _ in synthlint.CHECKS if flags[k]["penalty"] < 0}
            assert "burstiness" in fired, name
        alone = [n for n in FLAT_ONLY_ADV
                 if {k for k, _ in synthlint.CHECKS
                     if run_synthlint(ALL_ADV[n])["flags"][k]["penalty"] < 0}
                 == {"burstiness"}]
        assert sorted(alone) == ["adv03_flat_subtle", "adv10_brand_subtle",
                                 "adv15_HO_subtle_flat"]

    @pytest.mark.parametrize("name", FLAT_ONLY_ADV)
    @pytest.mark.parametrize("keep_stops", [True, False])
    def test_bulleting_slop_does_not_buy_the_exemption(self, name, keep_stops):
        # THE EVASION TEST. Prefix every sentence with "- " and the text is
        # still not a spec list: no shared skeleton, and with the stops kept,
        # no row that stops being a sentence.
        evaded = _bulleted(ALL_ADV[name], keep_stops=keep_stops)
        assert is_spec_list(evaded) is False
        r = run_synthlint(evaded)
        assert r["passed"] is False, r["score"]
        assert r["flags"]["burstiness"]["penalty"] < 0

    @pytest.mark.parametrize("name", FLAT_ONLY_ADV)
    @pytest.mark.parametrize("where", ["cue", "label"])
    def test_forging_a_compliant_spec_row_does_not_buy_it_either(self, name, where):
        # The strongest evasion available: every clause of the detector
        # satisfied. The text IS accepted as a spec list — and the field
        # measurement catches it anyway, wherever the prose was hidden.
        forged = _forged_rows(ALL_ADV[name], where=where)
        assert is_spec_list(forged) is True
        fields = spec_list_fields(forged)
        assert statistics.mean([word_count(f) for f in fields]) >= \
            C.BURSTINESS_MIN_MEAN_WORDS
        r = run_synthlint(forged)
        assert r["flags"]["burstiness"]["penalty"] < 0, forged[:120]
        assert r["passed"] is False, r["score"]

    def test_the_violation_names_the_unit_it_measured(self):
        forged = _forged_rows(ADV_DERIVATION["adv03_flat_subtle"])
        v = check_burstiness(forged)[0][0]
        assert "row-field" in v and "spec list" in v
        assert "sentence" in check_burstiness(_uniform(12, 12))[0][0]

    def test_metrics_report_the_shape(self):
        assert run_synthlint(
            TIMBR_SPEC_LISTS["vol11:workout_p4"])["flags"]["_metrics"]["spec_list"] \
            is True
        assert run_synthlint(
            TIMBR_DERIVATION["vol11:city_intro"])["flags"]["_metrics"]["spec_list"] \
            is False

    def test_burstiness_itself_still_reports_the_sentence_statistic(self):
        # The public statistic does not change meaning with the shape. Only
        # check_burstiness switches unit.
        text = TIMBR_SPEC_LISTS["vol11:workout_p4"]
        assert burstiness(text)[0] == len(split_sentences(text)) == 9
        assert burstiness(text)[3] == pytest.approx(0.116, abs=0.005)


# ===========================================================================
# CHECK 6 — repeated-opener runs
# ===========================================================================
_LONG = ("{w} is the reason the room fills before six on a Tuesday morning "
         "in winter.")


class TestRepeatedOpeners:

    def test_four_long_same_word_sentences_fire(self):
        text = " ".join(_LONG.format(w=w) for w in
                        ["The bar", "The rack", "The floor", "The coach"])
        runs = repeated_opener_runs(text)
        assert len(runs) == 1 and runs[0][0] == "same-opener" and runs[0][1] == 4
        assert check_repeated_openers(text)[1] == -C.OPENER_RUN_TELLS * C.TELL

    def test_three_long_same_word_sentences_are_the_triad_and_do_not_fire(self):
        # PRINCIPLES Sec. 7 endorses "Triads and parallelism". Three parallel
        # sentences is the device landing; four is the device running on.
        text = " ".join(_LONG.format(w=w) for w in
                        ["The bar", "The rack", "The floor"])
        assert repeated_opener_runs(text) == []
        assert C.SAME_OPENER_RUN_MIN == 4

    def test_three_generic_openers_fire_even_with_different_first_words(self):
        text = ("This means the muscle receives a stimulus it has not seen "
                "before. It allows the body to adapt over the following days "
                "and weeks. These are the changes that accumulate across a "
                "training block of several weeks.")
        runs = repeated_opener_runs(text)
        assert len(runs) == 1 and runs[0][0] == "generic-opener"
        assert C.GENERIC_OPENER_RUN_MIN == 3

    def test_the_crossfit_triad_is_anaphora_and_is_exempt(self):
        # sample_issue Training, verbatim. Three consecutive generic openers,
        # and it is house voice: parallelism in four-word declaratives.
        text = "It is not CrossFit. It is not Pilates. It is the barbell."
        assert repeated_opener_runs(text) == []
        assert check_repeated_openers(text) == ([], 0, False)

    def test_the_supplements_fragment_triad_is_exempt(self):
        # magazine_pass Supplements, verbatim: [3, 2, 8] words.
        text = ("No loading phase. No cycling. No timing protocol worth the "
                "attention it gets.")
        assert repeated_opener_runs(text) == []

    def test_a_menu_block_is_a_data_listing_and_is_exempt(self):
        # magazine_pass Nutrition's shape, extended to four rows so it clears
        # SAME_OPENER_RUN_MIN and the data-listing exemption is what saves it.
        text = ("The turkey and white bean bowl is 41g protein, 29g carbs, 19g "
                "fat, $16. The smoked trout plate with rye is 39g protein, 31g "
                "carbs, 21g fat, $17. The egg and barley skillet is 42g "
                "protein, 28g carbs, 20g fat, $14. The cold roast chicken with "
                "beans is 38g protein, 27g carbs, 18g fat, $15.")
        assert len(split_sentences(text)) == 4
        assert repeated_opener_runs(text) == []

    def test_the_anaphora_exemption_has_a_ceiling(self):
        assert C.ANAPHORA_MAX_WORDS == 10
        long_run = " ".join(_LONG.format(w=w) for w in
                            ["This", "This", "This"])
        assert repeated_opener_runs(long_run)     # 13-word sentences: exposition

    def test_one_number_a_line_is_prose_not_a_data_listing(self):
        # DATA_LISTING_MIN_NUMBERS counts number TOKENS. A four-digit year is
        # one number, not four digits' worth of table.
        text = (
            "The Ballard room opened in 2021 and has not changed its schedule "
            "since. The Georgetown room opened in 2019 and still runs the same "
            "four classes. The Fremont room opened in 2022 and lost its lease "
            "the following winter. The Eastlake room opened in 2018 and has "
            "quietly outlasted all of them.")
        assert len(repeated_opener_runs(text)) == 1

    def test_one_passage_is_priced_once(self):
        # adv04_openers is two same-word runs of four inside one eight-sentence
        # generic run. Without span de-duplication it was charged three times.
        runs = repeated_opener_runs(ADV_DERIVATION["adv04_openers"])
        assert len(runs) == 2
        assert all(k == "same-opener" for k, _, _ in runs)

    def test_one_run_alone_passes_and_two_runs_fail(self):
        # The corroboration rule again, pinned in verdicts rather than in the
        # value of OPENER_RUN_TELLS.
        one = " ".join(_LONG.format(w=w) for w in
                       ["The bar", "The rack", "The floor", "The coach"])
        two = one + " " + " ".join(_LONG.format(w=w) for w in
                                   ["A bar", "A rack", "A floor", "A coach"])
        assert len(repeated_opener_runs(one)) == 1
        assert len(repeated_opener_runs(two)) == 2
        assert run_synthlint(one + " " + FILLER)["passed"] is True
        assert run_synthlint(two + " " + FILLER)["passed"] is False

    def test_a_generic_run_can_be_carried_by_the_copula_alone(self):
        text = ("This is the reason the room fills before six on a Tuesday in "
                "winter. It is also why the coaching staff moved the session "
                "an hour earlier. That is the whole argument for a base block "
                "in the dark months.")
        runs = repeated_opener_runs(text)
        assert len(runs) == 1 and runs[0][0] == "generic-opener"

    def test_the_anaphora_exemption_needs_every_sentence_to_be_short(self):
        # One short line inside an otherwise expository run does not make the
        # run a rhetorical figure.
        text = ("The bar is the reason the room fills before six on a Tuesday "
                "morning in winter. The rack is the reason the room fills "
                "before six on a Tuesday morning. The floor is the reason the "
                "room fills before six in winter. The coach knows.")
        assert word_count(split_sentences(text)[-1]) <= C.ANAPHORA_MAX_WORDS
        assert len(repeated_opener_runs(text)) == 1

    def test_the_data_listing_exemption_needs_every_sentence_to_be_a_row(self):
        text = ("The turkey and white bean bowl is 41g protein, 29g carbs, "
                "19g fat, $16. The smoked trout plate is 39g protein, 31g "
                "carbs, 21g fat, $17. The egg and barley skillet is 42g "
                "protein, 28g carbs, 20g fat, $14. The room seats twenty-two "
                "and the staff know their regulars by order.")
        assert len(repeated_opener_runs(text)) == 1

    def test_no_real_timbr_text_produces_a_run(self):
        for name, text in ALL_TIMBR.items():
            assert repeated_opener_runs(text) == [], name


# ===========================================================================
# The dropped check
# ===========================================================================
class TestDroppedTriadCheck:

    def test_the_triad_check_is_not_shipped(self):
        names = {n for n, _ in synthlint.CHECKS}
        assert not any("triad" in n for n in names)
        assert not any("triad" in n for n in dir(synthlint))

    def test_the_drop_is_documented_with_its_numbers(self):
        note = C.DROPPED_CHECKS["triad_rate"]
        assert note.startswith("DROPPED.")
        for evidence in ("0.219", "0.50", "114 paragraphs", "11 of 12"):
            assert evidence in note

    def test_the_measurement_that_forced_the_drop_still_holds(self):
        # Recomputed, not asserted from memory: real TIMBR copy uses triads
        # MORE than the adversarial corpus does. Any threshold that catches
        # slop fires on house voice first.
        timbr = max(_triad_saturation(t) for t in ALL_TIMBR.values())
        adv = max(_triad_saturation(t) for t in ALL_ADV.values())
        assert timbr >= adv
        n_timbr = sum(len(_prose_triads(t)) for t in ALL_TIMBR.values())
        n_adv = sum(len(_prose_triads(t)) for t in ALL_ADV.values())
        assert n_timbr > n_adv


_TRIAD_ITEM = r"[^,;:.!?()\[\]\n]{1,45}?"
_TRIAD_AND = re.compile(
    r"(?<![\w,])(" + _TRIAD_ITEM + r"),\s+(" + _TRIAD_ITEM +
    r"),\s+(?:and|or)\s+(" + _TRIAD_ITEM + r")(?=[.,;:!?)\n]|$)", re.IGNORECASE)
_TRIAD_BARE = re.compile(
    r"(?<![\w,])(" + _TRIAD_ITEM + r"),\s+(" + _TRIAD_ITEM + r"),\s+(" +
    _TRIAD_ITEM + r")(?=[.;:!?)\n]|$)")


def _prose_triads(chunk):
    """The detector the dropped check would have used. Kept in the suite so
    the finding that killed it can be re-derived rather than believed."""
    out = []
    for pat in (_TRIAD_AND, _TRIAD_BARE):
        for m in pat.finditer(chunk):
            items = [g.strip() for g in m.groups()]
            if any(re.search(r"\d", i) for i in items):
                continue                    # a menu row or an address
            if any(len(i.split()) > 6 for i in items):
                continue                    # a list of clauses, not a triad
            out.append(tuple(items))
    return out


def _triad_saturation(text):
    best = 0.0
    for para in split_paragraphs(text):
        sents = split_sentences(para)
        if not sents:
            continue
        bearing = sum(1 for s in sents if _prose_triads(s))
        best = max(best, bearing / len(sents))
    return best


# ===========================================================================
# The scale, and the EFFECTIVE pass bar
# ===========================================================================
class TestScale:

    def test_the_threshold_is_the_budget_not_a_number(self):
        assert C.PASS_THRESHOLD == C.SCORE_START + C.NOISE_BUDGET * -C.TELL

    def test_the_effective_bar_is_pinned_in_tells_not_in_points(self):
        # Asserting PASS_THRESHOLD == 84 is what lets a threshold drift while
        # the test still passes. Pin the TELL COUNT at which pass flips.
        vocab = ["Moreover", "Furthermore", "In summary", "In essence"]
        for n_tells in range(0, 5):
            text = FILLER * 2 + ". ".join(vocab[:n_tells]) + "."
            r = run_synthlint(text)
            assert r["flags"]["_metrics"]["total_tells"] == n_tells
            assert r["passed"] is (n_tells <= C.NOISE_BUDGET), n_tells
        assert C.NOISE_BUDGET == 2

    def test_a_clean_text_scores_the_start_value(self):
        assert run_synthlint(TIMBR_DERIVATION["vol11:city_intro"])["score"] == \
            C.SCORE_START

    def test_the_score_is_clamped_at_zero(self):
        r = run_synthlint(ADV_DERIVATION["adv01_vocab_blatant"])
        assert r["score"] == 0

    def test_a_hard_fail_alone_fails_a_perfect_score(self, monkeypatch):
        # Under the shipped constants every hard fail also drives the score
        # below the threshold, so the corpus cannot tell whether `passed`
        # actually consults hard_fail. Force the case: a check that hard-fails
        # and costs nothing.
        def hard_and_free(text):
            return ["synthetic"], 0, True
        # Patch the module that DEFINES run_synthlint, not whatever
        # `import synthlint` happens to bind: from the repo root that name is
        # the package and patching it would be a silent no-op.
        impl = sys.modules[run_synthlint.__module__]
        monkeypatch.setattr(impl, "CHECKS",
                            impl.CHECKS + (("synthetic", hard_and_free),))
        r = run_synthlint("Train first. Then coffee.")
        assert r["score"] == C.SCORE_START
        assert r["passed"] is False

    def test_a_hard_fail_cannot_be_redeemed_by_score(self):
        text = "Moreover. Furthermore. In summary. In conclusion. To sum up."
        r = run_synthlint(text)
        assert r["flags"]["ai_vocabulary"]["hard_fail"] is True
        assert r["passed"] is False


# ===========================================================================
# Output shape — the orchestrator contract
# ===========================================================================
class TestOutputShape:

    def test_top_level_keys(self):
        r = run_synthlint("Train first. Then coffee.")
        assert set(r) == {"violations", "score", "passed", "flags"}
        assert isinstance(r["violations"], list)
        assert isinstance(r["score"], int)
        assert isinstance(r["passed"], bool)
        assert isinstance(r["flags"], dict)

    def test_every_check_reports_under_its_own_flag(self):
        r = run_synthlint("Train first.")
        for name, _ in synthlint.CHECKS:
            assert set(r["flags"][name]) == {"violations", "penalty", "hard_fail"}

    def test_metrics_are_reported_for_scorecards(self):
        m = run_synthlint(TIMBR_DERIVATION["vol11:editor_body"])["flags"]["_metrics"]
        for key in ("words", "paragraphs", "sentences", "mean_sentence_words",
                    "stdev_sentence_words", "burstiness_cv", "total_tells"):
            assert key in m

    def test_violations_are_the_concatenation_of_the_checks(self):
        r = run_synthlint(ADV_DERIVATION["adv07_mixed_mid"])
        pooled = [v for n, _ in synthlint.CHECKS
                  for v in r["flags"][n]["violations"]]
        assert r["violations"] == pooled

    def test_empty_and_none_are_clean_not_crashes(self):
        for text in ("", None, "   "):
            r = run_synthlint(text)
            assert r["score"] == C.SCORE_START and r["passed"] is True

    def test_a_sections_dict_is_a_type_error_not_a_silent_pass(self):
        with pytest.raises(TypeError, match="expects str"):
            run_synthlint({"Training": "Train first."})

    def test_there_is_no_ruleset_argument(self):
        # Deliberate: reading like an LLM is a defect on every product line.
        import inspect
        assert list(inspect.signature(run_synthlint).parameters) == ["text"]

    def test_run_does_not_mutate_its_input(self):
        text = TIMBR_DERIVATION["vol11:editor_body"]
        before = text
        run_synthlint(text)
        assert text == before

    def test_every_check_returns_the_repo_standard_triple(self):
        for name, fn in synthlint.CHECKS:
            v, p, hf = fn("Train first. Then coffee.")
            assert isinstance(v, list) and isinstance(p, int) and isinstance(hf, bool)
            assert p <= 0, name


# ===========================================================================
# THE CORPUS CONTRACT — derivation split
# ===========================================================================
class TestDerivationCorpus:

    @pytest.mark.parametrize("name", sorted(TIMBR_DERIVATION))
    def test_every_real_timbr_text_passes_clean(self, name):
        r = run_synthlint(TIMBR_DERIVATION[name])
        assert r["passed"] is True, r["violations"]
        assert r["score"] == C.SCORE_START, r["violations"]
        assert r["violations"] == []

    @pytest.mark.parametrize("name", sorted(ADV_DERIVATION))
    def test_every_adversarial_text_fails(self, name):
        r = run_synthlint(ADV_DERIVATION[name])
        assert r["passed"] is False, r["score"]
        assert r["violations"]


# ===========================================================================
# THE CORPUS CONTRACT — held-out split, run cold
# ===========================================================================
class TestHeldOutCorpus:

    @pytest.mark.parametrize("name", sorted(TIMBR_HELDOUT))
    def test_every_held_out_timbr_text_passes_clean(self, name):
        r = run_synthlint(TIMBR_HELDOUT[name])
        assert r["passed"] is True, r["violations"]
        assert r["score"] == C.SCORE_START, r["violations"]

    @pytest.mark.parametrize("name", sorted(ADV_HELDOUT))
    def test_every_held_out_adversarial_text_fails(self, name):
        r = run_synthlint(ADV_HELDOUT[name])
        assert r["passed"] is False, r["score"]

    def test_the_two_corpora_do_not_overlap_in_score(self):
        timbr = [run_synthlint(t)["score"] for t in ALL_TIMBR.values()]
        adv = [run_synthlint(t)["score"] for t in ALL_ADV.values()]
        assert min(timbr) > max(adv)


# ===========================================================================
# CALIBRATION — every derived number recomputed from the corpus
# ===========================================================================
class TestCalibrationHolds:

    def test_the_real_corpus_still_carries_zero_tells(self):
        for name, text in ALL_TIMBR.items():
            assert run_synthlint(text)["flags"]["_metrics"]["total_tells"] == 0, name

    def test_the_flattest_real_text_is_still_above_the_floor(self):
        # BURSTINESS_CV_FLOOR was derived as worst_real x 0.75, rounded down.
        cvs = [burstiness(t)[3] for t in ALL_TIMBR.values()
               if burstiness(t)[0] >= C.BURSTINESS_MIN_SENTENCES
               and burstiness(t)[1] >= C.BURSTINESS_MIN_MEAN_WORDS]
        worst = min(cvs)
        assert worst == pytest.approx(0.3867, abs=0.005)
        assert C.BURSTINESS_CV_FLOOR <= worst * 0.75

    def test_the_weakest_adversarial_text_still_clears_the_budget(self):
        # AI FLOOR: the derivation of NOISE_BUDGET needs the two corpora to
        # stay separated by the interval [0, 3).
        tells = [run_synthlint(t)["flags"]["_metrics"]["total_tells"]
                 for t in ALL_ADV.values()]
        assert min(tells) > C.NOISE_BUDGET

    def test_the_transition_rate_bound_still_holds(self):
        paras = sum(len(split_paragraphs(t)) for t in ALL_TIMBR.values())
        hits = sum(len(transition_openers(t)) for t in ALL_TIMBR.values())
        assert hits == 0
        assert paras >= 114
        rule_of_three = 3 / paras
        assert C.FORMULAIC_TRANSITION_RATE_MAX > rule_of_three * 5

    def test_the_longest_real_anaphoric_sentence_is_under_the_ceiling(self):
        # The ANAPHORA_MAX_WORDS cut sits above every sentence inside a real
        # exempt run and below every sentence inside the adversarial one.
        real = max(word_count(s) for s in [
            "No timing protocol worth the attention it gets.",
            "It is the barbell."])
        assert real <= C.ANAPHORA_MAX_WORDS
        adv_run = repeated_opener_runs(ADV_DERIVATION["adv04_openers"])
        assert min(word_count(s) for _, _, run in adv_run for s in run) > \
            C.ANAPHORA_MAX_WORDS

    def test_the_corpus_is_the_size_the_derivation_claims(self):
        assert len(TIMBR_DERIVATION) == 29
        assert len(TIMBR_HELDOUT) == 6
        assert len(ADV_DERIVATION) == 12
        assert len(ADV_HELDOUT) == 4
        assert len(TIMBR_SPEC_LISTS) == 6

    def test_the_spec_lists_are_all_below_the_cv_floor_as_rows(self):
        # The defect, recomputed. synth_config records vol11 at CV 0.116 and
        # 0.085; every shipped list is under the floor when its ROWS are read
        # as sentences, so this is not a vol11 anomaly.
        measured = {name: round(burstiness(t)[3], 3)
                    for name, t in TIMBR_SPEC_LISTS.items()}
        assert all(cv < C.BURSTINESS_CV_FLOOR for cv in measured.values()), measured
        assert measured["vol11:workout_p4"] == pytest.approx(0.116, abs=0.005)
        assert measured["vol11:workout_p5"] == pytest.approx(0.085, abs=0.005)

    def test_the_six_that_shipped_clean_were_saved_by_the_mean_gate(self):
        # And this is why the fix had to be structural. The lists that passed
        # before the fix passed on row mean alone — vol11's rows are one or two
        # words longer, which is the entire difference between shipping and a
        # 44. Every list is over the gate on its own merits only now.
        over = {n: round(burstiness(t)[1], 2) for n, t in TIMBR_SPEC_LISTS.items()
                if burstiness(t)[1] >= C.BURSTINESS_MIN_MEAN_WORDS}
        assert sorted(over) == ["vol11:workout_p4", "vol11:workout_p5"], over
        under = [round(burstiness(t)[1], 2) for n, t in TIMBR_SPEC_LISTS.items()
                 if n not in over]
        assert max(under) < C.BURSTINESS_MIN_MEAN_WORDS
        assert max(under) > C.BURSTINESS_MIN_MEAN_WORDS - 1.5, under

    def test_the_field_gate_separates_the_lists_from_the_forgeries(self):
        # The separation the exemption rests on, recomputed from both sides.
        # synth_config records real field means of 2.56-5.11 and forged means
        # of 9.27-11.57, either side of BURSTINESS_MIN_MEAN_WORDS = 8.
        def field_mean(text):
            return statistics.mean([word_count(f) for f in spec_list_fields(text)])

        real = [field_mean(t) for t in TIMBR_SPEC_LISTS.values()]
        forged = [field_mean(_forged_rows(ALL_ADV[n], where=w))
                  for n in FLAT_ONLY_ADV for w in ("cue", "label")]
        assert max(real) < C.BURSTINESS_MIN_MEAN_WORDS <= min(forged)
        assert max(real) == pytest.approx(5.11, abs=0.05)
        assert min(forged) == pytest.approx(9.27, abs=0.05)
        # and every forged text is flat enough to fire once it is measured
        for n in FLAT_ONLY_ADV:
            for w in ("cue", "label"):
                text = _forged_rows(ALL_ADV[n], where=w)
                cv = statistics.pstdev([word_count(f) for f in spec_list_fields(text)]) \
                    / field_mean(text)
                assert cv < C.BURSTINESS_CV_FLOOR, (n, w, cv)


# ===========================================================================
# MUTATION TESTING
# ===========================================================================
# A mutant is KILLED when _assert_contract raises on it. Before any kill is
# trusted the harness itself has to be shown to work, so three no-op mutations
# run first and MUST survive: if a comment change "kills" a mutant the harness
# is measuring itself, not the module.

_IMPORT_BLOCK = re.compile(
    r"try:.*?from synthlint import synth_config as C.*?"
    r"except ImportError:.*?import synth_config as C\n", re.DOTALL)


def _read(name):
    return open(os.path.join(MODULE_DIR, name)).read()


def _build(config_src, lint_src):
    """Load a mutated SynthLint into a throwaway module pair."""
    cfg = types.ModuleType("mutant_synth_config")
    cfg.__file__ = os.path.join(MODULE_DIR, "synth_config.py")
    exec(compile(config_src, "<mutant_config>", "exec"), cfg.__dict__)
    lint = types.ModuleType("mutant_synthlint")
    lint.__file__ = os.path.join(MODULE_DIR, "synthlint.py")
    lint.__dict__["C"] = cfg
    stripped = _IMPORT_BLOCK.sub("", lint_src)
    exec(compile(stripped, "<mutant_synthlint>", "exec"), lint.__dict__)
    return lint


def _assert_contract(m):
    """Everything SynthLint promises, restated against an arbitrary module."""
    # 1. the corpus verdicts
    for name, text in ALL_TIMBR.items():
        r = m.run_synthlint(text)
        assert r["passed"] and r["score"] == m.C.SCORE_START, f"timbr {name}"
    for name, text in ALL_ADV.items():
        assert not m.run_synthlint(text)["passed"], f"adv {name}"

    # 2. the exemptions that keep the checks off TIMBR's own devices
    assert m.repeated_opener_runs(
        "It is not CrossFit. It is not Pilates. It is the barbell.") == []
    assert m.repeated_opener_runs(
        "No loading phase. No cycling. No timing protocol worth the attention "
        "it gets.") == []
    assert m.repeated_opener_runs(
        "The turkey and white bean bowl is 41g protein, 29g carbs, 19g fat, "
        "$16. The smoked trout plate with rye is 39g protein, 31g carbs, 21g "
        "fat, $17. The egg and barley skillet is 42g protein, 28g carbs, 20g "
        "fat, $14. The cold roast chicken with beans is 38g protein, 27g "
        "carbs, 18g fat, $15.") == []
    assert m.repeated_opener_runs(
        " ".join(_LONG.format(w=w) for w in ["The bar", "The rack", "The floor"])
    ) == []
    assert m.check_burstiness(_uniform(12, 4)) == ([], 0, False)
    assert m.check_burstiness(
        TIMBR_DERIVATION["vol11:post_stack_body"]) == ([], 0, False)
    for name, text in TIMBR_SPEC_LISTS.items():
        assert m.is_spec_list(text) is True, f"spec list {name}"
        assert m.check_burstiness(text) == ([], 0, False), f"spec list {name}"
        r = m.run_synthlint(text)
        assert r["passed"] and r["score"] == m.C.SCORE_START, f"spec list {name}"
    assert m.hedge_stacks(
        "held for a use the previous tenant could not possibly match") == []
    assert m.hedge_stacks("It is roughly about the same distance.") == []
    assert m.hedge_stacks(
        "Members often report better sleep, and the effect is typically "
        "small.") == []
    assert m.hedge_stacks(
        "Members often report better sleep on the nights they typically use "
        "it.") == []
    assert m.check_contrastive_frames(
        "Strength training isn't just about lifting heavy things. " + FILLER
    ) == ([], 0, False)
    assert m.check_transition_density(
        "Moreover, the racks fill early.\n" + _P * 3) == ([], 0, False)

    # 3. the positives
    assert len(m.repeated_opener_runs(" ".join(
        _LONG.format(w=w) for w in ["The bar", "The rack", "The floor",
                                    "The coach"]))) == 1
    assert len(m.repeated_opener_runs(
        "This means the muscle receives a stimulus it has not seen before. "
        "It allows the body to adapt over the following days and weeks. "
        "These are the changes that accumulate across a training block of "
        "several weeks."
    )) == 1
    assert len(m.repeated_opener_runs(ADV_DERIVATION["adv04_openers"])) == 2
    assert len(m.repeated_opener_runs(
        "The Ballard room opened in 2021 and has not changed its schedule "
        "since. The Georgetown room opened in 2019 and still runs the same "
        "four classes. The Fremont room opened in 2022 and lost its lease the "
        "following winter. The Eastlake room opened in 2018 and has quietly "
        "outlasted all of them.")) == 1
    assert m.check_burstiness(_uniform(12, 12))[1] < 0
    assert len(m.hedge_stacks("It may possibly potentially help a little.")) == 1
    assert m.check_hedge_stacking(
        "It may potentially help. The dose could possibly matter.")[2] is False
    assert m.check_hedge_stacking(
        "It may potentially help. The dose could possibly matter. The effect "
        "might perhaps persist.")[2] is True
    assert m.check_transition_density(
        "Moreover, a.\nFurthermore, b.\n" + _P * 3)[1] < 0
    assert m.check_contrastive_frames(
        "It isn't just a gym. It's not about weight. " + FILLER)[1] < 0
    four = "Moreover. Furthermore. In summary. In conclusion."
    assert m.check_ai_vocabulary(four)[2] is False
    assert m.check_ai_vocabulary(four + " Needless to say.")[2] is True

    # 3b. the spec-list exemption, from both sides. The detector's clauses are
    #     asserted directly, not only through verdicts: a clause that stops
    #     doing anything widens the exemption, and the widening is the defect
    #     even when a downstream check happens to cover for it.
    assert m.is_spec_list(_ROWS) is True
    assert m.spec_list_rows(FILLER) is None
    assert m.is_spec_list("\n".join(_ROWS.split("\n")[:3])) is False
    assert m.is_spec_list(_ROWS + "\nThe room opens at five thirty.") is False
    assert m.is_spec_list(_HEADED_ROWS) is False
    assert m.is_spec_list(_ROWS.replace("upright", "upright.")) is False
    assert m.is_spec_list("- alpha\n- bravo\n- charlie\n- delta") is False
    assert m.is_spec_list(_MIXED_DELIMS) is False
    assert m.is_spec_list(
        "- Sleep is the lever — it is free\n"
        "- Food is the second — it is not\n"
        "- Walking is underrated — it costs nothing\n"
        "- Deloads get skipped — they should not be") is False
    assert m.spec_list_fields(
        TIMBR_SPEC_LISTS["vol11:workout_p4"])[0] == "activation, learn the hinge"
    for name in FLAT_ONLY_ADV:
        for keep in (True, False):
            evaded = _bulleted(ALL_ADV[name], keep_stops=keep)
            assert m.is_spec_list(evaded) is False, f"bulleted {name}"
            assert not m.run_synthlint(evaded)["passed"], f"bulleted {name}"
        for where in ("cue", "label"):
            forged = _forged_rows(ALL_ADV[name], where=where)
            assert m.is_spec_list(forged) is True, f"forged {name}/{where}"
            assert m.check_burstiness(forged)[1] < 0, f"forged {name}/{where}"
            assert not m.run_synthlint(forged)["passed"], f"forged {name}/{where}"

    # 4. segmentation and the scale
    assert m.split_sentences("The Night Off\nSouth Lake Union") == [
        "The Night Off", "South Lake Union"]
    assert m.split_paragraphs("Alpha.\nBravo.\nCharlie.") == [
        "Alpha.", "Bravo.", "Charlie."]
    assert m.burstiness("One two. One two three four.")[2] == pytest.approx(1.0)
    vocab = ["Moreover", "Furthermore", "In summary", "In essence"]
    for n in range(0, 5):
        r = m.run_synthlint(FILLER * 2 + ". ".join(vocab[:n]) + ".")
        assert r["flags"]["_metrics"]["total_tells"] == n, f"{n} tells"
        assert r["passed"] is (n <= 2), f"effective bar at {n} tells"


#: (name, config mutation, lint mutation). None means "leave that file alone".
_NOOP_CONTROLS = [
    ("noop-trailing-comment",
     lambda s: s + "\n# harmless trailing comment\n",
     lambda s: s + "\n# harmless trailing comment\n"),
    ("noop-extra-blank-line", lambda s: s, lambda s: s.replace(
        "\nimport re\n", "\n\nimport re\n", 1)),
    ("noop-docstring-whitespace", lambda s: s.replace(
        '"""\n\nimport re', '"""\n\n\nimport re', 1), lambda s: s),
]

_MUTANTS = [
    # thresholds
    ("cv-floor raised above real copy",
     lambda s: s.replace("BURSTINESS_CV_FLOOR = 0.29",
                         "BURSTINESS_CV_FLOOR = 0.55"), None),
    ("cv-floor lowered under the slop",
     lambda s: s.replace("BURSTINESS_CV_FLOOR = 0.29",
                         "BURSTINESS_CV_FLOOR = 0.10"), None),
    ("burstiness sentence gate removed",
     lambda s: s.replace("BURSTINESS_MIN_SENTENCES = 8",
                         "BURSTINESS_MIN_SENTENCES = 2"), None),
    ("staccato exemption removed",
     lambda s: s.replace("BURSTINESS_MIN_MEAN_WORDS = 8",
                         "BURSTINESS_MIN_MEAN_WORDS = 0"), None),
    ("same-opener run lowered to the triad",
     lambda s: s.replace("SAME_OPENER_RUN_MIN = 4",
                         "SAME_OPENER_RUN_MIN = 3"), None),
    ("same-opener run raised past the slop",
     lambda s: s.replace("SAME_OPENER_RUN_MIN = 4",
                         "SAME_OPENER_RUN_MIN = 5"), None),
    ("generic-opener run raised",
     lambda s: s.replace("GENERIC_OPENER_RUN_MIN = 3",
                         "GENERIC_OPENER_RUN_MIN = 4"), None),
    ("anaphora exemption disabled",
     lambda s: s.replace("ANAPHORA_MAX_WORDS = 10",
                         "ANAPHORA_MAX_WORDS = 0"), None),
    ("anaphora exemption widened to swallow exposition",
     lambda s: s.replace("ANAPHORA_MAX_WORDS = 10",
                         "ANAPHORA_MAX_WORDS = 40"), None),
    ("data-listing exemption disabled",
     lambda s: s.replace("DATA_LISTING_MIN_NUMBERS = 2",
                         "DATA_LISTING_MIN_NUMBERS = 99"), None),
    ("hedge adjacency widened to co-occurrence",
     lambda s: s.replace("HEDGE_STACK_MAX_GAP_WORDS = 2",
                         "HEDGE_STACK_MAX_GAP_WORDS = 12"), None),
    ("negated-modal guard removed",
     lambda s: s.replace('HEDGE_NEGATION_GUARD = r"(?!\\s+(?:not|n\'?t))"',
                         'HEDGE_NEGATION_GUARD = r""'), None),
    ("measurement qualifiers added to the hedge lexicon",
     lambda s: s.replace('r"presumably|apparently"',
                         'r"presumably|apparently|about|around|roughly"'), None),
    ("noise budget loosened",
     lambda s: s.replace("NOISE_BUDGET = 2", "NOISE_BUDGET = 5"), None),
    ("noise budget tightened to zero",
     lambda s: s.replace("NOISE_BUDGET = 2", "NOISE_BUDGET = 0"), None),
    ("transition rate raised",
     lambda s: s.replace("FORMULAIC_TRANSITION_RATE_MAX = 0.20",
                         "FORMULAIC_TRANSITION_RATE_MAX = 0.90"), None),
    ("transition single-hit gate removed",
     lambda s: s.replace("FORMULAIC_TRANSITION_MIN_HITS = 2",
                         "FORMULAIC_TRANSITION_MIN_HITS = 1"), None),
    ("contrastive rate raised",
     lambda s: s.replace("CONTRASTIVE_RATE_MAX = 2.0",
                         "CONTRASTIVE_RATE_MAX = 30.0"), None),
    ("contrastive min-words gate restored to the buggy value",
     lambda s: s.replace("CONTRASTIVE_MIN_WORDS = 40",
                         "CONTRASTIVE_MIN_WORDS = 200"), None),
    ("contrastive single-frame gate removed",
     lambda s: s.replace("CONTRASTIVE_MIN_HITS = 2",
                         "CONTRASTIVE_MIN_HITS = 1"), None),
    ("vocab hard fail on a single hit",
     lambda s: s.replace("VOCAB_HARD_FAIL_HITS = 5",
                         "VOCAB_HARD_FAIL_HITS = 1"), None),
    ("vocab hard fail disabled",
     lambda s: s.replace("VOCAB_HARD_FAIL_HITS = 5",
                         "VOCAB_HARD_FAIL_HITS = 99"), None),
    ("hedge hard fail on a single stack",
     lambda s: s.replace("HEDGE_STACK_HARD_FAIL = 3",
                         "HEDGE_STACK_HARD_FAIL = 1"), None),
    # logic
    ("newline no longer separates paragraphs", None,
     lambda s: s.replace('re.split(r"\\n\\s*\\n+|\\n", text)',
                         're.split(r"\\n\\s*\\n+", text)')),
    ("newline no longer separates sentences", None,
     lambda s: s.replace('for line in re.split(r"\\n+", text):',
                         'for line in [text]:')),
    ("sample stdev instead of population stdev", None,
     lambda s: s.replace("sd = statistics.pstdev(lengths)",
                         "sd = statistics.stdev(lengths) if len(lengths) > 1 "
                         "else 0.0")),
    ("opener-run span de-duplication removed", None,
     lambda s: s.replace("        if span <= covered:\n            return\n", "")),
    ("hedge per-clause de-duplication removed", None,
     lambda s: s.replace(
         '                    stacked = ("adjacent", a.group(0), b.group(0))\n'
         "                    break",
         '                    found.append(("adjacent", a.group(0), '
         "b.group(0), clause.strip()))")),
    ("data-listing counts digits instead of numbers", None,
     lambda s: s.replace(r'_NUMBER_RE = re.compile(r"\d+(?:[.,:/]\d+)*")',
                         r'_NUMBER_RE = re.compile(r"\d")')),
    # spec-list detection and the rhythm unit
    ("spec-list row minimum raised past a real list",
     lambda s: s.replace("SPEC_LIST_MIN_ROWS = 4",
                         "SPEC_LIST_MIN_ROWS = 99"), None),
    ("spec-list row minimum lowered to two",
     lambda s: s.replace("SPEC_LIST_MIN_ROWS = 4",
                         "SPEC_LIST_MIN_ROWS = 2"), None),
    ("one shared dash is enough to be a template",
     lambda s: s.replace("SPEC_LIST_MIN_SHARED_DELIMITERS = 2",
                         "SPEC_LIST_MIN_SHARED_DELIMITERS = 1"), None),
    ("shared-skeleton requirement raised past the real core",
     lambda s: s.replace("SPEC_LIST_MIN_SHARED_DELIMITERS = 2",
                         "SPEC_LIST_MIN_SHARED_DELIMITERS = 4"), None),
    ("the bullet glyph is dropped from the marker",
     lambda s: s.replace(r'SPEC_LIST_MARKER = r"^\s*(?:[-*•‣▪–—]|\d{1,2}[.)])\s+"',
                         r'SPEC_LIST_MARKER = r"^\s*(?:[*•‣▪]|\d{1,2}[.)])\s+"'),
     None),
    ("the full-stop clause is disabled",
     lambda s: s.replace(
         'SPEC_LIST_TERMINAL_PUNCTUATION = r"[.!?][\\"\'”’)\\]]*$"',
         'SPEC_LIST_TERMINAL_PUNCTUATION = r"(?!x)x"'), None),
    ("the comma is treated as a structural delimiter",
     lambda s: s.replace('SPEC_LIST_DELIMITERS = ":—–×|·→="',
                         'SPEC_LIST_DELIMITERS = ":—–×|·→=,"'), None),
    ("a spec list is exempted from the rhythm check entirely", None,
     lambda s: s.replace(
         '    spec = is_spec_list(text)\n'
         '    if spec:\n'
         '        unit, units = "row-field", spec_list_fields(text)\n',
         '    spec = is_spec_list(text)\n'
         '    if spec:\n'
         '        return [], 0, False\n'
         '    if spec:\n'
         '        unit, units = "row-field", spec_list_fields(text)\n')),
    ("the rhythm unit is the whole row instead of its field", None,
     lambda s: s.replace('unit, units = "row-field", spec_list_fields(text)',
                         'unit, units = "row-field", spec_list_rows(text)')),
    ("the rhythm unit is the last field instead of the longest", None,
     lambda s: s.replace("fields.append(max(parts, key=word_count))",
                         "fields.append(parts[-1])")),
    ("detection accepts a text where only SOME lines are rows", None,
     lambda s: s.replace(
         "    if not all(C.SPEC_LIST_MARKER_RE.match(r) for r in rows):",
         "    if not any(C.SPEC_LIST_MARKER_RE.match(r) for r in rows):")),
    ("the shared-skeleton clause is computed as a union, not an intersection",
     None,
     lambda s: s.replace("shared = set.intersection(*(set(C.SPEC_LIST_DELIM_RE.findall(b))",
                         "shared = set.union(*(set(C.SPEC_LIST_DELIM_RE.findall(b))")),
]


class TestMutationHarness:

    def test_the_harness_finds_the_import_block_it_strips(self):
        # If synthlint.py's import block is ever reworded, the harness would
        # silently load the REAL config and every mutant would survive. Fail
        # loudly instead.
        assert _IMPORT_BLOCK.search(_read("synthlint.py"))

    def test_the_baseline_module_satisfies_the_contract(self):
        _assert_contract(_build(_read("synth_config.py"), _read("synthlint.py")))

    @pytest.mark.parametrize("name,cfg_fn,lint_fn", _NOOP_CONTROLS,
                             ids=[c[0] for c in _NOOP_CONTROLS])
    def test_noop_controls_survive(self, name, cfg_fn, lint_fn):
        cfg_src, lint_src = _read("synth_config.py"), _read("synthlint.py")
        mutated_cfg, mutated_lint = cfg_fn(cfg_src), lint_fn(lint_src)
        assert (mutated_cfg, mutated_lint) != (cfg_src, lint_src), \
            "control mutation did not apply"
        _assert_contract(_build(mutated_cfg, mutated_lint))


class TestMutantsAreKilled:

    @pytest.mark.parametrize("name,cfg_fn,lint_fn", _MUTANTS,
                             ids=[m[0] for m in _MUTANTS])
    def test_mutant_is_killed(self, name, cfg_fn, lint_fn):
        cfg_src, lint_src = _read("synth_config.py"), _read("synthlint.py")
        new_cfg = cfg_fn(cfg_src) if cfg_fn else cfg_src
        new_lint = lint_fn(lint_src) if lint_fn else lint_src
        assert (new_cfg, new_lint) != (cfg_src, lint_src), \
            f"mutation {name!r} did not apply — its target string moved"
        with pytest.raises((AssertionError, ValueError, TypeError,
                            KeyError, IndexError, re.error)):
            _assert_contract(_build(new_cfg, new_lint))
