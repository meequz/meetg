from meetg.utils import get_current_unixtime, get_unixtime_before_now


class SoftDict(dict):
    """
    Dict that doesn't raise exceptions. It returns another SoftDict
    in any usually-exception case, or custom class if init() called
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_class = SoftDict

    def __getitem__(self, key):
        if self.__contains__(key):
            item = super().__getitem__(key)
        else:
            item = self.default_class()
            self.__setitem__(key, item)
        return item

    def __delitem__(self, key):
        if self.__contains__(key):
            return super().__delitem__(key)

    def init(self, cls):
        self.default_class = cls


"""App-wide cache"""
service_cache = SoftDict()


class DateSegment(list):
    """
    List with two dates: one on object creation,
    one on calling the finish()
    """
    def __init__(self):
        super().__init__()
        time = get_current_unixtime()
        self.append(time)

    def finish(self):
        time = get_current_unixtime()
        self.append(time)

    def get_duration(self):
        return self[-1] - self[0]


class DateCache(list):
    """
    List to easy store and get back date objects: points and segments.
    Useful to store runtime stats, to later report them.
    Usage:
    cache = DateCache()
    cache.add() - add current Unix time to cache
    cache.get_day_count() - return number of additions happened for the last 24 hours
    """
    def add(self, obj=None):
        if obj is None:
            obj = get_current_unixtime()
        return self.append(obj)

    def _get_day_treshold(self):
        day_before = get_unixtime_before_now(24)
        for i, item in enumerate(self):
            to_compare = item
            if isinstance(item, list):
                to_compare = item[-1]
            if to_compare >= day_before:
                return i

    def get_day(self):
        treshold = self._get_day_treshold()
        if treshold is not None:
            return self[treshold:]

    def get_day_count(self):
        last_day = self.get_day()
        return len(last_day)

    def get_day_duration(self):
        """
        Method only for Segments. Count duration
        of date segments added for the last 24 hours
        """
        last_day = self.get_day()
        total = 0
        for segment in last_day:
            if not isinstance(segment, DateSegment):
                raise RuntimeError('get_day_duration() is only applicable for DateSegments')
            total += segment.get_duration()
        return total

    def clear_before_last_day(self):
        treshold = self._get_day_treshold()
        if treshold is not None:
            del self[:treshold]
