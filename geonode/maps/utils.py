def _layer_json(layers, sources):
    """
    return a list of layer config for the provided layer
    """
    server_lookup = {}

    def uniqify(seq):
        """
        get a list of unique items from the input sequence.

        This relies only on equality tests, so you can use it on most
        things.  If you have a sequence of hashables, list(set(seq)) is
        better.
        """
        results = []
        for x in seq:
            if x not in results: results.append(x)
        return results

    configs = [l.source_config() for l in layers]

    i = 0
    for source in uniqify(configs):
        while str(i) in sources: i = i + 1
        sources[str(i)] = source 
        server_lookup[json.dumps(source)] = str(i)

    def source_lookup(source):
        for k, v in sources.iteritems():
            if v == source: return k
        return None

    def layer_config(l):
        cfg = l.layer_config()
        src_cfg = l.source_config()
        source = source_lookup(src_cfg)
        if source: cfg["source"] = source
        return cfg
    
    return [layer_config(l) for l in layers]
