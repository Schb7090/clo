package app.postponeguard.core

import java.time.LocalDate

/**
 * A to-do item. [postponedDays] counts the distinct calendar days on which the
 * item was postponed (at most one increment per day).
 */
data class Item(
    val id: String,
    val title: String,
    val createdAtMillis: Long,
    val postponedDays: Int = 0,
    val lastPostponedOn: LocalDate? = null,
    val skippedOn: LocalDate? = null,
    val done: Boolean = false,
)

object Items {
    /** The overlay appears from the third postponed day. */
    const val MIN_POSTPONED_DAYS = 3

    /** Most postponed first, then the oldest. Done items are excluded. */
    val ORDER: Comparator<Item> =
        compareByDescending<Item> { it.postponedDays }.thenBy { it.createdAtMillis }.thenBy { it.id }

    fun open(items: List<Item>): List<Item> = items.filter { !it.done }.sortedWith(ORDER)

    /** The item the overlay should show today, or null. */
    fun overlayCandidate(items: List<Item>, today: LocalDate): Item? =
        open(items).firstOrNull { it.postponedDays >= MIN_POSTPONED_DAYS && it.skippedOn != today }

    /** Postpone by one day; a second postponement on the same day is a no-op. */
    fun postpone(item: Item, today: LocalDate): Item =
        if (item.lastPostponedOn == today) item
        else item.copy(postponedDays = item.postponedDays + 1, lastPostponedOn = today)

    /** SKIP TODAY: hides the item for the rest of today and counts as today's postponement. */
    fun skipToday(item: Item, today: LocalDate): Item = postpone(item, today).copy(skippedOn = today)

    fun markDone(item: Item): Item = item.copy(done = true)
}
