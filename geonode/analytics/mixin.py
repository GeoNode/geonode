
from itertools import groupby          
from operator import itemgetter

class AnalyticsMixin(object):
    """
    Analytics model mixin: format data, group data
    """

    def get_analytics(self, data, keys):
        grouper = itemgetter(*tuple(keys))
        results = []
        for key, group in groupby(data, grouper):
            results.append(dict(dict(zip(keys, key)), count=len(list(group))))

        return results

    def format_data(self, query=None, model_instance=None, filters=None, exclude=None, order_by=None, extra_field=None):
        if model_instance:
            query = model_instance.objects.all()

        if filters:
            query = query.filter(**filters)
        if exclude:
            query = query.exclude(**exclude)
        if order_by:
            query = query.order_by(*tuple(order_by))

        extra = {}
        if extra_field:
            extra = dict(extra_field)

        data = [dict(l.__dict__, last_modified_date=l.last_modified_date, **extra) for l in query]

        return data