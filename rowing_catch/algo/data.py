import scipy
from scipy import stats
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import json
from collections import namedtuple


def clean_and_index_data(df):
    df = df.rename(columns={'Handle/0/X': 'Handle_X', 'Handle/0/Y': 'Handle_Y', 'Shoulder/0/X': 'Shoulder_X',
                            'Shoulder/0/Y': 'Shoulder_Y', 'Seat/0/X': 'Seat_X'})
    df = df.drop(columns=['Time',
                          'Seat/0/Y'])  # Time column is not consistent, not good for index; Seat is not moving up or down therefore this column is not useful
    df.insert(0, 'Index', range(0, len(df)))
    df = df.set_index('Index')
    return df


def smoothing_data(df, rolling_window):
    df['Handle_X_Smooth'] = df['Handle_X'].rolling(rolling_window).mean()
    df['Handle_Y_Smooth'] = df['Handle_Y'].rolling(rolling_window).mean()
    df['Shoulder_X_Smooth'] = df['Shoulder_X'].rolling(rolling_window).mean()
    df['Shoulder_Y_Smooth'] = df['Shoulder_Y'].rolling(rolling_window).mean()
    df['Seat_X_Smooth'] = df['Seat_X'].rolling(rolling_window).mean()
    return df


def plot_proof_of_smoothing(df):
    df.plot(y=['Handle_X', 'Handle_X_Smooth'], figsize=(10, 2))
    df.plot(y=['Handle_Y', 'Handle_Y_Smooth'], figsize=(10, 2))
    df.plot(y=['Shoulder_X', 'Shoulder_X_Smooth'], figsize=(10, 2))
    df.plot(y=['Shoulder_Y', 'Shoulder_Y_Smooth'], figsize=(10, 2))
    df.plot(y=['Seat_X', 'Seat_X_Smooth'], figsize=(10, 2))
    plt.show()


# start of stroke cycle is when the rower at hands away position during the recovery
def find_and_mark_start_of_stroke_cycle(df, frame_of_hands_away):
    def debugStrokeStart(window):
        current = window.iloc[1]
        currentIndex = window.index[1]
        prev = window.iloc[0]
        prevIndex = window.index[0]

        if currentIndex > 950 and currentIndex < 1010:
            print(window)

        if prev > frame_of_hands_away and current <= frame_of_hands_away:
            return frame_of_hands_away
        else:
            return 0

    def markStrokeStart(window):
        current = window[1]
        prev = window[0]

        if prev > frame_of_hands_away and current <= frame_of_hands_away:
            return frame_of_hands_away
        else:
            return 0

    # df['Handle_X_Smooth'].rolling(2).apply(debugStrokeStart)
    df['Stroke_Start'] = df['Handle_X_Smooth'].rolling(2).apply(markStrokeStart, raw=True)
    return df


# first and last stroke cycles are partial most of the time, should be removed to get clean data
def remove_partial_stroke_cycle(df, frame_of_hands_away):
    stroke_starts = df.loc[df['Stroke_Start'] == frame_of_hands_away]
    first_index = stroke_starts.index[0]
    last_index = stroke_starts.index[-1] - 3  # delete before new cycle starts
    df = df.drop(df.index[0:first_index])
    df = df.drop(df.index[last_index:df.index[-1]])
    return df


def split_into_cycles(df, frame_of_hands_away):
    stroke_starts = df.loc[df['Stroke_Start'] == frame_of_hands_away]
    start_index = stroke_starts.index[0]
    cycles = []
    for index in stroke_starts.index[1:]:
        cycle = df[start_index:index - 1]
        cycles.append(cycle)
        start_index = index
    # add new index to make merge easier
    for c in cycles:
        c.reset_index(drop=True, inplace=True)
        c.index.name = 'Cycle_Index'
    return cycles


def plot_proof_of_spliting(cycles):
    # verify the split was okay and the lines are roughly together
    df_handles = pd.DataFrame()
    for index, c in enumerate(cycles):
        df_handles['Handle_X' + str(index)] = c['Handle_X_Smooth']
    df_handles.plot(figsize=(12, 5))
    plt.show()


# next task: merge with error bars, keep min, max of data for that cycle index
def merge_cycles(cycles):
    # merge the cycles into one average dataframe
    df = pd.concat(cycles).groupby('Cycle_Index', as_index=True).mean()

    # drop Stroke_Start as it is not needed anymore
    df = df.drop(columns=['Stroke_Start'])

    # remove rows that are longer than minimum length, as the average value cannot be calculated properly and skews the data anyway
    rows = []
    for c in cycles:
        rows.append(c.shape[0])
    shortest_row_count = min(rows)
    df = df[0:shortest_row_count]

    return df, shortest_row_count


# standardize, rescale the values
def rescale(df):
    df['Handle_X_Smooth'] = stats.zscore(df['Handle_X_Smooth'])
    df['Handle_Y_Smooth'] = stats.zscore(df['Handle_Y_Smooth'])
    df['Shoulder_X_Smooth'] = stats.zscore(df['Shoulder_X_Smooth'])
    df['Shoulder_Y_Smooth'] = stats.zscore(df['Shoulder_Y_Smooth'])
    df['Seat_X_Smooth'] = stats.zscore(df['Seat_X_Smooth'])
    return df


def plot_catch_and_finish(title, data, catch_index, finish_index):
    ax = data.plot(figsize=(18, 8))
    ax.axvline(catch_index, color='green', linestyle='dashed')
    plt.text(catch_index + 2, 0, 'Catch', rotation=90)
    ax.axvline(finish_index, color='green', linestyle='dashed')
    plt.text(finish_index + 2, 0, 'Finish', rotation=90)

    plt.title(title)
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.1))
    plt.show()


def stroke_ratio(catch_index, finish_index, shortest_row_count):
    drive_duration = finish_index - catch_index
    recovery_duration = shortest_row_count - drive_duration
    drive_percentage = (drive_duration / shortest_row_count) * 100
    recovery_percentage = (recovery_duration / shortest_row_count) * 100
    return drive_percentage, recovery_percentage


# based on the page 17 Fig. 2.6 in the 'The Biomechanics of Rowing' book 2nd revision
def rhythm(spm):
    drive_ratio = -0.000202 * (spm * spm) + 0.0195 * spm + 0.0793
    return drive_ratio


def __plot_stroke_ratio_only(title, df):
    ax = sns.lineplot(data=df, x='SPM', y='Ratio', hue='Origin', style='Origin', markers=True, markersize=14)
    ax.set(title=title)
    plt.grid(True)
    loc = plticker.MultipleLocator(base=2.5)
    ax.yaxis.set_major_locator(loc)
    ax.yaxis.set_major_formatter('{x}%')
    for x, y in zip(df['SPM'], df['Ratio']):
        if x % 5 == 0:
            plt.text(x=x+0.4, y=y-1.1, s='{:.1f}%'.format(y), fontsize=14,
                     bbox=dict(facecolor='lightblue', alpha=0.3,
                               linewidth=0))
    plt.show()


def plot_stroke_ratio(origin, drive_percentage, spm):
    i = pd.DataFrame()
    i['SPM'] = range(14, 50)
    i['Ratio'] = rhythm(i['SPM']) * 100
    i['Origin'] = 'Ideal'

    r = pd.DataFrame()
    r['SPM'] = [spm]
    r['Ratio'] = [drive_percentage]
    r['Origin'] = origin

    df = i.merge(right=r, how='outer')
    __plot_stroke_ratio_only('Stroke Ratio [Drive vs Recovery]', df)


def plot_stroke_ratios(title, df):
    i = pd.DataFrame()
    i['SPM'] = range(14, 50)
    i['Ratio'] = rhythm(i['SPM']) * 100
    i['Origin'] = 'Ideal'

    df = df.merge(right=i, how='outer')
    __plot_stroke_ratio_only(title, df)


def read_stroke_ratio_pairs_by_spms(derivatives_csv_path, metadata_of_derivatives_csv_path, spms):
    stroke_ratio_pairs = []

    for spm in spms:
        df = pd.read_csv(derivatives_csv_path.format(spm=spm))
        md = import_metadata(metadata_of_derivatives_csv_path.format(spm=spm))

        shortest_row_count = df.shape[0]
        drive_percentage, recovery_percentage = stroke_ratio(md.catch_index, md.finish_index, shortest_row_count)
        stroke_ratio_pairs.append((spm, drive_percentage))
    return pd.DataFrame(stroke_ratio_pairs, columns=['SPM', 'Ratio'])


def concat_stroke_ratio_pairs(df_old, df_new):
    df = pd.concat([df_new[['SPM', 'Ratio', 'Origin']], df_old])
    return df.reset_index()


class StrokeRatioData:
    def __init__(self, derivatives_csv_path, metadata_of_derivatives_csv_path, origin, spms):
        self.derivatives_csv_path = derivatives_csv_path
        self.metadata_of_derivatives_csv_path = metadata_of_derivatives_csv_path
        self.spms = spms
        self.origin = origin


def read_stroke_ratio_pairs(stroke_ratio_data: list[StrokeRatioData]):
    df = pd.DataFrame()
    for std in stroke_ratio_data:
        df_new = read_stroke_ratio_pairs_by_spms(std.derivatives_csv_path,
                                                                  std.metadata_of_derivatives_csv_path, std.spms)
        df_new['Origin'] = std.origin
        df = concat_stroke_ratio_pairs(df, df_new)
    return df


# Derivatives
# Caveat - smoothing pushes the line right potentially which gives misaligned lines
def derivate(df, column_name, derivative_column_name, smoothing, scaling):
    dy = np.diff(df[column_name])
    dx = np.diff(df.index)
    deriv = dy / dx
    # prepanding first element so the new data has the same dimension as the original
    df[derivative_column_name] = np.insert(deriv, 0, deriv[0], axis=0)
    # smoothing the derivative
    df[derivative_column_name] = df[derivative_column_name].rolling(smoothing).mean()
    # shifts the data to the left as rolling 'pushed' to the right
    df[derivative_column_name] = df[derivative_column_name].shift(periods=int(smoothing / 2) * -1, fill_value=0)
    # back fill NaN so rescaling will work
    df[derivative_column_name] = df[derivative_column_name].bfill()
    # rescale the derivative
    df[derivative_column_name] = stats.zscore(df[derivative_column_name]) * scaling
    return df


def process_stroke_analysis(trajectory_csv_path, spm, frame_of_hands_away, catch_index, finish_index):
    df = pd.read_csv(trajectory_csv_path)
    df = clean_and_index_data(df)
    # smoothing the data
    df = smoothing_data(df, 10)

    df = find_and_mark_start_of_stroke_cycle(df, frame_of_hands_away)
    df = remove_partial_stroke_cycle(df, frame_of_hands_away)

    # original data is not needed anymore, we verified that the cleaned data is good
    df = df.drop(columns=['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X'])

    cycles = split_into_cycles(df, frame_of_hands_away)
    df, shortest_row_count = merge_cycles(cycles)

    df = rescale(df)

    drive_percentage, recovery_percentage = stroke_ratio(catch_index, finish_index, shortest_row_count)

    df = derivate(df, 'Handle_X_Smooth', 'Handle_X_Velocity', 5, 1)
    df = derivate(df, 'Handle_X_Velocity', 'Handle_X_Acceleration', 8, 0.5)
    df = derivate(df, 'Handle_X_Acceleration', 'Handle_X_Jerk', 5, 0.2)

    df = derivate(df, 'Shoulder_X_Smooth', 'Shoulder_X_Velocity', 5, 1)
    df = derivate(df, 'Shoulder_X_Velocity', 'Shoulder_X_Acceleration', 8, 0.5)
    df = derivate(df, 'Shoulder_X_Acceleration', 'Shoulder_X_Jerk', 5, 0.2)

    df = derivate(df, 'Seat_X_Smooth', 'Seat_X_Velocity', 5, 1)
    df = derivate(df, 'Seat_X_Velocity', 'Seat_X_Acceleration', 8, 0.5)
    df = derivate(df, 'Seat_X_Acceleration', 'Seat_X_Jerk', 5, 0.2)

    return df, drive_percentage


def export_metadata(trajectory_csv_path, derivatives_csv_path, metadata_of_derivatives_csv_path, spm,
                    frame_of_hands_away, catch_index, finish_index, drive_percentage):
    data = {
        "trajectory_csv_path": trajectory_csv_path,
        "derivatives_csv_path": derivatives_csv_path,
        "spm": spm,
        "frame_of_hands_away": frame_of_hands_away,
        "catch_index": catch_index,
        "finish_index": finish_index,
        "drive_percentage": drive_percentage
    }

    metadata_json = json.dumps(data)
    f = open(metadata_of_derivatives_csv_path, "w")
    f.write(metadata_json)
    f.close()


def import_metadata(metadata_of_derivatives_csv_path):
    f = open(metadata_of_derivatives_csv_path, 'r')
    metadata_string = f.read()
    metadata = json.loads(metadata_string,
                          object_hook=lambda d: namedtuple('MetadataStrokeAnalysis', d.keys())(*d.values()))
    f.close()
    return metadata


def stabilize_raw_trajectory(raw_csv_path, trajectory_csv_path):
    df = pd.read_csv(raw_csv_path)
    df['Handle_X'] = df['Handle/0/X'] - df['Boat/0/X']
    df['Handle_Y'] = df['Handle/0/Y'] - df['Boat/0/Y']
    df['Shoulder_X'] = df['Shoulder/0/X'] - df['Boat/0/X']
    df['Shoulder_Y'] = df['Shoulder/0/Y'] - df['Boat/0/Y']
    df['Seat_X'] = df['Seat/0/X'] - df['Boat/0/X']
    df['Seat_Y'] = df['Seat/0/Y'] - df['Boat/0/Y']

    df['Handle/0/X'] = df['Handle_X']
    df['Handle/0/Y'] = df['Handle_Y']
    df['Shoulder/0/X'] = df['Shoulder_X']
    df['Shoulder/0/Y'] = df['Shoulder_Y']
    df['Seat/0/X'] = df['Seat_X']
    df['Seat/0/Y'] = df['Seat_Y']

    df = df.drop(
        columns=['Boat/0/X', 'Boat/0/Y', 'Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y'])
    df.to_csv(trajectory_csv_path, index=False)


class MaxWattData:
    def __init__(self, log_book_csv_path, date_of_data, skip_number_of_rows, matching_time_pattern):
        self.log_book_csv_path = log_book_csv_path
        self.date_of_data = date_of_data
        self.skip_number_of_rows = skip_number_of_rows
        self.matching_time_pattern = matching_time_pattern


def read_concept2_log_book(m: MaxWattData):
    df = pd.read_csv(m.log_book_csv_path, skiprows=m.skip_number_of_rows)
    df = df.drop(columns=['Date', 'Time of Day', 'Workout Name'])
    df = df[df['Time.1'] == m.matching_time_pattern]
    df['Type'] = m.date_of_data
    return df


def concat_log_books_for_watt(df_old, df_new):
    df = pd.concat([df_new[['SPM', 'Watt', 'Type']], df_old])
    return df.reset_index(drop=True)


def read_max_watt_datas(max_watt_data_list: list[MaxWattData]):
    df = pd.DataFrame()
    for m in max_watt_data_list:
        df_new = read_concept2_log_book(m)
        df = concat_log_books_for_watt(df, df_new)
    return df


def plot_max_watt_datas(df, x_name, y_name, title):
    ax = sns.lineplot(data=df, x=x_name, y=y_name, hue='Type', marker='o', markersize=10)
    ax.set(title=title)
    plt.grid(True)
    x_ticks = df[x_name]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(map(str, x_ticks))
    loc = plticker.MultipleLocator(base=50.0)
    ax.yaxis.set_major_locator(loc)

    for x, y in zip(df[x_name], df[y_name]):
        plt.text(x=x + 0.3, y=y - 6, s='{:.0f}'.format(y), fontsize=14,
                 bbox=dict(facecolor='lightblue', alpha=0.3, linewidth=0))
    plt.show()


def calculate_relative_watt_time(df):
    df['Recovery Ratio'] = 1 - rhythm(df['SPM'])
    df['Relative Watt Time'] = df['Watt'] * (df['Recovery Ratio'] * df['Recovery Ratio'])  # Watt * (Recovery Ratio)^2
    return df


def plot_relative_watt_time(df, x_name, y_name, title):
    ax = sns.lineplot(data=df, x=x_name, y=y_name, hue='Type', marker='o', markersize=10)
    ax.set(title=title)
    plt.grid(True)
    x_ticks = df[x_name]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(map(str, x_ticks))
    plt.show()
