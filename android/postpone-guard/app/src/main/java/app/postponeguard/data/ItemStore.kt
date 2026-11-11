package app.postponeguard.data

import android.content.Context
import app.postponeguard.core.Item
import org.json.JSONArray
import org.json.JSONObject
import java.time.LocalDate
import java.util.UUID

/** Minimal persistent store: items as a JSON array, plus the overlay's last-shown time. */
class ItemStore(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("store", Context.MODE_PRIVATE)

    @Synchronized
    fun load(): List<Item> {
        val arr = JSONArray(prefs.getString(KEY_ITEMS, "[]"))
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            Item(
                id = o.getString("id"),
                title = o.getString("title"),
                createdAtMillis = o.getLong("createdAt"),
                postponedDays = o.optInt("postponedDays", 0),
                lastPostponedOn = o.optDate("lastPostponedOn"),
                skippedOn = o.optDate("skippedOn"),
                done = o.optBoolean("done", false),
            )
        }
    }

    @Synchronized
    fun save(items: List<Item>) {
        val arr = JSONArray()
        items.forEach { it ->
            arr.put(JSONObject().apply {
                put("id", it.id)
                put("title", it.title)
                put("createdAt", it.createdAtMillis)
                put("postponedDays", it.postponedDays)
                put("lastPostponedOn", it.lastPostponedOn?.toString())
                put("skippedOn", it.skippedOn?.toString())
                put("done", it.done)
            })
        }
        prefs.edit().putString(KEY_ITEMS, arr.toString()).apply()
    }

    fun add(title: String): Item {
        val item = Item(UUID.randomUUID().toString(), title, System.currentTimeMillis())
        save(load() + item)
        return item
    }

    @Synchronized
    fun update(id: String, change: (Item) -> Item) {
        save(load().map { if (it.id == id) change(it) else it })
    }

    var lastShownAtMillis: Long?
        get() = prefs.getLong(KEY_LAST_SHOWN, -1).takeIf { it >= 0 }
        set(v) { prefs.edit().putLong(KEY_LAST_SHOWN, v ?: -1).apply() }

    private fun JSONObject.optDate(key: String): LocalDate? =
        if (isNull(key) || !has(key)) null else LocalDate.parse(getString(key))

    private companion object {
        const val KEY_ITEMS = "items"
        const val KEY_LAST_SHOWN = "lastShownAt"
    }
}
