import numpy as np

def number2dbm(number):
    return 18.63 * np.log10(number) - 63.53

def gain2dbm(gain):
        return 20 * np.log10(self.gain) - 10