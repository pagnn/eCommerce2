from django.dispatch import Signal

user_logged_in_signal=Signal(providing_args=['instance','request'])
