"""Module to augment CSV survey data with duration and banned pesticides use.

Libraries:
pip3 install fuzzywuzzy[speedup]
pip3 install pandas

Use:
from survey_data_augmenter import augment
augment('path_to_data.csv')
"""

from datetime import datetime
from functools import partial
import re

from fuzzywuzzy import fuzz, process
import pandas as pd

# Constants
time_format = '%m/%d/%y %H:%M'
banned_pesticides = ['endosulfan', 'gramaxon', 'paraquat', 'preglone',
                     'parathion', 'terbufos', 'thiodan', 'vidate']
pesticide_columns = ['herbicides', 'other_herbicides', 'fertilizers',
                     'other_fertilizers', 'insecticides', 'other_insecticides']
augmented_csv_ending = '_augmented.csv'
augmented_pickle_ending = '_augmented.pickle'


def duration(format, started_time, ended_time):
    """Calculates duration between start and end times given time format."""
    started_time = datetime.strptime(started_time, format)
    ended_time = datetime.strptime(ended_time, format)
    total_time = ended_time - started_time
    return int((total_time.days * 24 * 60) + (total_time.seconds / 60))


def check_pesticides(banned, allow_misspellings, pesticides):
    """Checks for banned pesticides. Yamaguchi et. al. suggest <22.222 threshold
    for chemical names, which rejects the usual 2 mismatches of 9 e.g. malathion
    vs. parathion (22.222)[goo.gl/piAvco]. Cap of 78 accepts 22.5, hence 79.
    """
    # Dash keeps npk codes (e.g. 18-46-0) as single unit; underscores also kept
    pesticides = re.findall(r'[\w-]+', ' '.join(pesticides))
    if not pesticides:
        return 'NA'
    cap = 79 if allow_misspellings else 100
    for p in pesticides:
        if process.extractOne(p, banned, scorer=fuzz.ratio, score_cutoff=cap):
            return 'F'
    return 'P'


def augment(data_filename, allow_misspellings=True, save_pickle=False):
    # If data_filename is a CSV, read it into a DataFrame
    if not data_filename.endswith('.csv'):
        raise ValueError('{} is not a CSV file.'.format(data_filename))
    df = pd.read_csv(data_filename).fillna(value='')

    # Add duration (minutes), briefest 10% (boolean) and pesticide use columns
    p_duration = partial(duration, time_format)
    p_check = partial(check_pesticides, banned_pesticides, allow_misspellings)
    df['duration'] = list(map(p_duration, df['started_time'], df['ended_time']))
    df['shortest_decile'] = df['duration'] < df['duration'].quantile(0.1)
    df['no_banned_pesticides'] = df[pesticide_columns].apply(p_check, axis=1)

    # Save augmented data to file names constructed by adding to original root
    df.to_csv(data_filename[:-4] + augmented_csv_ending)
    if save_pickle:
        df.to_pickle(data_filename[:-4] + augmented_pickle_ending)
