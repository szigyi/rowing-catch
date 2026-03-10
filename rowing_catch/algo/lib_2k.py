import scipy
from scipy import stats
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import json
from collections import namedtuple
import datetime as dt


def custom_palette(number_of_colours):
    return sns.color_palette('rocket', number_of_colours)


class Test2KData:
    def __init__(self, log_book_csv_path, date_of_data, skip_number_of_rows):
        self.log_book_csv_path = log_book_csv_path
        self.date_of_data = date_of_data
        self.skip_number_of_rows = skip_number_of_rows


def str_to_time_delta(x):
    return pd.to_timedelta("0 days 00:" + str(x))


def time_delta_to_seconds(x):
    return x.total_seconds()


def timedelta_to_string(td):
    td_in_seconds = td.total_seconds()
    _, remainder = divmod(td_in_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    minutes = int(minutes)
    seconds = int(seconds)
    if minutes < 10:
        minutes = "0{}".format(minutes)
    if seconds < 10:
        seconds = "0{}".format(seconds)
    return "{}:{}".format(minutes, seconds)


def seconds_to_split_time(x):
    return timedelta_to_string(pd.to_timedelta(x, 's'))


def generate_split_ticks_as_seconds(min_seconds, max_seconds):
    steps_in_seconds = 5
    td = []
    for s in range(min_seconds, max_seconds, steps_in_seconds):
        td.append(s)
    return pd.Series(td)


def read_2k_splits_logbook(d: Test2KData):
    df = pd.read_csv(d.log_book_csv_path, skiprows=d.skip_number_of_rows)
    df = df[['Time.1', 'Meters.1', 'SPM']]
    df = df.rename(columns={'Time.1': 'Time', 'Meters.1': 'Meters'})
    df = df.dropna()
    df['Time in Duration'] = df['Time'].map(str_to_time_delta)
    df['Time in Seconds'] = df['Time in Duration'].map(time_delta_to_seconds)
    df['Origin'] = d.date_of_data
    return df


def read_2k_total_logbook(d: Test2KData):
    df = pd.read_csv(d.log_book_csv_path, skiprows=d.skip_number_of_rows)
    df = df[['Time']]
    df = df.dropna()
    df['Time in Duration'] = df['Time'].map(str_to_time_delta)
    df['Time in Seconds'] = df['Time in Duration'].map(time_delta_to_seconds)
    df['Origin'] = d.date_of_data
    return df


def read_2k_split_results(test_2ks_data_list: list[Test2KData]):
    df = pd.DataFrame()
    for m in test_2ks_data_list:
        df_new = read_2k_splits_logbook(m)
        df = pd.concat([df_new[['Time', 'Time in Seconds', 'Meters', 'SPM', 'Origin']], df])
    return df.reset_index()


def read_2k_total_results(test_2ks_data_list: list[Test2KData]):
    df = pd.DataFrame()
    for m in test_2ks_data_list:
        df_new = read_2k_total_logbook(m)
        df = pd.concat([df_new[['Time', 'Time in Seconds', 'Origin']], df])
    return df.reset_index()


def plot_2k_split_results(title, df):
    min_seconds = int(df['Time in Seconds'].min()) - 5
    max_seconds = int(df['Time in Seconds'].max()) + 10
    colour_palette = custom_palette(len(df['Origin'].value_counts()))
    # line plot for split
    ax = sns.lineplot(data=df, x='Meters', y='Time in Seconds', hue='Origin', marker='o', markersize=10,
                      palette=colour_palette)
    ax.set(title=title)
    ax.grid(True)
    ax.set(ylabel='Time', xlabel='Meters')
    x_ticks = df['Meters']
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_ticks.map(lambda m: str(int(m)) + ' m'))

    y_ticks = generate_split_ticks_as_seconds(min_seconds, max_seconds)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_ticks.map(seconds_to_split_time))

    for x, y, t in zip(df['Meters'], df['Time in Seconds'], df['Time']):
        plt.text(x=x + 0.9, y=y - 0.6, s=t, fontsize=14,
                 bbox=dict(facecolor='grey', alpha=0.3, linewidth=0))

    # line plot for stroke per minute
    ax2 = ax.twinx()
    sns.lineplot(data=df, x='Meters', y='SPM', hue='Origin', marker='^', markersize=10, linestyle=(0, (3, 10, 1, 10)), alpha=0.5,
                 palette=colour_palette, ax=ax2)
    ax2.grid(False)

    for x, y in zip(df['Meters'], df['SPM']):
        plt.text(x=x + 1.2, y=y, s=str(int(y)), fontsize=12,
                 bbox=dict(facecolor='lightgrey', alpha=0.3, linewidth=0))

    plt.show()


def plot_2k_total_results(title, df):
    min_seconds = int(df['Time in Seconds'].min()) - 20
    max_seconds = int(df['Time in Seconds'].max()) + 5
    colour_palette = custom_palette(len(df['Origin'].value_counts()))
    df = df.iloc[::-1]
    pd.set_option('mode.chained_assignment', None)  # to avoid false positive interpreter warnings of SettingWithCopy
    df['Previous Time'] = df['Time in Seconds'].rolling(window=2).apply(lambda x: x.iloc[0])
    df['Difference'] = df['Time in Seconds'].diff()
    pd.set_option('mode.chained_assignment', 'raise')  # turning back on the SettingWithCopy warning

    ax = sns.barplot(data=df, y='Origin', x='Time in Seconds', hue='Origin', palette=colour_palette)
    ax.set(title=title)
    ax.grid(True)
    ax.set(xlim=(min_seconds, max_seconds), xlabel='Time', ylabel='Date')
    ax.xaxis.set_major_formatter(lambda x, pos: seconds_to_split_time(x))

    for x, y, t in zip(df['Time in Seconds'], df['Origin'], df['Time']):
        plt.text(x=x - 6, y=y, s=t, fontsize=14, bbox=dict(facecolor='lightgrey', linewidth=0))

    sns.barplot(data=df, y='Origin', x='Previous Time', hue='Origin', palette=colour_palette, alpha=0.5)

    for x, y, t in zip(df['Previous Time'], df['Origin'], df['Difference']):
        if not np.isnan(t):
            plt.text(x=x - 2, y=y, s=str(int(t)) + ' s' , fontsize=14, bbox=dict(facecolor='lightgrey', linewidth=0))

    plt.show()
