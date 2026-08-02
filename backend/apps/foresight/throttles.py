from rest_framework.throttling import UserRateThrottle


class ForesightFeedSyncThrottle(UserRateThrottle):
    scope = "foresight_feed_sync"
