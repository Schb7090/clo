package app.postponeguard.core

/**
 * Apps in front of which the overlay must never appear.
 *
 * The lists are best effort: OEMs ship their own dialler and emergency
 * packages, and not every name here has been verified on a device. The system
 * default dialler is always added at runtime (TelecomManager.defaultDialerPackage).
 */
object BlockedPackages {
    enum class Category { DIALLER, EMERGENCY, NAVIGATION }

    val DIALLER = setOf(
        "com.google.android.dialer",
        "com.android.dialer",
        "com.samsung.android.dialer",
        "com.samsung.android.incallui",
        "com.android.incallui",
        "com.android.phone",
        "com.android.server.telecom",
    )

    val EMERGENCY = setOf(
        "com.android.emergency",
        "com.google.android.apps.safetyhub",
        "com.samsung.android.emergencymode.service",
        "com.android.cellbroadcastreceiver",
        "com.google.android.cellbroadcastreceiver",
    )

    val NAVIGATION = setOf(
        "com.google.android.apps.maps",
        "com.google.android.apps.mapslite",
        "com.google.android.projection.gearhead", // Android Auto
        "com.waze",
        "com.here.app.maps",
        "net.osmand",
        "net.osmand.plus",
        "app.organicmaps",
        "com.sygic.aura",
        "ru.yandex.yandexnavi",
    )

    fun classify(pkg: String?, defaultDialer: String? = null): Category? = when {
        pkg == null -> null
        pkg == defaultDialer || pkg in DIALLER -> Category.DIALLER
        pkg in EMERGENCY -> Category.EMERGENCY
        pkg in NAVIGATION -> Category.NAVIGATION
        else -> null
    }
}
