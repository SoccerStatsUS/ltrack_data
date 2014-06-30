# Process Ltrack data files.

# All United States Ltrack data received from Scott Leach.

import datetime
import os


def format_name(s):
    # Reverse a name from Donovan, Landon to Landon Donovan.
    fields = [e.strip() for e in s.split(",", 1)]

    if len(fields) == 1:
        ns = fields[0]
    elif len(fields) == 2:
        ns = "%s %s" % (fields[1], fields[0])
    return ns




# Grouped.

def make_team_to_competition_dict():
    """
    Create a dict mapping a team and season to a competition based on standings
    """

    from donelli.parse.standings import process_standings_file
    from smid.build.load import USD1_DIR, US_MINOR_DIR
    from smid.alias.teams import get_team


    standings = [
        ('data/standings/mls', USD1_DIR),
        ('standings/d2/apsl', US_MINOR_DIR),
        ('standings/d2/usl0', US_MINOR_DIR),
        ('standings/d2/premier', US_MINOR_DIR),
        ('standings/d2/usisl', US_MINOR_DIR),
        ('standings/d2/12', US_MINOR_DIR),
        ('standings/d2/nasl2', US_MINOR_DIR),
        ('standings/d2/ussf2', US_MINOR_DIR),

        ('standings/d3/pro', US_MINOR_DIR),
        ('standings/d3/usl_pro', US_MINOR_DIR),
        ('standings/d3/select', US_MINOR_DIR),

        ('standings/d4/pdl', US_MINOR_DIR),
        ('standings/d4/pdl_2012', US_MINOR_DIR),
        ('standings/d4/pdl_2013', US_MINOR_DIR),


        ]

    l = []
    for path, dir in standings:
        p = os.path.join(dir, path)
        l.extend(process_standings_file(p))

    d = {}
    for e in l:
        key = (get_team(e['team']), e['season'])
        if key not in d:
            d[key] = [e['competition']]

    return d



competition_map = make_team_to_competition_dict()


# Only used by ltrack.
def determine_competition(comp, team, season):
    from smid.alias.teams import get_team

    

    # Pull this out.
    abbreviations = {
        'CCC': 'CONCACAF Champions\' Cup',
        'CCL': 'CONCACAF Champions League',

        'CCup': 'Canadian Championship',
        'CanC': 'Canadian Championship',

        'SL': 'North American SuperLiga',
        'CFU': 'CFU Club Championship',

        'IAC': 'Interamerican Cup',
        'GC': 'CONCACAF Giants Cup',
        'FDLY': 'Friendly',
        'MerC': 'Merconorte Cup',
        'CCWC': 'CONCACAF Cup Winners Cup',
        'LMC': 'La Manga Cup',

        'RC': 'Recopa CONCACAF',
        'PCK': 'Peace Cup',
        'CQ': 'Caribbean Qualification',
        #'CQ': 'Concacaf Champions\' Cup',
        'PPC': 'Pan-Pacific Championship',
        'INDC': 'Independence Cup',
        'USOC': 'US Open Cup',
        'ASG': 'Friendly',
        'PDL': 'USL Premier Developmental League',
        'DC': 'Dallas Cup',

        'LT': 'Friendly', # Lisbon Tournament
        'WC': 'FIFA World Cup',

        'MkC': 'Friendly', # Milk Cup
        'Milk': 'Friendly', # Milk Cup

        'GCup': 'Gold Cup',

        'VDMT': 'Friendly', #'Val-de-Marne Tournament',

        'APT': 'Friendly', # Asia-Pacific Tour
        'NIF': 'Friendly', #'Nike International',

        'NLG': 'Friendly', # Non-League
        'SCC': 'Friendly', #'Sister Cities Cup'

        'MMF': 'FIFA U-17 World Cup', # not sure... 'Mondial Minimes Fra'
        'WC17': 'FIFA U-17 World Cup', 

        'ResL': 'MLS Reserve League',
        'CU17': 'FIFA U-17 World Cup',
        'CU20': 'FIFA U-20 World Cup',

        'WFC': 'Friendly', # World Football Challenge',
        'RGP': 'Friendly', # Rio Grande Plate
        }

    if comp in abbreviations:
        return abbreviations[comp]

    # ILG -> Interleague

    elif comp in ('LGE', 'ILG', 'PLO', 'PLOF'):  
        try:
            competitions = competition_map[(get_team(team), season)]
        except:
            competitions = []
            #import pdb; pdb.set_trace()

        if len(competitions) == 0:
            return comp
        elif len(competitions) > 1:
            import pdb; pdb.set_trace()
        else:
            return competitions[0]

    else:
        import pdb; pdb.set_trace()
        return comp


    


def process_lineups_file(p, determine_competition):
    text = open(p).read().replace('\r', '').split('\n')
    header = text[0]
    data = text[1:]

    l = []

    order = 1
    previous_team = None
    
    for line in data:
        s = line.strip()
        if s:
            fields = line.split('\t')

            comp, date_string, home_team, away_team, team, name, rating, on, off, yc1, yc2, rc, yc, time, substituted, time_on, time_off, yc_time = fields

            month, day, year = [int(e) for e in date_string.split("/")]
            d = datetime.datetime(year, month, day)
            season = str(d.year)

            competition = determine_competition(comp, team, season)

            n = format_name(name)

            if previous_team == team:
                order += 1
            else:
                order = 1
                
            on = int(on)
            off = int(off)

            unused = (on == 0 and off == 0)

            l.append({
                    'name': n,
                    'on': int(on),
                    'off': int(off),
                    'team': team,
                    'date': d,
                    'season': season,
                    'competition': competition,
                    'order': order,
                    'unused': unused
                    })

    return l
    #return [e for e in l if e['competition'] != 'Major League Soccer']


def process_games_file(p, determine_competition):
    """
    Process a games file.
    """
    text = open(p).read().replace('\r', '').split('\n')
    header = text[0]
    data = text[1:]

    l = []
    
    for line in data:
        s = line.strip()
        if s:
            fields = line.split('\t')
            
            # 14 fields always
            
            if len(fields) == 9:
                date_string, home_team, away_team, home_score, away_score, attendance, competition_type, comp, comments = fields
            elif len(fields) == 14:
                date_string, home_team, away_team, home_score, away_score, attendance, competition_type, comp, comments, referee, awarded, _, _, _ = fields
            else:
                import pdb; pdb.set_trace()

            month, day, year = [int(e) for e in date_string.split("/")]
            d = datetime.datetime(year, month, day)

            season = str(d.year)

            competition = determine_competition(comp, home_team, season)

            try:
                if attendance.strip():
                    attendance = int(attendance.replace(',', ''))
                else:
                    attendance = None
            except:
                import pdb; pdb.set_trace()

            if attendance in (0, 1, 10):
                attendance = None
                

            l.append({
                    'team1': home_team,
                    'team2': away_team,
                    'team1_score': int(home_score),
                    'team2_score': int(away_score),
                    'home_team': home_team,
                    'competition': competition,
                    'season': season,
                    'date': d,
                    'attendance': attendance,
                    'referee': format_name(referee),
                    'sources': ['Scott Leach'],
                    })

    return l
    return [e for e in l if e['competition'] != 'Major League Soccer']


def process_goals_file(p, determine_competition):
    """
    Process a goal file.
    """

    text = open(p).read().replace('\r', '').split('\n')
    header = text[0]
    data = text[1:]

    l = []

    for line in data:
        s = line.strip()
        if s:
            fields = line.split('\t')

            # 11 fields always
            player, team, _, _, date_string, minute, _, comp, assist1, assist2, _ = fields

            month, day, year = [int(e) for e in date_string.split("/")]

            d = datetime.datetime(year, month, day)
            season = str(d.year)

            if assist1 and assist2:
                assists = [format_name(assist1), format_name(assist2)]
            elif assist1:
                assists = [format_name(assist1)]
            else:
                assists = []

            competition = determine_competition(comp, team, season)

            l.append({
                    'goal': format_name(player),
                    'minute': int(minute),
                    'team': team,
                    'type': 'normal',
                    'date': d,
                    'assists': assists,
                    'season': season,
                    'competition': competition,
                    })

    return l
    return [e for e in l if e['competition'] != 'Major League Soccer']


def process_goals(root):
    """
    Process all goal data from Leach.
    """
    l = []
    directory = os.path.join(root, 'goals')
    for fn in os.listdir(directory):
        p = os.path.join(directory, fn)
        data = process_goals_file(p, determine_competition)
        l.extend(data)
    return l
        

def process_games(root):
    """
    Process all game data from Leach.
    """
    l = []
    directory = os.path.join(root, 'games')
    for fn in [e for e in os.listdir(directory) if not e.endswith('~')]:
        p = os.path.join(directory, fn)
        data = process_games_file(p, determine_competition)
        l.extend(data)
    return l
     

def process_lineups(root):
    """
    Process all game data from Leach.
    """
    l = []
    directory = os.path.join(root, 'squads')
    for fn in os.listdir(directory):
        p = os.path.join(directory, fn)
        data = process_lineups_file(p, determine_competition)
        l.extend(data)
    return l
