def identify_delimiter(filename):
    import csv
    sniffer = csv.Sniffer()
    with open(filename) as fp:
        delimiter = sniffer.sniff(fp.read(5000)).delimiter
    return delimiter


def identify_header(path, n=5, th=0.9, sep=None):
    import pandas as pd
    df1 = pd.read_csv(path, sep=sep, header='infer', nrows=n, on_bad_lines='warn', engine='python',
                      escapechar='\\')
    df2 = pd.read_csv(path, sep=sep, header=None, nrows=n, on_bad_lines='warn', engine='python',
                      escapechar='\\')
    sim = (df1.dtypes.values == df2.dtypes.values).mean()  # Boolean mask array mean
    return 'infer' if sim < th else None


def get_file_line_count(path, header=None):
    with open(path, 'rb') as file:
        for count, _ in enumerate(file):
            pass
    count = count if header else count + 1
    return count