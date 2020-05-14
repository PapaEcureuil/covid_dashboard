# Countries name not consistent between COVID dataset and Geojson data
COUNTRIES_NAME = {
    'Bahamas': 'The Bahamas',
    'Burma': 'Myanmar',
    'Cabo Verde': 'Cape Verde',
    'Congo (Brazzaville)': 'Republic of Congo',
    'Congo (Kinshasa)': 'Democratic Republic of the Congo',
    'Cote d\'Ivoire': 'Ivory Coast',
    'Czechia': 'Czech Republic',
    'Eswatini': 'Swaziland',
    'Guinea-Bissau': 'Guinea Bissau',
    'Holy See': 'Vatican',
    'Korea, South': 'South Korea',
    'North Macedonia': 'Macedonia',
    'Serbia': 'Republic of Serbia',
    'Taiwan*': 'Taiwan',
    'Tanzania': 'United Republic of Tanzania',
    'Timor-Leste': 'East Timor',
    'US': 'United States of America',
    'West Bank and Gaza' : 'Palestine'
}

COLOR_RANGE = [
    [65, 182, 196],
    [127, 205, 187],
    [199, 233, 180],
    [237, 248, 177],
    [255, 255, 204],
    [255, 237, 160],
    [254, 217, 118],
    [254, 178, 76],
    [253, 141, 60],
    [252, 78, 42],
    [227, 26, 28],
    [189, 0, 38],
    [128, 0, 38],
]

PLOTLY_COLORS = [
    f'rgba({x[0]}, {x[1]}, {x[2]}, 0.8)' for x in COLOR_RANGE
]