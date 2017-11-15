import praw
from tkinter import *
from tkinter import font
from bs4 import BeautifulSoup
import webbrowser
from urllib.request import *
import base64
from info import username, password, client_id, client_secret, user_agent

reddit = praw.Reddit(client_id=client_id.strip(),
                     client_secret=client_secret.strip(),
                     username=username.strip(),
                     password=password.strip(),
                     user_agent=user_agent.strip())

# Uses praw (Python Reddit API Wrapper) to access the streams in the comments on r/nbastreams
subreddit = reddit.subreddit('nbastreams')

soup = BeautifulSoup(urlopen('https://www.foxsports.com/nba/schedule').read(), 'html.parser')
todays_games = soup.find('table', {'class': 'wisbb_scheduleTable'}).find('tbody')

'''
Team class that stores name, record, score
Score's value will differ depending on whether the team's game:
    -Hasn't started yet
    -Is currently going on
    -Is over
'''
class Team:
    def __init__(self, name, record, score, icon):
        self.name = name
        self.record = record
        self.score = score

        # The parameter icon is the url to the team icon on the FOX website so it still has to be opened and encoded
        # into base64 because that is the type of data that Python accepts
        pic = urlopen(icon).read()
        b64 = base64.encodebytes(pic)
        icon = PhotoImage(data=b64).subsample(2, 2)
        self.icon = Label(root, image=icon)
        self.icon.image = icon


# Game class - at is the away team and ht is the home team for the game
class Game:
    def __init__(self, time, at, ht):
        self.time = time
        self.at = at
        self.ht = ht

    def game_state(self):
        # Returns 0 if the game hasn't started yet
        if 'ET' in self.time:
            return 0
        # Returns 2 if the game has ended
        if 'FINAL' in self.time:
            return 2
        # Returns 1 if the game is currently going on
        else:
            return 1

    # Changes the format that the game is presented in
    # Depends on if the game hasn't started, is currently going on, is over
    def format_game(self):
        state = self.game_state()

        if state > 0:
            game_text = '{} {} | {} {}'.format(self.at.name, self.at.score, self.ht.score, self.ht.name)
            if state == 2:
                game_text = 'FINAL\n' + game_text
            return game_text
        else:
            return '{}\n{} {} vs. {} {}'.format(self.time, self.at.name, self.at.record, self.ht.record, self.ht.name)


def get_streams(team):
    streams = []
    try:
        for submission in subreddit.hot():
            # Only need links in the game threads
            if team.lower() in submission.title.lower():
                submission.comments.replace_more(limit=0)

                for comment in submission.comments:
                    flair = comment.author_flair_text
                    # Only get streams from accounts that have been approved or verified by /r/NBAStreams
                    if flair == 'Verified Streamer' or flair == 'Approved Streamer':
                        for get_tag in comment.body_html.split('<'):
                            if 'http' in get_tag and 'prnt' not in get_tag:
                                url = get_tag.split('"')[1]
                                streams.append(url)
    except IndexError:
        if not streams:
            return

    return streams


# Extracts the name of the team from the html in BeautifulSoup
def get_name(html):
    return html.span.findAll('label')[1].text.strip() + ' ' + html.findAll('span')[1].text.strip()


# Extracts the record of the team from the html in BeautifulSoup
def get_record(html):
    return html.find('span', {'class': 'wisbb_teamRecord'}).text.strip()


# Extracts the score of the team from the html in BeautifulSoup
def get_score(html):
    return html.find('div', {'class': 'wisbb_score'}).text.strip()


# Extracts the time of the game from the html in BeautifulSoup
def get_time(html):
    if html.find('span', {'class': 'wisbb_status'}).text == '':
        return html.findAll('span', {'class': 'wisbb_status'})[1].text
    return html.find('span', {'class': 'wisbb_status'}).text


# Returns a list of Game objects, filled with the games scheduled for the current day
def get_games():
    list_games = []

    for game in todays_games.findAll('tr'):
        info = game.findAll('td')
        at_info = info[0]
        time = info[1]
        ht_info = info[2]

        away_team = Team(get_name(at_info), get_record(at_info), get_score(at_info), at_info.img['src'])
        home_team = Team(get_name(ht_info), get_record(ht_info), get_score(ht_info), ht_info.img['src'])
        # Create new Game objects for each game scheduled that day and add it to the list that is returned
        game = Game(get_time(time), away_team, home_team)

        list_games.append(game)
    return list_games


# Class for Tkinter app
class Stream:
    def __init__(self, root):
        root.title("NBA Streams")
        self.title_label = Label(root, text="Which game do you want to watch?", font=50)
        self.title_label.grid(row=0, column=1, padx=7, pady=7)
        self.game_label = Label(root, font=50)
        self.game_labels = self.stream_labels = self.icons = []
        self.back_button = Button(root, text="<- Back to the games")
        self.show_games()

    def show_games(self):
        row = 1
        # For loop to show all of the games for the current day
        for game in get_games():
            game_label = Label(root, text=game.format_game())
            label_font = font.Font(game_label, game_label.cget("font"))
            game_label.configure(font=label_font, fg="blue", cursor="hand2")
            game_label.grid(row=row, column=1, padx=7, pady=7)
            # Bind the labels to open the streams for the game that was clicked
            game_label.bind("<Button-1>", lambda event, game=game: self.show_streams(game))
            self.game_labels.append(game_label)

            game.at.icon.grid(row=row, column=0)
            game.ht.icon.grid(row=row, column=2)
            self.icons.extend((game.ht.icon, game.at.icon))

            row += 1

    # Sets the title back to it's original state
    def set_title_back(self):
        self.title_label.config(text="Which game do you want to watch?", fg='black')

    # Shows the icon for team at row row, and column col
    def show_icon(self, team, row, col):
        # Creates an image for the icon and shrinks it by 50%
        icon = PhotoImage(data=team.icon).subsample(2, 2)
        label = Label(root, image=icon)
        label.image = icon
        label.grid(row=row, column=col)
        self.icons.append(label)

    # Forgets all of the grids associated with the window showing the streams
    def forget_stream_grids(self, game):
        for label in self.stream_labels:
            label.grid_forget()
        self.game_label.grid_forget()
        game.at.icon.grid_forget()
        game.ht.icon.grid_forget()
        self.back_button.grid_forget()

    # Forgets all of the grids associated with the window showing the games
    def forget_game_grids(self, game):
        for label in self.game_labels:
            label.grid_forget()
        for icon in self.icons:
            icon.grid_forget()
        self.title_label.grid_forget()

    # Hides or shows the games depending on what value boolean is
    # If boolean is 0, it hides all of the games except for the one the user clicked on
    def hide_games(self, boolean, game):
        # If boolean is 0 then show the streams, otherwise hide the streams and show the games again
        if boolean == 0:
            self.forget_game_grids(game)
            self.game_label.config(text=game.format_game(), font=30, fg='red')
            self.game_label.grid(row=0, column=1)
            game.at.icon.grid(row=0, column=0)
            game.ht.icon.grid(row=0, column=2)
        else:
            self.forget_stream_grids(game)
            self.title_label.grid(row=0, column=1, padx=7, pady=7)
            self.show_games()

    # Iterate through the list returned by get_streams
    def show_streams(self, game):
        row = 1
        streams = get_streams(game.ht.name)

        # If streams is empty the team isn't in a game
        if not streams:
            self.title_label.config(text="That game hasn't started yet!", fg='red', font=20)
            self.title_label.after(1600, self.set_title_back)
            return

        # If the game is 2 then the game is over
        if game.game_state() == 2:
            self.title_label.config(text="That game is already over!", fg='red', font=20)
            self.title_label.after(1600, self.set_title_back)
            return

        self.hide_games(0, game)

        # List the urls out and bind the left click to open the url
        for url in streams:
            label = Label(root, text=url)
            label.grid(row=row, column=1, padx=7, pady=7)
            label_font = font.Font(label, label.cget("font"))

            # If there are games for that team going on then the urls will appear in blue
            # and when the user's mouse hovers over them the url will be underlined and their mouse will change
            label.configure(font=label_font, fg="blue", cursor="hand2")
            label.bind("<Button-1>", lambda event, name=url: webbrowser.open_new(name))
            self.stream_labels.append(label)
            row += 1

        self.back_button.bind("<ButtonRelease-1>", lambda event: self.hide_games(1, game))
        self.back_button.grid(row=row, column=1, padx=7, pady=7)


root = Tk()
app = Stream(root)
root.mainloop()