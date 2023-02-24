import scoutingbackend
app = scoutingbackend.create_app()

from scoutingbackend import bluealliance
bluealliance.init_cache(app)