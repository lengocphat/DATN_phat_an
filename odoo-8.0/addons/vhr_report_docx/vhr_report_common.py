import locale
from datetime import datetime

locale.setlocale(locale.LC_ALL, '')


def validate_date(date_text):
    try:
        res = ''
        if len(date_text) == 10:
            date = datetime.strptime(str(date_text), '%Y-%m-%d')
            res = date.strftime('%d/%m/%Y')
        if len(date_text) == 19:
            dt = datetime.strptime(str(date_text), '%Y-%m-%d %H:%M:%S')
            res = dt.strftime('%d/%m/%Y %H:%M:%S')

        return res
    except ValueError:
        return False


class vhr_report_common(object):

    def repair_data(self, data):
        if data and isinstance(data, dict):
            for key, val in data.iteritems():
                if isinstance(val, (list, tuple)) and len(val) == 2 and isinstance(val[0], (int, long)):
                    data[key] = val[1]
                elif isinstance(val, (int, float, long)) and not isinstance(val, bool):
                    new_val = val and locale.format('%d', val, 1) or '0'
                    data[key] = new_val
                elif isinstance(val, (str, unicode)) and "-" in val and validate_date(val):
                    new_val = validate_date(val)
                    data[key] = new_val
                else:
                    new_val = val if isinstance(val, (str, unicode)) else str(val or '')
                    data[key] = new_val
        return data
