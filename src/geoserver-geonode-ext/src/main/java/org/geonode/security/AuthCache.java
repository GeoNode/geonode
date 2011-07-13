package org.geonode.security;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.geotools.util.logging.Logging;
import org.springframework.scheduling.concurrent.CustomizableThreadFactory;
import org.springframework.security.Authentication;
import org.springframework.util.Assert;

public class AuthCache {

    private static final Logger LOGGER = Logging.getLogger(AuthCache.class);

    private static final int DEFAULT_TIMEOUT = 2000;

    private ConcurrentHashMap<String, Authentication> cache;

    private final ScheduledExecutorService cacheEvictor;

    private class EvictAuth implements Runnable {

        private final String key;

        public EvictAuth(final String key) {
            this.key = key;
        }

        public void run() {
            Authentication removed = cache.remove(key);
            if (LOGGER.isLoggable(Level.FINER)) {
                LOGGER.finer("evicted auth '" + key + "': " + removed);
            }
        }

    }

    private long timeout = DEFAULT_TIMEOUT;

    public AuthCache() {
        cache = new ConcurrentHashMap<String, Authentication>();

        CustomizableThreadFactory tf = new CustomizableThreadFactory();
        tf.setDaemon(true);
        tf.setThreadNamePrefix("GeoNode Auth Cache Evictor-");
        tf.setThreadPriority(Thread.MIN_PRIORITY + 1);
        cacheEvictor = Executors.newScheduledThreadPool(1, tf);
    }

    public long getTimeout() {
        return timeout;
    }

    public void setTimeout(long timeout) {
        this.timeout = timeout;
    }

    public Authentication get(final String authKey) {
        return cache.get(authKey);
    }

    public void put(final String authKey, final Authentication auth) {
        Assert.notNull(auth);
        cache.put(authKey, auth);
        cacheEvictor.schedule(new EvictAuth(authKey), timeout, TimeUnit.MILLISECONDS);
    }

}
