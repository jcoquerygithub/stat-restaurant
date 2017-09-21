from clientapi.restaurant import get_taux
from datetime import datetime, timedelta


def format_date():
    current_date = datetime.now() + timedelta(hours=1)
    return '%s-%02d-%02d %02d:%02d:%02d' % (current_date.year,
                                            current_date.month,
                                            current_date.day,
                                            current_date.hour,
                                            current_date.minute,
                                            current_date.second)


with open("statsRestaurant2.csv", "a") as stat_file:
    stat_file.write(format_date() + "|" + get_taux())
