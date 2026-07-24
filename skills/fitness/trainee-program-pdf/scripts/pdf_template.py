import sys
sys.path.insert(0, '/home/hermes/.local/lib/python3.12/site-packages')
import warnings
warnings.filterwarnings('ignore')
from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT = '/home/hermes/Blair_T1_Program.pdf'

# --- Palette ---
DARK       = (15, 15, 15)
CARD_BG    = (26, 26, 26)
WHITE      = (255, 255, 255)
OFF_WHITE  = (245, 245, 245)
GREY_LIGHT = (200, 200, 200)
GREY_MID   = (140, 140, 140)
GREY_DARK  = (70, 70, 70)
TEAL       = (34, 95, 107)
TEAL_LIGHT = (220, 242, 246)
ORANGE     = (220, 128, 32)
AMBER      = (190, 148, 40)
AMBER_LIGHT= (255, 248, 215)
ROW_A      = (248, 248, 248)
ROW_B      = (237, 237, 237)

PHASE_COLORS = [
    (38, 120, 100),
    (60,  95, 165),
    (160, 100, 35),
    (120, 50, 155),
    (185, 50,  60),
]

def c(s):
    repl = {'\u2013':'-','\u2014':'-','\u2019':"'",'\u2018':"'",
            '\u201c':'"','\u201d':'"','\u2022':'-','\u2192':'->',
            '\u00d7':'x','\u2248':'~','\u2264':'<=','\u2265':'>='}
    for u,a in repl.items(): s = s.replace(u,a)
    return s.encode('latin-1','replace').decode('latin-1')

class PDF(FPDF):
    def header(self): pass

    def footer(self):
        self.set_y(-9)
        self.set_font('Helvetica','',6)
        self.set_text_color(*GREY_MID)
        self.cell(0,4,c('Blair Grimes  -  T1 Campaign  -  Designed by Tanzim Ozer'),align='C')

    # ── helpers ────────────────────────────────────────────────

    def hline(self, color=GREY_LIGHT, width=0.2):
        self.set_draw_color(*color)
        self.set_line_width(width)
        self.line(self.l_margin, self.get_y(), self.l_margin + self.epw, self.get_y())
        self.ln(1)

    def tag(self, label, color=TEAL):
        self.set_font('Helvetica','B',6)
        self.set_text_color(*color)
        self.cell(0,3,c(label),new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    def page_header(self, small_label, big_title):
        self.ln(3)
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_MID)
        self.cell(0,3,c(small_label),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_font('Helvetica','B',18)
        self.set_text_color(*DARK)
        self.cell(0,8,c(big_title),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_fill_color(*TEAL)
        self.rect(self.l_margin, self.get_y(), 28, 1.2, 'F')
        self.ln(3)

    def section_bar(self, left_text, right_text='', color=DARK):
        w = self.epw
        self.set_fill_color(*color)
        y = self.get_y()
        self.rect(self.l_margin, y, w, 5.5, 'F')
        self.set_xy(self.l_margin + 2, y + 0.8)
        self.set_font('Helvetica','B',7)
        self.set_text_color(*WHITE)
        self.cell(w * 0.55, 4, c(left_text))
        if right_text:
            self.set_font('Helvetica','',6)
            self.set_text_color(200,220,225)
            self.cell(w * 0.45, 4, c(right_text), align='R')
        self.ln(5.5)

    def meal_card(self, title, tag_text, foods, supps, macro_bar=''):
        lm = self.l_margin
        w  = self.epw

        # Estimate height
        food_h  = sum(1 + len(f)//60 for f in foods) * 3.5
        supp_h  = (4 + sum(1 + len(s)//70 for s in supps) * 3.2) if supps else 0
        total_h = 5.5 + food_h + supp_h + 4
        if self.get_y() + total_h > 278:
            self.add_page()

        self.section_bar(title, tag_text)
        card_top = self.get_y()

        # Foods
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_DARK)
        for food in foods:
            self.set_x(lm + 3)
            self.multi_cell(w - 3, 3.5, c('- ' + food))

        # Supplements
        if supps:
            self.ln(1)
            self.set_x(lm + 3)
            self.set_font('Helvetica','B',6.5)
            self.set_text_color(*ORANGE)
            self.cell(w - 3, 3.5, 'SUPPLEMENTS:')
            self.ln(3.5)
            self.set_font('Helvetica','',6.5)
            self.set_text_color(*GREY_DARK)
            for s in supps:
                self.set_x(lm + 5)
                self.multi_cell(w - 5, 3.2, c('- ' + s))

        card_bot = self.get_y() + 0.5
        self.set_fill_color(*TEAL)
        self.rect(lm, card_top, 1.5, card_bot - card_top, 'F')
        self.set_y(card_bot + 2)

    def callout(self, text, border_color=TEAL, bg=TEAL_LIGHT):
        lm, w = self.l_margin, self.epw
        lines = len(text) // 95 + 2
        needed = lines * 3.8 + 4
        if self.get_y() + needed > 278: self.add_page()
        y = self.get_y()
        self.set_xy(lm + 3, y + 1.5)
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        self.multi_cell(w - 4, 3.8, c(text))
        end_y = self.get_y() + 1.5
        height = end_y - y
        self.set_fill_color(*bg)
        self.rect(lm, y, w, height, 'F')
        self.set_fill_color(*border_color)
        self.rect(lm, y, 2, height, 'F')
        self.set_xy(lm + 4, y + 1.5)
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        self.multi_cell(w - 5, 3.8, c(text))
        self.set_y(end_y + 2)

    # ── PAGES ───────────────────────────────────────────────────

    def cover(self):
        self.add_page()
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 297, 'F')

        self.set_xy(0, 20)
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_MID)
        self.cell(210, 4, c('T1 CAMPAIGN  -  PERSONALIZED PROGRAM'), align='C')

        self.set_xy(0, 44)
        self.set_font('Helvetica','B',40)
        self.set_text_color(*WHITE)
        self.cell(210, 16, c('Blair Grimes'), align='C')

        self.set_xy(0, 63)
        self.set_font('Helvetica','',13)
        self.set_text_color(*GREY_LIGHT)
        self.cell(210, 6, c('6-Week Transformation Plan'), align='C')

        self.set_fill_color(*TEAL)
        self.rect(78, 72, 54, 1.5, 'F')

        # Stats
        stats = [
            [('GOAL EVENT','Mexico - June 13'),('BODYWEIGHT','178 lbs'),('DAILY TARGET','1,750 cal')],
            [('PROTEIN','178g / day'),('TRAINING SPLIT','4 + 1 Pilates'),('PROGRAM TYPE','Hypertrophy + Depletion')],
        ]
        y0 = 82
        xs = [20, 84, 148]
        cw = 58
        for row in stats:
            for i,(lbl,val) in enumerate(row):
                self.set_xy(xs[i], y0)
                self.set_font('Helvetica','',6)
                self.set_text_color(*GREY_MID)
                self.cell(cw, 4, c(lbl), align='C')
                self.set_xy(xs[i], y0 + 4.5)
                self.set_font('Helvetica','B',11)
                self.set_text_color(*WHITE)
                self.cell(cw, 6, c(val), align='C')
            y0 += 16

        # Phase timeline
        phases = [
            ('Phase 1 - Depletion + Flush','May 4-24'),
            ('Phase 2 - Intensify','May 25-Jun 1'),
            ('Phase 3 - Pre-Peak','Jun 2-6'),
            ('Phase 4 - Carb Reload','Jun 7-11'),
            ('Phase 5 - Peak Day','Jun 12-13'),
        ]
        y = 126
        for i,(name,dates) in enumerate(phases):
            pc = PHASE_COLORS[i]
            self.set_fill_color(*CARD_BG)
            self.rect(20, y, 170, 12, 'F')
            self.set_fill_color(*pc)
            self.rect(20, y, 2.5, 12, 'F')
            self.set_xy(25, y+1)
            self.set_font('Helvetica','B',8.5)
            self.set_text_color(*pc)
            self.cell(110, 4.5, c(name))
            self.set_xy(25, y+5.5)
            self.set_font('Helvetica','',7)
            self.set_text_color(*GREY_LIGHT)
            self.cell(110, 4, c(dates))
            y += 14

        self.set_xy(0, 284)
        self.set_font('Helvetica','',6)
        self.set_text_color(*GREY_DARK)
        self.cell(210, 4, 'Confidential - Personal Use Only', align='C')

    def phase_overview(self):
        self.add_page()
        self.page_header('THE PLAN AT A GLANCE', 'Phase Overview')

        hdrs = ['PHASE','DATES','CAL','PROTEIN','CARBS','FAT','PRIMARY GOAL']
        ws   = [32, 32, 15, 17, 15, 12, 57]
        self.set_fill_color(*DARK)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica','B',6.5)
        for h,w in zip(hdrs,ws): self.cell(w,5.5,c(h),fill=True)
        self.ln()

        rows = [
            ('Phase 1\nDepletion + Flush','May 4-24','1,750','178g','100g','71g','Burn fat, flush water, build muscle'),
            ('Phase 2\nIntensify','May 25-Jun 1','1,650','178g','80g','69g','Deeper deficit, sharpen conditioning'),
            ('Phase 3\nPre-Peak','Jun 2-6','1,600','178g','60g','72g','Final glycogen depletion, sodium taper'),
            ('Phase 4\nCarb Reload','Jun 7-11','2,072','178g','250g','40g','Supercompensation - full 3D look'),
            ('Phase 5\nPeak Day Prep','Jun 12-13','2,000','178g','200g','54g','Peak physique for Mexico'),
        ]
        for i,(phase,*rest) in enumerate(rows):
            bg = ROW_A if i%2==0 else ROW_B
            self.set_fill_color(*bg)
            lines = phase.split('\n')
            y0 = self.get_y()
            self.set_xy(self.l_margin, y0)
            self.set_font('Helvetica','B',6.5)
            self.set_text_color(*PHASE_COLORS[i])
            self.cell(ws[0], 4.2, c(lines[0]), fill=True)
            self.set_font('Helvetica','',6)
            self.set_text_color(*GREY_MID)
            for v,w in zip(rest,ws[1:]):
                self.cell(w,4.2,c(v),fill=True)
            self.ln()
            self.set_xy(self.l_margin, self.get_y())
            self.set_font('Helvetica','',6)
            self.set_text_color(*GREY_DARK)
            self.set_fill_color(*bg)
            self.cell(ws[0],3.5,c(lines[1] if len(lines)>1 else ''),fill=True)
            self.cell(sum(ws[1:]),3.5,'',fill=True)
            self.ln()

        self.ln(2)
        self.callout(
            'WEEKLY REFEED (Phases 1-2 only): Once per week on a training day. '
            'Carbs bump to 150g. Protein stays 178g. Fat reduces slightly. Total ~1,750 cal. '
            'Purpose: Reset leptin, prevent metabolic adaptation, amplify fat loss on following days. Do not skip.',
            AMBER, AMBER_LIGHT
        )

        self.ln(1)
        self.set_font('Helvetica','B',9)
        self.set_text_color(*DARK)
        self.cell(0,5,'Rules That Never Change',new_x=XPos.LMARGIN,new_y=YPos.NEXT)

        cols3 = [
            ('PROTEIN',[
                '178g every single day - no exceptions',
                'Min 40g protein per meal',
                'Sources: chicken, tilapia, turkey, egg whites, Greek yogurt',
                'Collagen does NOT count toward 178g (no MPS signal)',
            ]),
            ('CARBS',[
                'Strict phase ceiling - zero flexibility',
                'Cluster carbs around training window on training days',
                'Karbolyn (~12g) counts toward daily total',
                'No bread, pasta, wraps, or processed carbs',
            ]),
            ('ALWAYS AVOID',[
                'Processed / packaged foods',
                'Dairy - except 0% Greek yogurt',
                'High-sodium condiments',
                'Alcohol - zero tolerance',
                'Banana / coconut water (Phases 1-3)',
            ]),
        ]
        cw3 = self.epw / 3
        xs3 = [self.l_margin, self.l_margin+cw3, self.l_margin+2*cw3]
        y_save = self.get_y()
        for i,(heading,items) in enumerate(cols3):
            cy = y_save
            self.set_xy(xs3[i], cy)
            self.set_font('Helvetica','B',7)
            self.set_text_color(*TEAL)
            self.cell(cw3,4,c(heading))
            cy += 4.5
            self.set_font('Helvetica','',6.5)
            self.set_text_color(*GREY_DARK)
            for item in items:
                self.set_xy(xs3[i], cy)
                self.multi_cell(cw3-2, 3.5, c('- '+item))
                cy = self.get_y()

    def training_day(self):
        self.add_page()
        self.page_header('DAILY BLUEPRINT - TRAINING DAYS', 'Training Day')
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_DARK)
        self.cell(0,3.5,c('Follow this structure on all 4 weight training days'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(1)

        self.callout(
            'CARB TIMING: Cluster 50-55g around training window (pre + intra + post). '
            'Remaining carbs split across Meal 2 and Meal 3.', TEAL, TEAL_LIGHT
        )

        self.meal_card(
            'WAKE UP - FASTED','Before food - non-negotiable',
            ['500ml water immediately',
             'Apple Cider Vinegar - 1 tbsp in water (insulin sensitivity)'],
            ['Yohimbine - 5-20mg (fasted AM only, titrate up slowly)',
             'Vitamin D - 4,000 IU',
             'EGCG - 400mg',
             'HMB - 1g (first of 3 daily doses)'],
        )
        self.meal_card(
            'MEAL 1 - ~60 MIN AFTER WAKE','P: 59g | C: 12-15g | F: 24g | ~480 cal',
            ['4 egg whites + 1 whole egg (scrambled or omelette)',
             '100g chicken breast or 93% lean ground turkey',
             'Cooked spinach or Swiss chard (unlimited)',
             '1/2 avocado (fat + potassium)',
             'Lemon juice, herbs - no soy sauce or high-sodium condiments'],
            ['HMB - 1g (second dose)',
             'Omega-3 Fish Oil - 1-2g EPA+DHA',
             'L-Carnitine L-Tartrate - 1g (half daily dose)'],
        )
        self.meal_card(
            'PRE-WORKOUT - 45-60 MIN BEFORE','Primary carb window',
            ['Karbolyn - quarter serving (~12-13g carbs) in water',
             'Collagen Peptides - 15g in water (fascia remodeling - NOT protein)',
             'Beet Root Powder - 500mg-1g (nitric oxide, pump)'],
            ['Kre-Alkalyn - 3g (buffered creatine, no bloat)'],
        )
        self.meal_card(
            'INTRA-WORKOUT','Sip throughout - never train depleted',
            ['Performance EAA - 10-15g in 500ml water',
             'Continue sipping water throughout session'],
            [],
        )
        self.meal_card(
            'MEAL 2 - POST-WORKOUT','P: 59g | C: 25-30g | F: 24g | ~550 cal',
            ['180-200g chicken breast or tilapia / cod',
             '3/4 cup cooked white jasmine rice',
             'Cooked vegetables (spinach, broccoli, zucchini - unlimited)',
             'Olive oil drizzle or 1/2 avocado'],
            ['L-Carnitine L-Tartrate - 1g (second dose)',
             'HMB - 1g (third and final dose)'],
        )
        self.meal_card(
            'MEAL 3 - DINNER','P: 60g | C: ~20g | F: 23g | ~510 cal',
            ['180-200g wild salmon or 93% lean turkey / chicken',
             '100g sweet potato (baked) or 40g rolled oats',
             'Large salad: spinach, Swiss chard, cucumber',
             'Avocado or olive oil as fat source'],
            ['Omega-3 Fish Oil - 1-2g EPA+DHA',
             'Noctrine - 1 serving (before bed)'],
        )

        self.set_font('Helvetica','I',6.5)
        self.set_text_color(*GREY_MID)
        self.cell(0,4,c('WATER: 3.5-4L/day (Phases 1-3), taper to 1.5-2L last 24-36 hrs.  |  SAUNA: 20-30 min post-workout, 3-4x/week.'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    def rest_day(self):
        self.add_page()
        self.page_header('DAILY BLUEPRINT - REST & PILATES DAYS', 'Rest Day')
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_DARK)
        self.cell(0,3.5,c('Carbs split evenly across 3 meals. No Karbolyn. No EAA.'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(1)

        self.callout(
            'REST DAY CARB RULE: Split 100g (Phase 1) evenly - ~33g per meal. '
            'No training window to cluster around. Kre-Alkalyn still taken daily.',
            TEAL, TEAL_LIGHT
        )

        self.meal_card(
            'WAKE UP - FASTED','Same fasted protocol every morning',
            ['500ml water immediately',
             'Apple Cider Vinegar - 1 tbsp in water'],
            ['Yohimbine - 5-20mg (fasted AM only)',
             'Vitamin D - 4,000 IU',
             'EGCG - 400mg',
             'HMB - 1g (first dose)'],
        )
        self.meal_card(
            'MEAL 1 - BREAKFAST','P: 59g | C: 33g | F: 24g | ~583 cal',
            ['4 egg whites + 1 whole egg',
             '100g chicken or turkey',
             '40g rolled oats (slow carb, keeps you full)',
             'Spinach or greens'],
            ['HMB - 1g',
             'Omega-3 Fish Oil - 1-2g EPA+DHA',
             'L-Carnitine L-Tartrate - 1g',
             'Kre-Alkalyn - 3g'],
        )
        self.meal_card(
            'MEAL 2 - MIDDAY','P: 59g | C: 33g | F: 24g | ~583 cal',
            ['180-200g tilapia, cod, or chicken',
             '3/4 cup white jasmine rice or 100g sweet potato',
             'Cooked vegetables',
             '1/2 avocado or olive oil drizzle'],
            ['HMB - 1g',
             'L-Carnitine L-Tartrate - 1g'],
        )
        self.meal_card(
            'MEAL 3 - DINNER','P: 60g | C: 34g | F: 23g | ~583 cal',
            ['180-200g salmon or turkey',
             '100g sweet potato or 3/4 cup jasmine rice',
             'Large salad with avocado'],
            ['Omega-3 Fish Oil - 1-2g EPA+DHA',
             'Noctrine - 1 serving before bed'],
        )

    def training_table(self, day_title, mobility, exs):
        lm, w = self.l_margin, self.epw
        needed = 6 + 4 + (len(exs) + sum(1 for e in exs if '\n' in e[1])) * 4.5 + 3
        if self.get_y() + needed > 278: self.add_page()

        self.set_fill_color(*DARK)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica','B',8)
        self.set_x(lm)
        self.cell(w, 6, c('  '+day_title), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font('Helvetica','I',6)
        self.set_text_color(*GREY_MID)
        self.set_x(lm)
        self.cell(w,3.5,c('Mobility: '+mobility),new_x=XPos.LMARGIN,new_y=YPos.NEXT)

        hdrs = ['#','EXERCISE','SETS x REPS','RPE','TEMPO','PROTOCOL']
        hws  = [6, 72, 23, 12, 14, 53]
        self.set_fill_color(205,205,205)
        self.set_text_color(*DARK)
        self.set_font('Helvetica','B',6)
        for h,hw in zip(hdrs,hws): self.cell(hw,4.5,c(h),fill=True)
        self.ln()

        for i,ex in enumerate(exs):
            bg = ROW_A if i%2==0 else ROW_B
            self.set_fill_color(*bg)
            num,name,sets,rpe,tempo,protocol = ex
            note = ''
            if '\n' in name:
                name,note = name.split('\n',1)
            self.set_font('Helvetica','B' if num!='*' else '',6)
            self.set_text_color(*DARK)
            self.set_x(lm)
            self.cell(hws[0],4,c(str(num)),fill=True)
            self.cell(hws[1],4,c(name),fill=True)
            self.set_font('Helvetica','',6)
            self.cell(hws[2],4,c(sets),fill=True)
            self.cell(hws[3],4,c(rpe),fill=True)
            self.cell(hws[4],4,c(tempo),fill=True)
            self.cell(hws[5],4,c(protocol),fill=True)
            self.ln()
            if note:
                self.set_x(lm)
                self.set_font('Helvetica','I',5.5)
                self.set_text_color(*GREY_MID)
                self.set_fill_color(*bg)
                self.cell(hws[0],3.2,'',fill=True)
                self.cell(sum(hws[1:]),3.2,c('  '+note),fill=True)
                self.ln()
        self.ln(3)

    def training_program(self):
        self.add_page()
        self.page_header('TRAINING PROGRAM','Day 1 & Day 2')
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        self.cell(0,3.5,c('Tempo = Eccentric/Pause/Concentric (sec)   |   RPE 8 = 2 reps left   |   RPE 9 = 1 rep left'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(1)
        self.callout('PROTOCOL RULES: Bands for warmup/activation ONLY - not on working sets. FST-7 = last exercise for target muscle, 30s rest between sets. Planks at end of session only - not inter-set.',TEAL,TEAL_LIGHT)

        day1=[
            ('1','Smith Machine Hip Thrust','4 x 8','8-9','4/2/1','Loaded Stretch'),
            ('2','Cable Pull-Through','4 x 10','8','4/1/1','Stretch Position'),
            ('3','Leg Press - Wide High Foot','4 x 10','8','3/1/2','Eccentric Overload'),
            ('4','Cable Kickback (per leg)','3 x 12','8','3/1/3','Slow Eccentric'),
            ('5','Lat Pulldown - Wide Grip','4 x 10','8','4/1/1','Loaded Stretch'),
            ('6','Seated Cable Row - Close','4 x 10','8','3/2/1','Stretch Position'),
            ('*','Plank Hold - end of session only','3 x 45s','-','-','Core Finisher'),
        ]
        self.training_table('DAY 1 - Glutes (Heavy) + Back','90/90 Hip Switches 2x8 each side',day1)

        day2=[
            ('1','Lying Leg Curl - Heavy','4 x 8','8-9','5/1/1','Eccentric Overload'),
            ('2','Seated Leg Curl','4 x 10','8','3/2/1','Loaded Stretch'),
            ('3','Cable Stiff-Leg Deadlift','3 x 12','8','4/1/1','Stretch Position'),
            ('4','Machine Chest Press','4 x 10','8','4/1/1','Eccentric Overload'),
            ('5','Cable Flye - Low to High','3 x 12','7-8','3/1/2','Loaded Stretch'),
            ('6','Cable Overhead Tricep Ext','3 x 12','8','4/1/1','Loaded Stretch'),
            ('*','Plank Hold - end of session only','3 x 45s','-','-','Core Finisher'),
        ]
        self.training_table('DAY 2 - Hamstrings + Chest + Triceps','T-Spine Rotations + Band Pull-Aparts 2x10',day2)

    def training_program_34(self):
        self.add_page()
        self.page_header('TRAINING PROGRAM','Day 3 & Day 4')
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        self.cell(0,3.5,c('Tempo = Eccentric/Pause/Concentric (sec)   |   RPE 8 = 2 reps left   |   RPE 9 = 1 rep left'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(2)

        day3=[
            ('1','45-Degree Hip Extension Machine\nReplaces hip thrust - different pattern, avoids Day 1 overlap','4 x 12','7-8','2/3/1','Intra-Set Stretch'),
            ('2','Hip Abduction - Leaned Fwd\nGlute medius - hip dip target. Do fresh, not fatigued','4 x 20','7','2/1/2','FST-7 Finisher'),
            ('3','Cable Sumo Squat','3 x 15','7','3/1/2','Constant Tension'),
            ('4','Cable Kickback - Slow Ecc','3 x 15','7','2/1/3','BFR'),
            ('5','Machine Shoulder Press','4 x 10','8','3/1/1','Eccentric Overload'),
            ('6','Cable Drag Curl','3 x 12','8','3/1/2','Loaded Stretch'),
            ('*','Plank Hold - end of session only','3 x 45s','-','-','Core Finisher'),
        ]
        self.training_table('DAY 3 - Glutes (Volume) + Shoulders + Biceps','Hip Flexor Stretch + Adductor Rockbacks 2x8',day3)

        day4=[
            ('1','Leg Extension - Slow','4 x 12','8','3/2/1','Loaded Stretch'),
            ('2','Leg Press - Narrow Low Foot','4 x 10','8-9','4/1/2','Eccentric Overload'),
            ('3','Hack Squat Machine','4 x 10','8','4/1/1','Lengthened Partials'),
            ('4','Lying Leg Curl - Heavy','4 x 8','9','5/1/1','Eccentric Overload'),
            ('5','Seated Leg Curl','3 x 12','8','3/2/1','Loaded Stretch'),
            ('6','Smith Machine Stiff-Leg DL','3 x 10','8','4/1/1','Stretch Position'),
            ('*','Plank Hold - end of session (longest hold)','3 x 60s','-','-','Core Finisher'),
        ]
        self.training_table('DAY 4 - Quads + Hamstrings','Hamstring Flossing + Hip Hinge Patterning 2x8',day4)

        lm, w = self.l_margin, self.epw
        self.set_font('Helvetica','B',7.5)
        self.set_text_color(*DARK)
        self.cell(0,4.5,'WEEKLY VOLUME',new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        self.multi_cell(w,3.5,c('Glutes 14 sets  |  Hamstrings 14 sets  |  Quads 12 sets  |  Back 8 sets  |  Chest 7 sets  |  Shoulders 4 sets  |  Biceps 3 sets  |  Triceps 3 sets  |  Core 12 sets'))
        self.ln(2)
        self.set_font('Helvetica','B',7.5)
        self.set_text_color(*DARK)
        self.cell(0,4.5,'KEY REMINDERS',new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        reminders=[
            'Add weight when RPE drops below target for 2 consecutive sessions',
            'BFR bands: 40-50% tightness, remove between exercises',
            'FST-7: 30s rest between the 7 sets',
            'Loaded Stretch: hold at stretch position on final set',
            'No momentum. No lockout. No shortcuts.',
        ]
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_DARK)
        for r in reminders:
            self.set_x(lm)
            self.cell(0,3.8,c('- '+r),new_x=XPos.LMARGIN,new_y=YPos.NEXT)

    def peak_week(self):
        self.add_page()
        self.page_header('JUNE 7-13 - MEXICO PREP','Peak Week Protocol')
        self.set_font('Helvetica','I',7)
        self.set_text_color(*GREY_MID)
        self.cell(0,3.5,c('This is the money window. Execute in order.'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(2)

        lm,w = self.l_margin, self.epw
        half = w/2 - 2

        y0 = self.get_y()
        self.set_xy(lm, y0)
        self.set_font('Helvetica','B',8)
        self.set_text_color(*PHASE_COLORS[3])
        self.cell(half,4.5,c('CARB RELOAD (JUN 7-11)'))
        rx = lm+half+4
        self.set_xy(rx, y0)
        self.set_text_color(*PHASE_COLORS[4])
        self.cell(half,4.5,c('PEAK DAY SEQUENCE (JUN 12-13)'))
        self.ln(5)

        lreload=[
            'Carbs jump to 250g - glycogen supercompensation',
            'Fat drops to 40g, protein stays at 178g',
            'White jasmine rice every meal - fastest glycogen uptake',
            'Add sweet potato 1-2 meals per day',
            'Banana allowed Phase 4-5 ONLY',
        ]
        lpeak=[
            'AM: Fasted BFR session',
            '45 min pre-event: Beet Root + Kre-Alkalyn pump stack',
            '30 min pre-event: rice cakes + honey (fast carbs)',
            'Water: 1.5-2L only all day',
            'Sodium: <500mg all day',
        ]
        y1 = self.get_y()
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_DARK)
        cy = y1
        for item in lreload:
            self.set_xy(lm, cy)
            self.multi_cell(half, 3.5, c('- '+item))
            cy = self.get_y()
        left_end = cy

        cy = y1
        for item in lpeak:
            self.set_xy(rx, cy)
            self.multi_cell(half, 3.5, c('- '+item))
            cy = self.get_y()

        self.set_y(max(left_end, cy)+2)

        self.set_font('Helvetica','B',8)
        self.set_text_color(*DARK)
        self.cell(0,4.5,'WATER PROTOCOL',new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_font('Helvetica','',7)
        self.set_text_color(*GREY_DARK)
        for wi in ['Now - Jun 11: 3.5-4L / day','Jun 12-13: taper to 1.5-2L','Sodium: moderate now, drop to <500mg last 2 days']:
            self.set_x(lm)
            self.cell(0,3.5,c('- '+wi),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(2)

        self.callout('WATER OUT ACTIVATES JUNE 7: 2-3 caps/day from June 7 onwards. Do NOT use before - daily use blunts the diuretic effect and flattens muscles during training.', PHASE_COLORS[3], (245,235,250))
        self.callout('FINAL DEPLETION (JUN 9-11): Carbs drop to 60g if needed. Sodium taper begins. Glycogen empties - this is intentional. You will feel flat. Trust the reload. It works.', PHASE_COLORS[2], (255,248,235))
        self.ln(1)

        self.set_font('Helvetica','B',10)
        self.set_text_color(*DARK)
        self.cell(0,5.5,'Full Supplement Cheatsheet',new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.set_font('Helvetica','',6.5)
        self.set_text_color(*GREY_MID)
        self.cell(0,3.5,c('Everything in one place - what it is, when to take it'),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
        self.ln(1)

        supps=[
            ('Yohimbine','5-20mg (titrate)','Fasted AM only','Fat mobilization - only works fasted'),
            ('Vitamin D','4,000 IU','With Meal 1','Hormonal health, muscle function'),
            ('EGCG','400mg','With Meal 1','Thermogenic, antioxidant'),
            ('HMB','3g/day (1g x 3)','Meals 1, 2, 3','Anti-catabolic - protects muscle on deficit'),
            ('Omega-3 Fish Oil','3g EPA+DHA','Meals 1 + 3','Inflammation, recovery, cell health'),
            ('L-Carnitine L-Tartrate','2g/day (1g x 2)','Meals 1 + 2','Androgen receptor upregulation in muscle'),
            ('Collagen Peptides','15g','30-45 min pre-workout','Fascia remodeling - 3D dense look. NOT protein.'),
            ('Beet Root Powder','500mg-1g','Pre-workout','Nitric oxide, pump'),
            ('Karbolyn','1/4 serving (~12-13g)','Pre-workout only','Fast carbs for training. Counts toward daily total.'),
            ('Kre-Alkalyn','3g','Pre-workout or Meal 1','Buffered creatine - strength, no water bloat'),
            ('Performance EAA','10-15g','Intra-workout (training days)','MPS during session, anti-catabolic'),
            ('Apple Cider Vinegar','1 tbsp in water','Fasted AM + before carb meals','Insulin sensitivity, water balance'),
            ('Noctrine','1 serving','Before bed','Recovery, sleep quality'),
            ('Water Out [!]','2-3 caps','Jun 7-13 ONLY','Diuretic - peak week only. Daily use kills pump.'),
        ]
        shdrs=['SUPPLEMENT','DOSE','WHEN','PURPOSE']
        sws=[36,26,34,84]
        self.set_fill_color(*DARK)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica','B',6)
        for sh,sw in zip(shdrs,sws): self.cell(sw,5,c(sh),fill=True)
        self.ln()
        for i,(name,dose,when,purpose) in enumerate(supps):
            bg = ROW_A if i%2==0 else ROW_B
            self.set_fill_color(*bg)
            bold = (name=='Water Out [!]')
            self.set_font('Helvetica','B' if bold else '',6)
            self.set_text_color((170,30,30) if bold else GREY_DARK)
            for v,sw in zip([name,dose,when,purpose],sws):
                self.cell(sw,4,c(v),fill=True)
            self.ln()

def main():
    pdf = PDF()
    pdf.set_margins(12,12,12)
    pdf.set_auto_page_break(True, margin=12)
    pdf.set_title('Blair Grimes - T1 Campaign')
    pdf.set_author('Tanzim Ozer')

    pdf.cover()
    pdf.phase_overview()
    pdf.training_day()
    pdf.rest_day()
    pdf.training_program()
    pdf.training_program_34()
    pdf.peak_week()

    pdf.output(OUTPUT)
    print(f'Done: {OUTPUT}')

main()
