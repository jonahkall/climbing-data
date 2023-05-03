# Hacky code for converting a written grade e.g. 5.11c or 5.13+ to a number
# we give 5.Xa/b the average of 5.Xa and 5.Xb
# we give 5.X- the same score as 5.Xa/b and 5.X+ the same score as 5.Xc/d

def get_grade_to_number_dict():

    d_pure = {'3rd': 1,
     '4th': 2,
     'Easy 5th': 3,
     '5.0': 4,
     '5.1': 5,
     '5.2': 6,
     '5.3': 7,
     '5.4': 8,
     '5.5': 9,
     '5.6': 10,
     '5.7': 11,
     '5.8': 12,
     '5.9': 13,
     '5.10a': 14,
     '5.10b': 15,
     '5.10': 16,
     '5.10c': 17,
     '5.10d': 18,
     '5.11a': 19,
     '5.11b': 20,
     '5.11': 21,
     '5.11c': 22,
     '5.11d': 23,
     '5.12a': 24,
     '5.12b': 25,
     '5.12': 26,
     '5.12c': 27,
     '5.12d': 28,
     '5.13a': 29,
     '5.13b': 30,
     '5.13': 31,
     '5.13c': 32,
     '5.13d': 33,
     '5.14a': 34,
     '5.14b': 35,
     '5.14': 36,
     '5.14c': 37,
     '5.14d': 38,
     '5.15a': 39,
     '5.15b': 40,
     '5.15': 41,
     '5.15c': 42,
     '5.15d': 43}

    d_pure_2 = {'3rd': 1,
     '4th': 2,
     'Easy 5th': 3,
     '5.0': 4,
     '5.1': 5,
     '5.2': 6,
     '5.3': 7,
     '5.4': 8,
     '5.5': 9,
     '5.6': 10,
     '5.7': 11,
     '5.7+': 11.5,
     '5.8-': 11.5,
     '5.8': 12,
     '5.8+': 12.5,
     '5.9-': 12.5,
     '5.9': 13,
     '5.9+': 13.5,
     '5.10a': 14,
     '5.10b': 15,
     '5.10': 16,
     '5.10c': 17,
     '5.10d': 18,
     '5.11a': 19,
     '5.11b': 20,
     '5.11': 21,
     '5.11c': 22,
     '5.11d': 23,
     '5.12a': 24,
     '5.12b': 25,
     '5.12': 26,
     '5.12c': 27,
     '5.12d': 28,
     '5.13a': 29,
     '5.13b': 30,
     '5.13': 31,
     '5.13c': 32,
     '5.13d': 33,
     '5.14a': 34,
     '5.14b': 35,
     '5.14': 36,
     '5.14c': 37,
     '5.14d': 38,
     '5.15a': 39,
     '5.15b': 40,
     '5.15': 41,
     '5.15c': 42,
     '5.15d': 43}

    pairs_to_add = {}
    for k in d_pure_2.keys():
        if "." in k:
            r = k.split(".")[1]
            if r[-1] == 'a':
                key_plus = "5." + r[:-1] + "+"
                key_minus = "5." + r[:-1] + "-"
                a_b_val = (d_pure_2[k] + d_pure_2[k.replace("a", "b")]) / 2.0
                b_c_val = (d_pure_2[k.replace("a", "b")] + d_pure_2[k.replace("a", "c")]) / 2.0
                c_d_val = (d_pure_2[k.replace("a", "c")] + d_pure_2[k.replace("a", "d")]) / 2.0
                pairs_to_add["5." + r[:-1] + "a/b"] = a_b_val
                pairs_to_add["5." + r[:-1] + "b/c"] = b_c_val
                pairs_to_add["5." + r[:-1] + "c/d"] = c_d_val
                pairs_to_add[key_plus] = c_d_val
                pairs_to_add[key_minus] = a_b_val
    d_final = {**d_pure_2, **pairs_to_add}
    return d_final