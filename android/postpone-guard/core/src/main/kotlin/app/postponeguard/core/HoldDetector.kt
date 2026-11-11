package app.postponeguard.core

import kotlin.math.hypot

/**
 * Detects a press held anywhere for [holdMillis] without moving more than
 * [slopPx]. Feed it touch events and call [tick] from a timer.
 */
class HoldDetector(
    private val holdMillis: Long = 5_000,
    private val slopPx: Float,
) {
    private var downAt: Long = -1
    private var downX = 0f
    private var downY = 0f
    private var fired = false

    val isHolding: Boolean get() = downAt >= 0 && !fired

    fun down(t: Long, x: Float, y: Float) {
        downAt = t; downX = x; downY = y; fired = false
    }

    fun move(x: Float, y: Float) {
        if (downAt >= 0 && hypot(x - downX, y - downY) > slopPx) cancel()
    }

    fun cancel() {
        downAt = -1
    }

    /** 0..1 progress of the current hold. */
    fun progress(t: Long): Float =
        if (!isHolding) 0f else ((t - downAt).toFloat() / holdMillis).coerceIn(0f, 1f)

    /** Returns true exactly once, when the hold reaches [holdMillis]. */
    fun tick(t: Long): Boolean {
        if (!isHolding || t - downAt < holdMillis) return false
        fired = true
        return true
    }
}
