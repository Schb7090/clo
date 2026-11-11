package app.postponeguard.env

import android.app.AppOpsManager
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.os.Process
import android.telecom.TelecomManager

/**
 * Finds the package of the last resumed activity from usage events (needs the
 * Usage access special permission). Events are read incrementally so a user
 * who stays in one app for hours is still resolved.
 */
class ForegroundApp(private val context: Context) {
    private val usm = context.getSystemService(UsageStatsManager::class.java)
    private var lastQueryEnd = 0L
    private var lastPackage: String? = null

    fun hasAccess(): Boolean {
        val ops = context.getSystemService(AppOpsManager::class.java)
        @Suppress("DEPRECATION")
        val mode = ops.checkOpNoThrow(AppOpsManager.OPSTR_GET_USAGE_STATS, Process.myUid(), context.packageName)
        return mode == AppOpsManager.MODE_ALLOWED
    }

    /** Package in front, or null if unknown. */
    @Synchronized
    fun current(now: Long = System.currentTimeMillis()): String? {
        if (!hasAccess()) return null
        val from = if (lastQueryEnd == 0L || now < lastQueryEnd) now - LOOKBACK_MILLIS else lastQueryEnd - OVERLAP_MILLIS
        val events = usm.queryEvents(from, now) ?: return lastPackage
        val e = UsageEvents.Event()
        while (events.hasNextEvent()) {
            events.getNextEvent(e)
            if (e.eventType == UsageEvents.Event.ACTIVITY_RESUMED) lastPackage = e.packageName
        }
        lastQueryEnd = now
        return lastPackage
    }

    fun defaultDialer(): String? = try {
        context.getSystemService(TelecomManager::class.java)?.defaultDialerPackage
    } catch (e: Exception) {
        null
    }

    private companion object {
        const val LOOKBACK_MILLIS = 24L * 60 * 60 * 1000
        const val OVERLAP_MILLIS = 2_000L
    }
}
