
# The screen clear function
def screen_clear():
    import platform
    import os
    # Windows platform.system() is 'Windows'
    if platform.system() == "Windows":
        _ = os.system("cls")
    else:
        # osx and Linux
        _ = os.system("clear")


def is_game_postponed(game):
    return game['status']['detailedState'] == "Postponed"


def num_games_postponed(games):
    return len([game for game in games if is_game_postponed(game)])


# Calculate seconds remaining in the regulation game.
# Inputs: period  = current period (1, 2, or 3)
#         timeRem = string of time remaining in period
#                   example: "14:23"
# Returns: Seconds remaining in regulation game.
#          If period is not 1,2,or 3, return 0.
#          If timeRem is not in time format, then return 0.
def calc_seconds_rem(period, timeRem):
    period_time_rem = {1: 40*60, 2: 20*60, 3: 0*60}

    if period not in period_time_rem:
        return 0

    seconds_rem_in_period = 0
    if ":" in timeRem:
        minute = int(timeRem.split(":")[0])
        second = int(timeRem.split(":")[1])
        seconds_rem_in_period = (60 * minute) + second

    seconds_rem_in_game = period_time_rem[period] + seconds_rem_in_period
    return seconds_rem_in_game


if __name__ == "__main__":
    screen_clear()

    USE_FILE = False
	
    nhldata = {}

    if USE_FILE:
        with open('AllStarGame_Feb042023.txt','r') as f:
            import json
            nhldata = json.load(f)
    else:
        import requests

        base_url = "https://statsapi.web.nhl.com/api/v1/schedule?hydrate=linescore,scoringplays"

        sess = requests.Session()

        try:
            resp = sess.get(base_url)
        except (requests.RequestException,
                requests.ConnectionError) as e:
            print("requests module exception: {}".format(e))
            quit()
        except KeyboardInterrupt:
            print("******** keyboard interrupted!!!! *******")
            quit()
        except Exception as e:
            print(e)
            quit()

        if "age" in resp.headers:
            print(f"age = {resp.headers['age']}")

        try:
            nhldata = resp.json()
        except Exception as e:
            print("Cannot parse JSON, ", e)
            quit()

    dates = nhldata['dates']
    if len(dates) == 0:
        print("No dates!")
    else:
        for date in dates:
            print("date = ", date['date'])
            games = date['games']
            numPostponed = num_games_postponed(games)
            numGames = len(games)
            print("Total games today = {} (playing = {}, postponed = {})"
                .format(numGames,
                        numGames-numPostponed,
                        numPostponed))

            totalAwayGoals = 0
            totalHomeGoals = 0
            totalGoals = 0
            totalMinGoals = 0
            totalSecondsRem = 0

            for game in games:
                print("")
                status = game['status']
                print("Status = {} - {}".format(status['abstractGameState'], status['detailedState']))
                postponed = is_game_postponed(game)

                linescore = game['linescore']
                teams = linescore['teams']

                awayTeamName = teams['away']['team']['name']
                homeTeamName = teams['home']['team']['name']

                if postponed:
                    print("    {} at {}".format(awayTeamName, homeTeamName))
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

                print("    {} {}".format(awayTeamName, awayGoals))
                print("    {} {}".format(homeTeamName, homeGoals))

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
                print("Period = {}  Time rem = {}  Seconds rem = {}  % left = {:.2f}%  Total goals = {}  Min goals = {}"
                    .format(period,
                            timeRem,
                            secondsRem,
                            (secondsRem * 100.0) / 3600.0,
                            gameGoals,
                            gameMinGoals))

                scoringPlays = game['scoringPlays']
                for scoringPlay in scoringPlays:
                    print("    {}".format(scoringPlay['result']['description']))

            totalGoals = totalAwayGoals + totalHomeGoals
            print("")
            print("Away Goals = {}, Home Goals = {}, TOTAL = {}, "
                "Total MIN goals = {}, Total seconds rem = {}, Total games rem = {:.3f}"
                .format(totalAwayGoals,
                        totalHomeGoals,
                        totalGoals,
                        totalMinGoals,
                        totalSecondsRem,
                        totalSecondsRem / 3600.0))
