# Generator message for empty return value
def gen_():
    return 'warning', 'The generator returned empty! Try to set the values again!'


# Generator message for 'AA' success return value
def gen_aa():
    return 'success', 'You have successfully set the values!'


# Generator message for invalid packet value
def gen_err():
    return 'error', 'Invalid packet!'


# Default COM port baud rates
device_baud = ['1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200']

# Generator input data types
signal_input = [
    'low_alpha_amplitude',
    'low_alpha_frequency',
    'high_alpha_amplitude',
    'high_alpha_frequency',
    'low_beta_amplitude',
    'low_beta_frequency',
    'high_beta_amplitude',
    'high_beta_frequency',
    'delta_amplitude',
    'delta_frequency',
    'low_gamma_amplitude',
    'low_gamma_frequency',
    'mid_gamma_amplitude',
    'mid_gamma_frequency',
    'theta_amplitude',
    'theta_frequency'
]

# TGAM1 packet structure based on MindSet Communications Protocol from June 28, 2010
signal_protocol = {
    'sync': 2,
    'plength': 1,
    'signal_quality': 2,
    'asic_eeg_power_int': 1,
    'vlength': 1,
    'delta': 3,
    'theta': 3,
    'low_alpha': 3,
    'high_alpha': 3,
    'low_beta': 3,
    'high_beta': 3,
    'low_gamma': 3,
    'mid_gamma': 3,
    'attention_id': 1,
    'attention': 1,
    'meditation_id': 1,
    'meditation': 1,
    'crc': 1
}

# EEG and attention graph types
graph_types = [
    'eeg',
    'attention'
]

# Types of data for EEG rhythms
eeg_output = [
    'low_alpha',
    'high_alpha',
    'low_beta',
    'high_beta',
    'delta',
    'low_gamma',
    'mid_gamma',
    'theta'
]

# Types of data for attention rhythms
attention_output = [
    'attention',
    'meditation'
]

# Graph plot colors for EEG signals
eeg_color = [
    '#8AD2D8',
    '#C6A68E',
    '#558AA4',
    '#F15E3D',
    '#56704B',
    '#CC3B7C',
    '#005594',
    '#EFCB5E'
]

# Graph plot colors for attention and meditation signals
attention_color = [
    '#89B65A',
    '#EBC9BE'
]
