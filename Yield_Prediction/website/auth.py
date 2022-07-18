from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import db
from .models import User
from .views import views
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from .form_contact import ContactForm, PredForm
from http.client import responses
import requests
import random

def getList(dict):
    return dict.keys()

def conditional_change(prediction, old_score, new_score):
    if new_score > old_score:
        return True
    else:
        return False

def prediction_change(prediction, old_value, new_value):
    if (new_value - old_value) == float(prediction):
        return True
    else:
        return False

auth = Blueprint("auth", __name__)
mail = Mail()

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        print(email)
        print(password)

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                print("Logged in!")
                return redirect(url_for('auth.success'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

def send_message(message):
    print(message.get('name'))

    msg = Message(message.get('subject'), sender = message.get('email'),
            recipients = ['newpythontestapp@gmail.com'],
            body= message.get('message')
    )
    mail.send(msg)

@auth.route("/sign-up", methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get("email")
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        email_exists = User.query.filter_by(email=email).first()
        username_exists = User.query.filter_by(username=username).first()

        if email_exists:
            flash('Email is already in use.', category='error')
        elif username_exists:
            flash('Username is already in use.', category='error')
        elif password1 != password2:
            flash('Password don\'t match!', category='error')
        elif len(username) < 2:
            flash('Username is too short.', category='error')
        elif len(password1) < 6:
            flash('Password is too short.', category='error')
        elif len(email) < 4:
            flash("Email is invalid.", category='error')
        else:
            new_user = User(email=email, username=username, password=generate_password_hash(
                password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User created!')
            return redirect(url_for('auth.login'))

    return render_template("signup.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("views.home"))

@auth.route("/")
def index():
    return render_template("index.html")

@auth.route('/success')
def success():
    headers = {
        'X-RapidAPI-Key': "d0c522027amsh51fdd1eb86fd81fp15b046jsn5bc411c88dcc",
        'X-RapidAPI-Host': "cricbuzz-cricket.p.rapidapi.com"
        }

    #Link to scrape data about ongoing matches

    url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
    response = requests.request("GET", url, headers=headers)
    information = response.json()

    game_types = [0]

    for game_type in game_types:
        data = information['typeMatches'][game_type]['seriesMatches'] 

        series_list = [] #Different ongoing Series
        match_details = [] #Different ongoing Matches

        for series_current in data:

            #Some Necessary Data Formatting and Series Finding
            try:
                curr_series_data = series_current['seriesAdWrapper']
            except:
                pass

            try:
                series_list.append([curr_series_data['seriesName'], curr_series_data['seriesId']])
                curr_series_data = curr_series_data['matches']
            except:
                pass

            if len(curr_series_data) == 0:
                curr_series_data['seriesAdWrapper'][0]['matchInfo']['matchInfo']
            
            for matchSet in curr_series_data:

                print(matchSet['matchInfo']['matchFormat'])

                if (matchSet['matchInfo']['matchFormat'] == 'TEST') and (matchSet['matchInfo']['state'] != 'Complete'):

                    #Getting current Match ID

                    current_match = matchSet['matchInfo']['matchId']
                    match_details.append([matchSet['matchInfo']['matchId'], matchSet['matchInfo']['state']])
                    
                    team_1_full = [] #Batmens-Bowler Data and other Meta for Team 1
                    team_2_full = [] #Batmens-Bowler Data and other Meta for Team 2

                    #Batsmen Bowler Data for a Single Game

                    batsmen_team_one = []
                    batsmen_team_two = []
                    bowlers_team_one = []
                    bowlers_team_two = []

                    #Meta Data for Each Team - Total Runs, Name, etc

                    team_1_full.append([matchSet['matchInfo']['team1']['teamName'], matchSet['matchScore']['team1Score']])
                    team_2_full.append([matchSet['matchInfo']['team2']['teamName'], matchSet['matchScore']['team2Score']])

                    url = "https://cricbuzz-cricket.p.rapidapi.com/mcenter/v1/" + str(current_match) + "/scard"

                    responsetest_ = requests.request("GET", url, headers=headers)

                    information_match = responsetest_.json()

                    cycle_number  = 0

                    #Batsmen Bowler Data for a Game

                    for team_number_ID in information_match['scoreCard']:
                        for data_point in team_number_ID['batTeamDetails']['batsmenData']:
                            curr_batsmen = team_number_ID['batTeamDetails']['batsmenData'][data_point]
                            if cycle_number == 0:
                                batsmen_team_one.append([curr_batsmen['batName'], curr_batsmen['isCaptain'], curr_batsmen['isKeeper'], curr_batsmen['runs'],curr_batsmen['balls'], curr_batsmen['strikeRate'], curr_batsmen['boundaries'],curr_batsmen['sixers'], curr_batsmen['wicketCode'], curr_batsmen['bowlerId'], curr_batsmen['fielderId1'], curr_batsmen['outDesc']])
                            else:
                                batsmen_team_two.append([curr_batsmen['batName'], curr_batsmen['isCaptain'], curr_batsmen['isKeeper'], curr_batsmen['runs'],curr_batsmen['balls'], curr_batsmen['strikeRate'], curr_batsmen['boundaries'],curr_batsmen['sixers'], curr_batsmen['wicketCode'], curr_batsmen['bowlerId'], curr_batsmen['fielderId1'], curr_batsmen['outDesc']])

                        for data_point in team_number_ID['bowlTeamDetails']['bowlersData']:
                            curr_bowler = team_number_ID['bowlTeamDetails']['bowlersData'][data_point]

                            if cycle_number == 0:
                                bowlers_team_two.append([curr_bowler['bowlName'], curr_bowler['isCaptain'], curr_bowler['isKeeper'], curr_bowler['overs'], curr_bowler['maidens'], curr_bowler['runs'], curr_bowler['wickets'], curr_bowler['economy'], curr_bowler['no_balls'], curr_bowler['wides']])
                            else:
                                bowlers_team_one.append([curr_bowler['bowlName'], curr_bowler['isCaptain'], curr_bowler['isKeeper'], curr_bowler['overs'], curr_bowler['maidens'], curr_bowler['runs'], curr_bowler['wickets'], curr_bowler['economy'], curr_bowler['no_balls'], curr_bowler['wides']])

                        cycle_number += 1

                    team_1_full.append(batsmen_team_one)
                    team_2_full.append(batsmen_team_two)
                    team_1_full.append(bowlers_team_one)
                    team_2_full.append(bowlers_team_two)
                else:
                    pass

    team_currently_batting = team_1_full
    team_currently_bowling = team_2_full

    if (len(team_2_full[1]) != 0):
        team_currently_batting = team_2_full
        team_currently_bowling = team_1_full

    team_batting = team_currently_batting[0][0]
    global batsmen_1 
    global batsmen_2 
    global batsmen_1_runs
    global batsmen_2_runs
    global batsmen_1_balls
    global batsmen_1_sr
    global batsmen_2_sr
    global batsmen_2_balls
    global batsmen_1_sixes
    global batsmen_2_sixes
    global batsmen_1_fours
    global batsmen_2_fours

    team_bowling = team_currently_bowling[0][0]
    global bowler_name
    global bowler_overs
    global bowler_runs
    global bowler_wickets
    global bowler_maidens
    global bowler_econ
    global bowler_no_ball
    global bowler_wides

    count_batter = 0 

    team_batting_stats = team_currently_batting[0][1]['inngs1']

    team_batting_runs = team_batting_stats['runs']
    team_batting_overs = team_batting_stats['overs']

    try:
        team_batting_wickets = team_batting_stats['wickets']
    except:
        team_batting_wickets = 0 

    batsmen_1_ = False
    batsmen_2_ = False

    for batter in team_currently_batting[1]:

        if count_batter == 2:
            break

        if (batter[-1] == 'batting') and (batsmen_1_ == False) and (count_batter == 0):
            batsmen_1 = str(batter[0])
            batsmen_1_runs = int(batter[3])
            batsmen_1_balls = int(batter[4])
            batsmen_1_sr = float(batter[5])
            batsmen_1_fours = int(batter[6])
            batsmen_1_sixes = int(batter[7])
            count_batter += 1
            batsmen_1_ = True

        elif (batter[-1] == 'batting') and (batsmen_2_ == False) and (count_batter == 1):
            batsmen_2 = str(batter[0])
            batsmen_2_runs = int(batter[3])
            batsmen_2_balls = int(batter[4])
            batsmen_2_sr = float(batter[5])
            batsmen_2_fours = int(batter[6])
            batsmen_2_sixes = int(batter[7])
            count_batter += 1
            batsmen_1_ = True

    for bowler in team_currently_bowling[2]:

        if (float(bowler[3]) % 1) != 0:
            bowler_name = str(bowler[0])
            bowler_overs = float(bowler[3])
            bowler_runs = int(bowler[5])
            bowler_wickets = int(bowler[6])
            bowler_maidens = int(bowler[4])
            bowler_econ = float(bowler[7])
            bowler_no_ball = int(bowler[8])
            bowler_wides = int(bowler[9])
            break

    if (43 < batsmen_1_runs < 47):
        batsmen = batsmen_1
    elif (43 < batsmen_2_runs < 47):
        batsmen = batsmen_2
    else:
        batsmen = 'None'

    wicket_number = team_batting_wickets + 1
    target_runs = int(team_batting_runs) + 60
    off_balls = bowler_no_ball + bowler_wides

    questions_general = ['How will the strike rate of {} of {} change in the next over'.format(batsmen_1, batsmen_1_sr),'How many fours will batsman {} hit in the next over?'.format(batsmen_2), 'How many sixes will batsman {} hit in the next over?'.format(batsmen_1), 'How many wides will bowler {} bowl in his next over?'.format(bowler), 'Will {} take a wicket in the over'.format(bowler), 'Currently bowled {} wides, will {} bowl another one this over?'.format(off_balls, bowler), 'Currently bowled {} maidens, will {} bowl another one this over?'.format(bowler_maidens, bowler), 'How will the economy of {} of {} change in the next over'.format(bowler, bowler_econ)]

    questions_general_overs = ['How many runs will team {} make in the next 5 overs?'.format(team_batting), 'How many fours will batsmen {} hit in the next 5 overs'.format(batsmen_2), 'How many wickets will {} take in the next five overs'.format(bowler_name), 'Will team {} lose its {} wicket in the next five overs'.format(team_batting, wicket_number), 'Will team {} cross {} in the next 5 overs'.format(team_batting, target_runs)]

    special_questions = ['Will team {} cross 50 runs in the next over?'.format(team_batting), 'Will team {} cross 100 runs in the next over?'.format(team_batting), 'Will {} score a half centuary in the next over?'.format(batsmen), 'Will {} score a centuary in the next over?'.format(batsmen), 'How many runs will the next partnership between batsman {} and {} be?'.format(batsmen_1, batsmen_2)]

    if team_batting_overs < 15:
        question = [*questions_general, *questions_general_overs]
    else:
        question = questions_general

    question_number = random.randint(0, len(question) - 1)
    question = question[question_number]

    special_question = 0

    global match_curr_id

    match_curr_id = match_details[0][0]

    if 40 < team_batting_runs < 45:
        question = special_questions[0]
        special_question = 1
    elif 90 < team_batting_runs < 95:
        question = special_questions[1]
        special_question = 2
    elif (43 < batsmen_1_runs < 47) or (43 < batsmen_2_runs < 47):
        question = special_questions[2]
        special_question = 3
    elif (93 < batsmen_1_runs < 96) or (93 < batsmen_2_runs < 96):
        question = special_questions[3]
        special_question = 4

    print(question)
    print(match_curr_id)

    return render_template('success.html')

@auth.route('/scorecard')
def scorecard():
    link_current_match = "https://www.cricbuzz.com/live-cricket-scores/" + str(match_curr_id)

    return render_template('scorecard.html', batsmen_1 = batsmen_1,
    batsmen_2 = batsmen_2,
    batsmen_1_runs = batsmen_1_runs,
    batsmen_2_runs = batsmen_2_runs,
    batsmen_1_balls = batsmen_1_balls,
    batsmen_1_sr = batsmen_1_sr,
    batsmen_2_sr = batsmen_2_sr,
    batsmen_2_balls = batsmen_2_balls,
    batsmen_1_sixes = batsmen_1_sixes,
    batsmen_2_sixes = batsmen_2_sixes,
    batsmen_1_fours = batsmen_1_fours,
    batsmen_2_fours = batsmen_2_fours,
    link = link_current_match)
    
@auth.route("/contact", methods=['POST', 'GET'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        send_message(request.form)
        return redirect('/')

    return render_template("contact.html", form=form)
