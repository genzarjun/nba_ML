from nba_api.stats.static import players #importing players
from nba_api.stats.endpoints import commonplayerinfo #importing player info
from nba_api.stats.endpoints import playercareerstats #importing player stats

#installed libraries
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#standard libraries
import time
import random
import math

#LOWESS function
from statsmodels.nonparametric.smoothers_lowess import lowess

headers  = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

nba_players = players.get_active_players()

df = pd.DataFrame(nba_players) #converting all the active player info into a dataframe

removed_full_names = df.loc[:,'id':'last_name'] #NOT USED - just showing its able to retrieve precise data from the DataFrame

active_players_ids = df.loc[:, 'id'].to_list() #: means its choosing all the rows

#creating a function that gets player info data, ultimately letting us get the player heights

def get_player_info(nba_player_id):
  player_info = commonplayerinfo.CommonPlayerInfo(player_id=nba_player_id, headers=headers,timeout=100)
  df = player_info.common_player_info.get_data_frame()
  return df

#creating a function that gets player game stats, for CareerTotalsRegularSeason, and provides the 'PerGame' stats per season

def get_player_game_stats(nba_player_id):
  player_stats = playercareerstats.PlayerCareerStats(player_id=nba_player_id, per_mode36='PerGame')
  df = player_stats.get_data_frames()[0]
  return df

#getting all the HEIGHTS of the players

list_of_player_info = [] #creating an empty list

#getting the player INFO
for nba_player_id in active_players_ids:
  player_info = get_player_info(nba_player_id) #calling the function we made above, with our ids from active_player_ids as parameters
  list_of_player_info.append(player_info) #adding the data frame to the list, list_of_player_info
  time.sleep(1.0) #we are adding a mini-sleep here so it doesn't overwhelm nba.com with so many calls and throw an error

#organizing the PLAYER INFO list into a full pandas dataframe
final_df_player_info = pd.concat(list_of_player_info, ignore_index = True)

undrafted_players = final_df_player_info.loc[(final_df_player_info['DRAFT_YEAR'] == 'Undrafted'), :] #listing undrafted players

final_df_player_info_cleaned = final_df_player_info.loc[(final_df_player_info['DRAFT_YEAR'] != 'Undrafted'), :]

reseted_player_info = final_df_player_info_cleaned.reset_index(drop=True) #Drop=False says that the index data is added to a new column

active_players_ids = reseted_player_info['PERSON_ID'] #taking the player ids from the dataframe, and setting them to the active_player_ids, so that it is easy to get the right game stats now, with removed duplicated and undrafted players!

heights_df = reseted_player_info.loc[:,"HEIGHT"] #getting the heights

#getting the player STATS

list_of_player_game_stats = []

for nba_player_id in active_players_ids:
  player_game_stats = get_player_game_stats(nba_player_id)
  list_of_player_game_stats.append(player_game_stats)
  time.sleep(1.0)

#organizing the PLAYER STATS list into a proper pandas dataframes
uncleaned_final_df_player_game_stats = pd.concat(list_of_player_game_stats, ignore_index = True)

#pd.concat is used for concatenating a list of dataframes
#ignore_index = True, is telling that when concatenating the dataframes, reset all the index and start with the top most item's index to 0.
'''ignore_index = False, is telling that when concatenating the dataframes, the indexes of the
dataframes being concatenated will be preserved, meaning that there will be multiple of the same indexes in the new dataframe'''

final_df_player_game_stats = uncleaned_final_df_player_game_stats.loc[((uncleaned_final_df_player_game_stats['SEASON_ID']) =='2024-25'),:] #change the season to whatever is the current season
#this line gets me what I need but note that the indices don't reset, which is why we use the .reset_index method later


no_duplicates = final_df_player_game_stats.drop_duplicates('PLAYER_ID', keep='last')
'''if a player played in the same season for two different teams, then their will be two separate rows with the same player/player ID
Therefore, we need to remove the duplicated player IDs by choosing one of their rows (the first one)'''

# Concatenate again after cleaning
game_stats_reseted_index = no_duplicates.reset_index(drop=True) #we are using the .reset_index() method so the indices start from 0 at the beginning
#drop=True tells us that the indices shouldn't go in a new column




#this small chunk checks if a player hasn't had a 24-25 season (for an injury or some sort), then they are removed from the heights dataframe
not_having_24_25_season = []

temporary_index = 0
increment = 0
for x in active_players_ids:
  try:
    if x == ((list(game_stats_reseted_index['PLAYER_ID']))[temporary_index]):
      temporary_index += 1
    elif (x != (list(game_stats_reseted_index['PLAYER_ID']))[temporary_index]):
      not_having_24_25_season.append((temporary_index)+(increment))
      increment += 1
  except IndexError:
    not_having_24_25_season.append(temporary_index)
    temporary_index += 1

if len(not_having_24_25_season) > 0:
  heights_df.drop(heights_df.index[not_having_24_25_season], axis=0, inplace=True) #axis=0 says we are dropping rows
  reseted_heights_df = heights_df.reset_index(drop=True) #Drop=False says that the index data is added to a new column'''




condensed_final_df_player_game_stats=game_stats_reseted_index.loc[:, 'GP':'PTS']

condensed_final_df_player_game_stats.drop(['GP','MIN','GS', 'FGA', 'FG_PCT', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT'],axis=1,inplace=True) #taking out non-worthy stats
#inplace=True is directly applying to the dataframe, meaning that we don't have to assign the new dataframe to a new variable
#axis=1 specifies that we are dropping columns, axis=0 means we are dropping rows

#combining the TWO dataframes

full_pd_cleaned = pd.concat([reseted_heights_df, condensed_final_df_player_game_stats], axis=1) #axis=1 combines the columns side-by-side, compared to axis=0 combining the columns vertically

full_pd_cleaned

print("Welcome to this NBA Height-Performance Analyzer!")

stats = ['FGM', 'FG3M', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
stat = 0
def ask():
  global stat
  stat = input("\n\nChoose a stat that you would like to see the most optimal height for and enter\nthe stat name exactly, each stat account for all the active players' stats per game in the regular season:\nFGM, FG3M, OREB, DREB, REB, AST, STL, BLK, TOV, PF, PTS\nFor example, enter, 'AST', (without quotes)  ")

def loop():
  if stat in stats:
    # Convert height for sorting
    def convert_height_to_feet(height_str):
        feet, inches = height_str.split('-')
        return (int(feet) + (int(inches) / 12))

    # Add a new hidden column (NEW_HEIGHTS_FOR_SORTING) for sorting
    full_pd_cleaned['NEW_HEIGHTS_FOR_SORTING'] = full_pd_cleaned['HEIGHT'].apply(convert_height_to_feet)

    # Sort by actual height (feet), using the new column for heights that we just made
    df_sorted = full_pd_cleaned.sort_values(by='NEW_HEIGHTS_FOR_SORTING')

    # Use ML lowess function to take into account trends in the data and apply weights to each of the heights based on the nearby points
    #frac determines how how the nearby points are being taken into account when applying the weights to each of the heights, ultimately resulting in how the curve will be smoothed
    #the higher the frac, the smoother the curve, the lower the frac, the more sensitive it will be to fluctuations
    smoothed = lowess(df_sorted[stat], df_sorted['NEW_HEIGHTS_FOR_SORTING'], frac=0.2)


    max_idx = np.argmax(smoothed[:, 1]) #returns the index of the highest value in the second column (the y-values) of the 2D Numpy Array that smoothed returns
    best_height = smoothed[max_idx, 0]
    best_height_formatted_without_decimal = f"{int(best_height)}-{round((((best_height) - (math.floor(best_height)))*12))}"
    best_stat = smoothed[max_idx, 1]


    plt.figure(figsize=(10, 6))
    plt.scatter(df_sorted['NEW_HEIGHTS_FOR_SORTING'], df_sorted[stat], label=f'Average {stat}', color='black')
    plt.plot(smoothed[:, 0], smoothed[:, 1], color='blue', linewidth=2, label='LOWESS Curve') #smoothed returns a 2D Numpy array in the format [x_value, smoothed_y_value] for each row
    #using slicing, smoothed[:, 0] tells us that we are taking all the rows in the first column, (the x-values)
    # the smoothed [:,1] tells us that we are taking all the rows in the second column, (the smoothed y-values)

    # Annotate the peak
    plt.scatter(best_height, best_stat, color='red', zorder=5, label=f'Peak: {best_stat:.2f} {stat} @ {best_height_formatted_without_decimal} ft')
    plt.text(
        best_height, best_stat + 0.3,
        f'{best_stat:.2f} {stat}\nat {best_height_formatted_without_decimal}',
        ha='center', color='red'
    )

    plt.xlabel('Height (feet)')
    plt.ylabel(f'{stat} per Game')
    plt.title(f'Height vs {stat} per Game')
    plt.xticks(df_sorted['NEW_HEIGHTS_FOR_SORTING'], df_sorted['HEIGHT'], rotation=25)
    plt.legend()
    plt.grid(True)
    plt.show()
    print(f"\n\nTHE MOST OPTIMAL HEIGHT FOR {stat} IS {best_height_formatted_without_decimal}")
  elif stat not in stats:
    print("\n\nYou entered an invalid input:")
    print(stat)
    ask()
    loop()

#of course we can't forget to call the functions!
ask()
loop()

