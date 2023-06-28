# nhl_gs.py
#
# NHL Grand Salami (scoreboard and game stats)
#
import platform
import sys
import os
import json
import argparse
import datetime
import requests

USE_FILE = False

# constants
ARG_LIVE = 'live'
ARG_START_DATE = 'start_date'
ARG_END_DATE = 'end_date'


def is_game_postponed(game):
    return game['status']['detailedState'] == "Postponed"


def num_games_postponed(games):
    return len([game for game in games if is_game_postponed(game)])


# Calculate seconds remaining in the regulation game.
# Inputs: period   = current period (1, 2, or 3)
#         time_rem = string of time remaining in period
#                   example: "14:23"
# Returns: Seconds remaining in regulation game (integer).
#          If period is not 1,2,or 3, return 0.
#          If timeRem is not in time format, then return 0.
def calc_seconds_rem(period, time_rem):
    period_time_rem = {1: 40*60, 2: 20*60, 3: 0*60}

    if period not in period_time_rem:
        return 0

    seconds_rem_in_period = 0
    if ":" in time_rem:
        minute = int(time_rem.split(":")[0])
        second = int(time_rem.split(":")[1])
        seconds_rem_in_period = (60 * minute) + second

    return period_time_rem[period] + seconds_rem_in_period


# The screen clear function
def screen_clear():
    # Windows platform.system() is 'Windows'
    if platform.system() == "Windows":
        _ = os.system("cls")
    else:
        # osx and Linux
        _ = os.system("clear")


# Get program arguments
#
# usage: nhl_gs.py [-h] [-l] [start_date] [end_date]
#
# Inputs:
#   None
# Returns:
#   dict containing input arguments as keys:
#     live, start_date, end_date
def get_arguments():

    # Helper function to parse date arguments
    # Inputs:
    #   date_arg: string of argument to parse
    # Returns:
    #   date_arg if in correct format YYYY-MM-DD
    #   argparse.ArgumentTypeError() if not
    def date_arg_parser(date_arg):
        try:
            date = datetime.date.fromisoformat(date_arg)
            return date_arg
        except:
            msg = f'not a valid date: "{date_arg}" expecting date format YYYY-MM-DD'
            raise argparse.ArgumentTypeError(msg)


    app_description = "Fetch NHL scores and stats. View NHL Grand Salami progress."
    app_epilog = ("Not specifying the end_date will only fetch data for the start_date.\n"
                  "When using the -l (live) flag, the app will not exit until user stops the app with CTRL+C.\n"
                  "Otherwise the app will display the data for the dates specified and exit.\n"
                  "\n"
                  "Examples:\n"
                  "\n"
                  "Fetch NHL scores and data from Feb 19, 2023 and exit:\n"
                  "%(prog)s 2023-02-19\n"
                  "\n"
                  "Fetch NHL scores and data from Feb 19, 2023 through Feb 23, 2023 and exit:\n"
                  "%(prog)s 2023-02-19 2023-02-23\n"
                  "\n"
                  "Fetch today's NHL scores and data, and update live:\n"
                  "%(prog)s -l\n")


    argParser = argparse.ArgumentParser(description=app_description,
                                        epilog=app_epilog,
                                        formatter_class=argparse.RawTextHelpFormatter)

    argParser.add_argument("-l",
                           "--" + ARG_LIVE,
                           action="store_true",
                           help="Live update the stats")
    argParser.add_argument(ARG_START_DATE,
                           nargs="?",
                           type=date_arg_parser,
                           help="(optional) Start date in YYYY-MM-DD format")
    argParser.add_argument(ARG_END_DATE,
                           nargs="?",
                           type=date_arg_parser,
                           help="(optional) End date in YYYY-MM-DD format")

    args = argParser.parse_args()

    # Convert args "namespace" to normal dict.
    args_dict = vars(args)

    # If end_date is empty, then end_date = start_date
    if args_dict[ARG_END_DATE] == None and args_dict[ARG_START_DATE] != None:
        args_dict[ARG_END_DATE] = args_dict[ARG_START_DATE]

    return args_dict


def run_nhl_gs_app():

    # Get arguments
    args_dict = get_arguments()

    screen_clear()

    nhl_data = {}

    if USE_FILE:
        with open('samples/another_sat_night_done.txt','r') as f:
            nhl_data = json.load(f)
    else:
        # Main NHL API URL
        BASE_URL = "https://statsapi.web.nhl.com/api/v1/schedule"

        # NHL API keys/values. Keep the order in the dictionary.
        payload = {}
        if args_dict[ARG_START_DATE] != None:
            payload['startDate'] = args_dict[ARG_START_DATE]
            payload['endDate'] = args_dict[ARG_END_DATE]

        payload['hydrate'] = "linescore,scoringplays,game(seriesSummary)"
        payload['site'] = 'en_nhl'

        CUSTOM_HEADERS = {'Host': 'statsapi.web.nhl.com',
                          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
                          'Accept': '*/*',
                          'Accept-Language': 'en-US,en;q=0.5',
                          'Accept-Encoding': 'gzip, deflate, br',
                          'Origin': 'https://www.nhl.com',
                          'Connection': 'keep-alive',
                          'Referer': 'https://www.nhl.com',
                          'Sec-Fetch-Dest': 'empty',
                          'Sec-Fetch-Mode': 'cors',
                          'Sec-Fetch-Site': 'same-site'}

        sess = requests.Session()

        try:
            resp = sess.get(BASE_URL, headers=CUSTOM_HEADERS, params=payload)
        except (requests.RequestException,
                requests.ConnectionError) as e:
            print(f"requests module exception: {e}")
            sys.exit()
        except KeyboardInterrupt:
            print("******** keyboard interrupted!!!! *******")
            sys.exit()
        except Exception as e:
            print(e)
            sys.exit()

        if "age" in resp.headers:
            print(f"age = {resp.headers['age']}")

        try:
            nhl_data = resp.json()
        except Exception as e:
            print(f"Cannot parse JSON, {e}")
            sys.exit()

    if "metaData" in nhl_data and "timeStamp" in nhl_data['metaData']:
        print(f"timeStamp = {nhl_data['metaData']['timeStamp']}")

    dates = nhl_data['dates']
    if len(dates) == 0:
        print("No dates!")
    else:
        for date in dates:
            print(f"date = {date['date']}")
            games = date['games']
            numPostponed = num_games_postponed(games)
            numGames = len(games)
            print(f"Total games today = {numGames} (playing = {numGames-numPostponed}, postponed = {numPostponed})")

            totalAwayGoals = 0
            totalHomeGoals = 0
            totalGoals = 0
            totalMinGoals = 0
            totalSecondsRem = 0

            for game in games:
                print("")
                status = game['status']
                print(f"Status = {status['abstractGameState']} - {status['detailedState']}")
                postponed = is_game_postponed(game)

                linescore = game['linescore']
                teams = linescore['teams']

                awayTeamName = teams['away']['team']['name']
                homeTeamName = teams['home']['team']['name']

                if postponed:
                    print(f"    {awayTeamName} at {homeTeamName}")
                    continue

                awayGoals = teams['away']['goals']
                totalAwayGoals += awayGoals

                homeGoals = teams['home']['goals']
                totalHomeGoals += homeGoals

                gameGoals = awayGoals + homeGoals
                gameMinGoals = gameGoals
                if awayGoals == homeGoals:
                    gameMinGoals += 1
                totalMinGoals += gameMinGoals

                print(f"    {awayTeamName} {awayGoals}")
                print(f"    {homeTeamName} {homeGoals}")

                period = linescore['currentPeriod']
                timeRem = 0
                secondsRem = 0
                if period > 0:
                    timeRem = linescore['currentPeriodTimeRemaining']
                    secondsRem = calc_seconds_rem(period, timeRem)
                elif period == 0 and (status['detailedState'] == "Scheduled" or status['detailedState'] == "Pre-Game"):
                    secondsRem = 3600
                    timeRem = "N/A"
                totalSecondsRem += secondsRem
                print(f"Period = {period}  Time rem = {timeRem}  Seconds rem = {secondsRem}  "
                    f"% left = {(secondsRem * 100.0) / 3600.0:.2f}%  "
                    f"Total goals = {gameGoals}  Min goals = {gameMinGoals}")

                scoringPlays = game['scoringPlays']
                for scoringPlay in scoringPlays:
                    print(f"    {scoringPlay['result']['description']}")

            totalGoals = totalAwayGoals + totalHomeGoals
            print("")
            print(f"Away Goals = {totalAwayGoals}, Home Goals = {totalHomeGoals}, TOTAL = {totalGoals}, "
                f"Total MIN goals = {totalMinGoals}, Total seconds rem = {totalSecondsRem}, "
                f"Total games rem = {totalSecondsRem / 3600.0:.3f}")

if __name__ == "__main__":
    run_nhl_gs_app()
