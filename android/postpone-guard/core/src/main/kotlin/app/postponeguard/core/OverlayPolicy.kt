package app.postponeguard.core

import java.time.LocalDate

/**
 * A snapshot of the device. A null value means "could not be determined"
 * (missing permission or no data). The policy treats null as a reason not to show.
 */
data class Environment(
    val today: LocalDate,
    val nowMillis: Long,
    val lastShownAtMillis: Long?,
    /** Screen on and keyguard unlocked. */
    val userActive: Boolean,
    /** Ringing or off-hook (telephony or VoIP audio mode). */
    val inCall: Boolean?,
    /** Package of the last resumed activity. */
    val foregroundPackage: String?,
    val defaultDialer: String? = null,
    /** Navigation running in the background (from the optional notification listener). */
    val backgroundNavigation: Boolean = false,
)

sealed interface Decision {
    data class Show(val item: Item) : Decision
    data class Hide(val reason: Reason) : Decision
}

enum class Reason {
    NO_ITEM, USER_INACTIVE, CALL_STATE_UNKNOWN, IN_CALL, FOREGROUND_UNKNOWN,
    DIALLER, EMERGENCY, NAVIGATION, CAPPED,
}

object OverlayPolicy {
    const val CAP_MILLIS = 30L * 60 * 1000

    /** Safety blockers: these also remove an overlay that is already showing. */
    fun blocker(env: Environment): Reason? {
        if (!env.userActive) return Reason.USER_INACTIVE
        when (env.inCall) {
            null -> return Reason.CALL_STATE_UNKNOWN
            true -> return Reason.IN_CALL
            false -> Unit
        }
        if (env.backgroundNavigation) return Reason.NAVIGATION
        val pkg = env.foregroundPackage ?: return Reason.FOREGROUND_UNKNOWN
        return when (BlockedPackages.classify(pkg, env.defaultDialer)) {
            BlockedPackages.Category.DIALLER -> Reason.DIALLER
            BlockedPackages.Category.EMERGENCY -> Reason.EMERGENCY
            BlockedPackages.Category.NAVIGATION -> Reason.NAVIGATION
            null -> null
        }
    }

    /** Whether a new overlay may be shown now. */
    fun decide(items: List<Item>, env: Environment): Decision {
        val item = Items.overlayCandidate(items, env.today) ?: return Decision.Hide(Reason.NO_ITEM)
        blocker(env)?.let { return Decision.Hide(it) }
        val last = env.lastShownAtMillis
        if (last != null && env.nowMillis - last in 0 until CAP_MILLIS) return Decision.Hide(Reason.CAPPED)
        return Decision.Show(item)
    }
}
